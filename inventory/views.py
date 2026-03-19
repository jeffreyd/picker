from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Q, Sum
from django.http import HttpResponse
from django.contrib import messages
from django.utils import timezone

from .models import Category, Item, Part, PartOrder, Sale, ModelNote, Auction
from .forms import ItemForm, PartForm, PartOrderForm, SaleForm, ModelNoteForm, CategoryForm, AuctionForm


# ── Dashboard ──────────────────────────────────────────────────────────────────

def dashboard(request):
    active_items = Item.objects.exclude(
        status__in=[Item.STATUS_SOLD, Item.STATUS_DONATED, Item.STATUS_DISPOSED]
    )
    open_orders = PartOrder.objects.filter(
        status__in=[PartOrder.STATUS_ORDERED, PartOrder.STATUS_SHIPPED]
    )
    active_auctions = Auction.objects.filter(
        status=Auction.STATUS_ACTIVE
    ).select_related('item', 'part')
    recent_sales = Sale.objects.select_related('item', 'part').order_by('-sale_date')[:5]
    available_parts = Part.objects.filter(status=Part.STATUS_AVAILABLE).count()

    total_revenue = Sale.objects.aggregate(
        total=Sum('sale_price') - Sum('fees')
    )['total'] or 0

    status_counts = {
        status: Item.objects.filter(status=status).count()
        for status, _ in Item.STATUS_CHOICES
    }
    context = {
        'active_items': active_items[:10],
        'active_item_count': active_items.count(),
        'open_orders': open_orders[:5],
        'open_order_count': open_orders.count(),
        'active_auctions': active_auctions[:5],
        'active_auction_count': active_auctions.count(),
        'recent_sales': recent_sales,
        'available_parts': available_parts,
        'total_revenue': total_revenue,
        'status_counts': status_counts,
        'status_choices_display': Item.STATUS_CHOICES,
    }
    return render(request, 'inventory/dashboard.html', context)


# ── Items ──────────────────────────────────────────────────────────────────────

def item_list(request):
    qs = Item.objects.select_related('category').all()
    q = request.GET.get('q', '')
    status = request.GET.get('status', '')
    category = request.GET.get('category', '')

    if q:
        qs = qs.filter(
            Q(name__icontains=q) | Q(make__icontains=q) | Q(model__icontains=q) |
            Q(notes__icontains=q) | Q(acquisition_source__icontains=q)
        )
    if status:
        qs = qs.filter(status=status)
    if category:
        qs = qs.filter(category_id=category)

    context = {
        'items': qs,
        'q': q,
        'status': status,
        'category': category,
        'status_choices': Item.STATUS_CHOICES,
        'categories': Category.objects.all(),
    }

    if request.headers.get('HX-Request'):
        return render(request, 'inventory/items/_table.html', context)
    return render(request, 'inventory/items/list.html', context)


def item_detail(request, pk):
    item = get_object_or_404(Item.objects.select_related('category'), pk=pk)
    context = {
        'item': item,
        'harvested_parts': item.harvested_parts.all(),
        'repair_parts': item.repair_parts.all(),
        'orders': item.orders.all(),
        'sales': item.sales.all(),
        'auctions': item.auctions.select_related('sale').all(),
    }
    return render(request, 'inventory/items/detail.html', context)


def item_create(request):
    if request.method == 'POST':
        form = ItemForm(request.POST)
        if form.is_valid():
            item = form.save()
            messages.success(request, f'Item "{item}" added.')
            return redirect(item.get_absolute_url())
    else:
        initial = {}
        if request.GET.get('date'):
            initial['acquisition_date'] = request.GET['date']
        form = ItemForm(initial=initial)
    return render(request, 'inventory/items/form.html', {'form': form, 'title': 'Add Item'})


def item_edit(request, pk):
    item = get_object_or_404(Item, pk=pk)
    if request.method == 'POST':
        form = ItemForm(request.POST, instance=item)
        if form.is_valid():
            form.save()
            messages.success(request, f'Item "{item}" updated.')
            return redirect(item.get_absolute_url())
    else:
        form = ItemForm(instance=item)
    return render(request, 'inventory/items/form.html', {
        'form': form, 'item': item, 'title': f'Edit {item}'
    })


def item_delete(request, pk):
    item = get_object_or_404(Item, pk=pk)
    if request.method == 'POST':
        name = str(item)
        item.delete()
        messages.success(request, f'Item "{name}" deleted.')
        return redirect('inventory:item_list')
    return render(request, 'inventory/confirm_delete.html', {
        'object': item, 'cancel_url': item.get_absolute_url()
    })


