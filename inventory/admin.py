from django.contrib import admin
from .models import Category, Item, Part, PartOrder, Sale, ModelNote, Auction


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name']


@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    list_display = ['display_name', 'category', 'acquisition_date', 'condition', 'status']
    list_filter = ['status', 'condition', 'category']
    search_fields = ['name', 'make', 'model', 'notes']
    date_hierarchy = 'acquisition_date'


@admin.register(Part)
class PartAdmin(admin.ModelAdmin):
    list_display = ['name', 'source_item', 'used_in_item', 'condition', 'status']
    list_filter = ['status']
    search_fields = ['name', 'description', 'notes']


@admin.register(PartOrder)
class PartOrderAdmin(admin.ModelAdmin):
    list_display = ['description', 'supplier_display', 'order_date', 'total_cost', 'status', 'for_item']
    list_filter = ['status', 'supplier']
    search_fields = ['description', 'tracking_number', 'notes']
    date_hierarchy = 'order_date'


@admin.register(Sale)
class SaleAdmin(admin.ModelAdmin):
    list_display = ['__str__', 'sale_date', 'sale_price', 'fees', 'platform']
    list_filter = ['platform']
    search_fields = ['description', 'notes']
    date_hierarchy = 'sale_date'


@admin.register(Auction)
class AuctionAdmin(admin.ModelAdmin):
    list_display = ['title', 'item', 'part', 'end_date', 'starting_bid', 'final_price', 'status']
    list_filter = ['status']
    search_fields = ['title', 'ebay_item_id', 'notes']
    date_hierarchy = 'end_date'


@admin.register(ModelNote)
class ModelNoteAdmin(admin.ModelAdmin):
    list_display = ['make', 'model', 'category', 'updated_at']
    list_filter = ['category']
    search_fields = ['make', 'model', 'notes']