def item_status_update(request, pk):
    """HTMX endpoint to update item status inline."""
    item = get_object_or_404(Item, pk=pk)
    if request.method == 'POST':
        new_status = request.POST.get('status')
        if new_status in dict(Item.STATUS_CHOICES):
            item.status = new_status
            item.save(update_fields=['status', 'updated_at'])
    return render(request, 'inventory/items/_status_badge.html', {'item': item})


# ── Parts ──────────────────────────────────────────────────────────────────────

def part_list(request):
    qs = Part.objects.select_related('source_item', 'used_in_item').all()
    q = request.GET.get('q', '')
    status = request.GET.get('status', '')

    if q:
        qs = qs.filter(
            Q(name__icontains=q) | Q(description__icontains=q) | Q(notes__icontains=q)
        )
    if status:
        qs = qs.filter(status=status)

    context = {
        'parts': qs,
        'q': q,
        'status': status,
        'status_choices': Part.STATUS_CHOICES,
    }

    if request.headers.get('HX-Request'):
        return render(request, 'inventory/parts/_table.html', context)
    return render(request, 'inventory/parts/list.html', context)


def part_detail(request, pk):
    part = get_object_or_404(Part.objects.select_related('source_item', 'used_in_item'), pk=pk)
    return render(request, 'inventory/parts/detail.html', {'part': part})


def part_create(request):
    initial = {}
    if request.GET.get('source_item'):
        initial['source_item'] = request.GET['source_item']
    if request.GET.get('used_in_item'):
        initial['used_in_item'] = request.GET['used_in_item']

    if request.method == 'POST':
        form = PartForm(request.POST)
        if form.is_valid():
            part = form.save()
            messages.success(request, f'Part "{part}" added.')
            if request.GET.get('next'):
                return redirect(request.GET['next'])
            return redirect(part.get_absolute_url())
    else:
        form = PartForm(initial=initial)
    return render(request, 'inventory/parts/form.html', {'form': form, 'title': 'Add Part'})


def part_edit(request, pk):
    part = get_object_or_404(Part, pk=pk)
    if request.method == 'POST':
        form = PartForm(request.POST, instance=part)
        if form.is_valid():
            form.save()
            messages.success(request, f'Part "{part}" updated.')
            return redirect(part.get_absolute_url())
    else:
        form = PartForm(instance=part)
    return render(request, 'inventory/parts/form.html', {
        'form': form, 'part': part, 'title': f'Edit {part}'
    })


def part_delete(request, pk):
    part = get_object_or_404(Part, pk=pk)
    if request.method == 'POST':
        name = str(part)
        part.delete()
        messages.success(request, f'Part "{name}" deleted.')
        return redirect('inventory:part_list')
    return render(request, 'inventory/confirm_delete.html', {
        'object': part, 'cancel_url': part.get_absolute_url()
    })


# ── Orders ─────────────────────────────────────────────────────────────────────

def order_list(request):
    qs = PartOrder.objects.select_related('for_item').all()
    q = request.GET.get('q', '')
    status = request.GET.get('status', '')

    if q:
        qs = qs.filter(
            Q(description__icontains=q) | Q(tracking_number__icontains=q) |
            Q(notes__icontains=q)
        )
    if status:
        qs = qs.filter(status=status)

    context = {
        'orders': qs,
        'q': q,
        'status': status,
        'status_choices': PartOrder.STATUS_CHOICES,
    }

    if request.headers.get('HX-Request'):
        return render(request, 'inventory/orders/_table.html', context)
    return render(request, 'inventory/orders/list.html', context)


def order_detail(request, pk):
    order = get_object_or_404(PartOrder.objects.select_related('for_item'), pk=pk)
    return render(request, 'inventory/orders/detail.html', {'order': order})


def order_create(request):
    initial = {}
    if request.GET.get('for_item'):
        initial['for_item'] = request.GET['for_item']

    if request.method == 'POST':
        form = PartOrderForm(request.POST)
        if form.is_valid():
            order = form.save()
            messages.success(request, f'Order "{order}" added.')
            if request.GET.get('next'):
                return redirect(request.GET['next'])
            return redirect(order.get_absolute_url())
    else:
        if 'order_date' not in initial:
            initial['order_date'] = timezone.now().date()
        form = PartOrderForm(initial=initial)
    return render(request, 'inventory/orders/form.html', {
        'form': form, 'title': 'Add Order'
    })


def order_edit(request, pk):
    order = get_object_or_404(PartOrder, pk=pk)
    if request.method == 'POST':
        form = PartOrderForm(request.POST, instance=order)
        if form.is_valid():
            form.save()
            messages.success(request, f'Order "{order}" updated.')
            return redirect(order.get_absolute_url())
    else:
        form = PartOrderForm(instance=order)
    return render(request, 'inventory/orders/form.html', {
        'form': form, 'order': order, 'title': f'Edit Order: {order}'
    })


def order_delete(request, pk):
    order = get_object_or_404(PartOrder, pk=pk)
    if request.method == 'POST':
        name = str(order)
        order.delete()
        messages.success(request, f'Order "{name}" deleted.')
        return redirect('inventory:order_list')
    return render(request, 'inventory/confirm_delete.html', {
        'object': order, 'cancel_url': order.get_absolute_url()
    })


def order_status_update(request, pk):
    """HTMX endpoint to update order status inline."""
    order = get_object_or_404(PartOrder, pk=pk)
    if request.method == 'POST':
        new_status = request.POST.get('status')
        if new_status in dict(PartOrder.STATUS_CHOICES):
            order.status = new_status
            if new_status == PartOrder.STATUS_RECEIVED and not order.received_date:
                order.received_date = timezone.now().date()
            order.save(update_fields=['status', 'received_date', 'updated_at'])
    return render(request, 'inventory/orders/_status_badge.html', {'order': order})


# ── Sales ──────────────────────────────────────────────────────────────────────

def sale_list(request):
    qs = Sale.objects.select_related('item', 'part').all()
    q = request.GET.get('q', '')
    platform = request.GET.get('platform', '')

    if q:
        qs = qs.filter(
            Q(description__icontains=q) | Q(notes__icontains=q) |
            Q(item__name__icontains=q) | Q(part__name__icontains=q)
        )
    if platform:
        qs = qs.filter(platform=platform)

    totals = qs.aggregate(
        gross=Sum('sale_price'),
        fees=Sum('fees'),
    )
    gross = totals['gross'] or 0
    fees = totals['fees'] or 0

    context = {
        'sales': qs,
        'q': q,
        'platform': platform,
        'platform_choices': Sale.PLATFORM_CHOICES,
        'gross': gross,
        'fees': fees,
        'net': gross - fees,
    }

    if request.headers.get('HX-Request'):
        return render(request, 'inventory/sales/_table.html', context)
    return render(request, 'inventory/sales/list.html', context)


def sale_detail(request, pk):
    sale = get_object_or_404(Sale.objects.select_related('item', 'part'), pk=pk)
    return render(request, 'inventory/sales/detail.html', {'sale': sale})


def sale_create(request):
    initial = {}
    if request.GET.get('item'):
        initial['item'] = request.GET['item']
    if request.GET.get('part'):
        initial['part'] = request.GET['part']

    if request.method == 'POST':
        form = SaleForm(request.POST)
        if form.is_valid():
            sale = form.save()
            # Auto-mark item/part as sold
            if sale.item and sale.item.status != Item.STATUS_SOLD:
                sale.item.status = Item.STATUS_SOLD
                sale.item.save(update_fields=['status', 'updated_at'])
            if sale.part and sale.part.status != Part.STATUS_SOLD:
                sale.part.status = Part.STATUS_SOLD
                sale.part.save(update_fields=['status'])
            messages.success(request, f'Sale recorded: ${sale.sale_price}')
            if request.GET.get('next'):
                return redirect(request.GET['next'])
            return redirect(sale.get_absolute_url())
    else:
        if 'sale_date' not in initial:
            initial['sale_date'] = timezone.now().date()
        form = SaleForm(initial=initial)
    return render(request, 'inventory/sales/form.html', {'form': form, 'title': 'Record Sale'})


def sale_edit(request, pk):
    sale = get_object_or_404(Sale, pk=pk)
    if request.method == 'POST':
        form = SaleForm(request.POST, instance=sale)
        if form.is_valid():
            form.save()
            messages.success(request, 'Sale updated.')
            return redirect(sale.get_absolute_url())
    else:
        form = SaleForm(instance=sale)
    return render(request, 'inventory/sales/form.html', {
        'form': form, 'sale': sale, 'title': 'Edit Sale'
    })


def sale_delete(request, pk):
    sale = get_object_or_404(Sale, pk=pk)
    if request.method == 'POST':
        sale.delete()
        messages.success(request, 'Sale deleted.')
        return redirect('inventory:sale_list')
    return render(request, 'inventory/confirm_delete.html', {
        'object': sale, 'cancel_url': sale.get_absolute_url()
    })


# ── Model Notes ────────────────────────────────────────────────────────────────

def modelnote_list(request):
    qs = ModelNote.objects.select_related('category').all()
    q = request.GET.get('q', '')
    category = request.GET.get('category', '')

    if q:
        qs = qs.filter(
            Q(make__icontains=q) | Q(model__icontains=q) | Q(notes__icontains=q)
        )
    if category:
        qs = qs.filter(category_id=category)

    context = {
        'notes': qs,
        'q': q,
        'category': category,
        'categories': Category.objects.all(),
    }

    if request.headers.get('HX-Request'):
        return render(request, 'inventory/model_notes/_table.html', context)
    return render(request, 'inventory/model_notes/list.html', context)


def modelnote_detail(request, pk):
    note = get_object_or_404(ModelNote.objects.select_related('category'), pk=pk)
    # Find items that match this make/model
    related_items = Item.objects.filter(
        make__iexact=note.make, model__iexact=note.model
    )
    return render(request, 'inventory/model_notes/detail.html', {
        'note': note, 'related_items': related_items
    })


def modelnote_create(request):
    initial = {}
    if request.GET.get('make'):
        initial['make'] = request.GET['make']
    if request.GET.get('model'):
        initial['model'] = request.GET['model']

    if request.method == 'POST':
        form = ModelNoteForm(request.POST)
        if form.is_valid():
            note = form.save()
            messages.success(request, f'Notes for "{note}" saved.')
            return redirect(note.get_absolute_url())
    else:
        form = ModelNoteForm(initial=initial)
    return render(request, 'inventory/model_notes/form.html', {
        'form': form, 'title': 'Add Model Note'
    })


def modelnote_edit(request, pk):
    note = get_object_or_404(ModelNote, pk=pk)
    if request.method == 'POST':
        form = ModelNoteForm(request.POST, instance=note)
        if form.is_valid():
            form.save()
            messages.success(request, f'Notes for "{note}" updated.')
            return redirect(note.get_absolute_url())
    else:
        form = ModelNoteForm(instance=note)
    return render(request, 'inventory/model_notes/form.html', {
        'form': form, 'note': note, 'title': f'Edit: {note}'
    })


def modelnote_delete(request, pk):
    note = get_object_or_404(ModelNote, pk=pk)
    if request.method == 'POST':
        name = str(note)
        note.delete()
        messages.success(request, f'Notes for "{name}" deleted.')
        return redirect('inventory:modelnote_list')
    return render(request, 'inventory/confirm_delete.html', {
        'object': note, 'cancel_url': note.get_absolute_url()
    })


# ── Categories ─────────────────────────────────────────────────────────────────

def category_list(request):
    categories = Category.objects.all()
    return render(request, 'inventory/categories/list.html', {'categories': categories})


def category_create(request):
    if request.method == 'POST':
        form = CategoryForm(request.POST)
        if form.is_valid():
            cat = form.save()
            messages.success(request, f'Category "{cat}" added.')
            return redirect('inventory:category_list')
    else:
        form = CategoryForm()
    return render(request, 'inventory/categories/form.html', {
        'form': form, 'title': 'Add Category'
    })


def category_edit(request, pk):
    cat = get_object_or_404(Category, pk=pk)
    if request.method == 'POST':
        form = CategoryForm(request.POST, instance=cat)
        if form.is_valid():
            form.save()
            messages.success(request, f'Category "{cat}" updated.')
            return redirect('inventory:category_list')
    else:
        form = CategoryForm(instance=cat)
    return render(request, 'inventory/categories/form.html', {
        'form': form, 'cat': cat, 'title': f'Edit Category: {cat}'
    })


def category_delete(request, pk):
    cat = get_object_or_404(Category, pk=pk)
    if request.method == 'POST':
        name = str(cat)
        cat.delete()
        messages.success(request, f'Category "{name}" deleted.')
        return redirect('inventory:category_list')
    return render(request, 'inventory/confirm_delete.html', {
        'object': cat, 'cancel_url': 'inventory:category_list'
    })


# ── Auctions ───────────────────────────────────────────────────────────────────

def auction_list(request):
    qs = Auction.objects.select_related('item', 'part').all()
    q = request.GET.get('q', '')
    status = request.GET.get('status', '')

    if q:
        qs = qs.filter(
            Q(title__icontains=q) | Q(ebay_item_id__icontains=q) | Q(notes__icontains=q)
        )
    if status:
        qs = qs.filter(status=status)

    context = {
        'auctions': qs,
        'q': q,
        'status': status,
        'status_choices': Auction.STATUS_CHOICES,
    }

    if request.headers.get('HX-Request'):
        return render(request, 'inventory/auctions/_table.html', context)
    return render(request, 'inventory/auctions/list.html', context)


def auction_detail(request, pk):
    auction = get_object_or_404(
        Auction.objects.select_related('item', 'part', 'sale'), pk=pk
    )
    return render(request, 'inventory/auctions/detail.html', {'auction': auction})


def auction_create(request):
    initial = {}
    if request.GET.get('item'):
        initial['item'] = request.GET['item']
    if request.GET.get('part'):
        initial['part'] = request.GET['part']

    if request.method == 'POST':
        form = AuctionForm(request.POST)
        if form.is_valid():
            auction = form.save()
            messages.success(request, f'Auction "{auction}" created.')
            if request.GET.get('next'):
                return redirect(request.GET['next'])
            return redirect(auction.get_absolute_url())
    else:
        if 'start_date' not in initial:
            initial['start_date'] = timezone.now().date()
        form = AuctionForm(initial=initial)
    return render(request, 'inventory/auctions/form.html', {
        'form': form, 'title': 'Add Auction'
    })


def auction_edit(request, pk):
    auction = get_object_or_404(Auction, pk=pk)
    if request.method == 'POST':
        form = AuctionForm(request.POST, instance=auction)
        if form.is_valid():
            form.save()
            messages.success(request, f'Auction "{auction}" updated.')
            return redirect(auction.get_absolute_url())
    else:
        form = AuctionForm(instance=auction)
    return render(request, 'inventory/auctions/form.html', {
        'form': form, 'auction': auction, 'title': f'Edit: {auction}'
    })


def auction_delete(request, pk):
    auction = get_object_or_404(Auction, pk=pk)
    if request.method == 'POST':
        name = str(auction)
        auction.delete()
        messages.success(request, f'Auction "{name}" deleted.')
        return redirect('inventory:auction_list')
    return render(request, 'inventory/confirm_delete.html', {
        'object': auction, 'cancel_url': auction.get_absolute_url()
    })


def auction_convert(request, pk):
    """Convert a won auction into a Sale record."""
    auction = get_object_or_404(Auction, pk=pk)

    if auction.sale:
        messages.info(request, 'This auction has already been converted to a sale.')
        return redirect(auction.sale.get_absolute_url())

    if request.method == 'POST':
        form = SaleForm(request.POST)
        if form.is_valid():
            sale = form.save()
            # Link auction → sale and mark it ended-sold
            auction.sale = sale
            auction.status = Auction.STATUS_ENDED_SOLD
            if not auction.final_price and sale.sale_price:
                auction.final_price = sale.sale_price
            auction.save(update_fields=['sale', 'status', 'final_price', 'updated_at'])
            # Auto-update item/part status
            if sale.item and sale.item.status != Item.STATUS_SOLD:
                sale.item.status = Item.STATUS_SOLD
                sale.item.save(update_fields=['status', 'updated_at'])
            if sale.part and sale.part.status != Part.STATUS_SOLD:
                sale.part.status = Part.STATUS_SOLD
                sale.part.save(update_fields=['status'])
            messages.success(request, f'Auction converted to sale: ${sale.sale_price}')
            return redirect(sale.get_absolute_url())
    else:
        # Pre-fill the sale form with data from the auction
        initial = {
            'sale_date': timezone.now().date(),
            'platform': Sale.PLATFORM_EBAY,
            'description': auction.title,
        }
        if auction.item:
            initial['item'] = auction.item.pk
        if auction.part:
            initial['part'] = auction.part.pk
        if auction.final_price:
            initial['sale_price'] = auction.final_price
        form = SaleForm(initial=initial)

    return render(request, 'inventory/auctions/convert.html', {
        'form': form,
        'auction': auction,
        'title': f'Convert Auction to Sale: {auction}',
    })
