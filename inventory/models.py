from django.db import models
from django.urls import reverse


class Category(models.Model):
    name = models.CharField(max_length=100)

    class Meta:
        verbose_name_plural = 'categories'
        ordering = ['name']

    def __str__(self):
        return self.name


class Item(models.Model):
    STATUS_ACQUIRED = 'acquired'
    STATUS_TESTING = 'testing'
    STATUS_REPAIRING = 'repairing'
    STATUS_PARTING_OUT = 'parting_out'
    STATUS_LISTED = 'listed'
    STATUS_SOLD = 'sold'
    STATUS_DONATED = 'donated'
    STATUS_DISPOSED = 'disposed'

    STATUS_CHOICES = [
        (STATUS_ACQUIRED, 'Acquired'),
        (STATUS_TESTING, 'Testing'),
        (STATUS_REPAIRING, 'Repairing'),
        (STATUS_PARTING_OUT, 'Parting Out'),
        (STATUS_LISTED, 'Listed for Sale'),
        (STATUS_SOLD, 'Sold'),
        (STATUS_DONATED, 'Donated'),
        (STATUS_DISPOSED, 'Disposed'),
    ]

    CONDITION_UNKNOWN = 'unknown'
    CONDITION_WORKING = 'working'
    CONDITION_WORKING_ISSUES = 'working_issues'
    CONDITION_NOT_WORKING = 'not_working'
    CONDITION_PARTS_ONLY = 'parts_only'

    CONDITION_CHOICES = [
        (CONDITION_UNKNOWN, 'Unknown'),
        (CONDITION_WORKING, 'Working'),
        (CONDITION_WORKING_ISSUES, 'Working with Issues'),
        (CONDITION_NOT_WORKING, 'Not Working'),
        (CONDITION_PARTS_ONLY, 'Parts Only'),
    ]

    name = models.CharField(max_length=200)
    make = models.CharField(max_length=100, blank=True)
    model = models.CharField(max_length=100, blank=True)
    category = models.ForeignKey(
        Category, on_delete=models.SET_NULL, null=True, blank=True, related_name='items'
    )
    acquisition_date = models.DateField()
    acquisition_source = models.CharField(
        max_length=200, blank=True, help_text='Where you found it (address, dumpster, etc.)'
    )
    condition = models.CharField(
        max_length=20, choices=CONDITION_CHOICES, default=CONDITION_UNKNOWN
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_ACQUIRED)
    cost_basis = models.DecimalField(
        max_digits=10, decimal_places=2, default=0,
        help_text='Your cost (usually $0 for trash finds)'
    )
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-acquisition_date', '-created_at']

    def __str__(self):
        if self.make and self.model:
            return f'{self.make} {self.model}'
        return self.name

    def get_absolute_url(self):
        return reverse('inventory:item_detail', kwargs={'pk': self.pk})

    @property
    def display_name(self):
        if self.make and self.model:
            return f'{self.make} {self.model}'
        return self.name

    @property
    def total_parts_cost(self):
        return sum(
            order.total_cost for order in self.orders.filter(
                status=PartOrder.STATUS_RECEIVED
            )
        )

    @property
    def total_revenue(self):
        return sum(s.net_amount for s in self.sales.all())

    @property
    def profit(self):
        return self.total_revenue - self.cost_basis - self.total_parts_cost


class Part(models.Model):
    STATUS_AVAILABLE = 'available'
    STATUS_USED = 'used'
    STATUS_SOLD = 'sold'
    STATUS_DISCARDED = 'discarded'

    STATUS_CHOICES = [
        (STATUS_AVAILABLE, 'Available'),
        (STATUS_USED, 'Used in Repair'),
        (STATUS_SOLD, 'Sold'),
        (STATUS_DISCARDED, 'Discarded'),
    ]

    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    source_item = models.ForeignKey(
        Item, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='harvested_parts',
        help_text='Item this part was pulled from'
    )
    used_in_item = models.ForeignKey(
        Item, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='repair_parts',
        help_text='Item this part was used to repair'
    )
    condition = models.CharField(max_length=50, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_AVAILABLE)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('inventory:part_detail', kwargs={'pk': self.pk})


class PartOrder(models.Model):
    STATUS_ORDERED = 'ordered'
    STATUS_SHIPPED = 'shipped'
    STATUS_RECEIVED = 'received'
    STATUS_RETURNED = 'returned'
    STATUS_CANCELLED = 'cancelled'

    STATUS_CHOICES = [
        (STATUS_ORDERED, 'Ordered'),
        (STATUS_SHIPPED, 'Shipped'),
        (STATUS_RECEIVED, 'Received'),
        (STATUS_RETURNED, 'Returned'),
        (STATUS_CANCELLED, 'Cancelled'),
    ]

    SUPPLIER_EBAY = 'ebay'
    SUPPLIER_AMAZON = 'amazon'
    SUPPLIER_ALIEXPRESS = 'aliexpress'
    SUPPLIER_OTHER = 'other'

    SUPPLIER_CHOICES = [
        (SUPPLIER_EBAY, 'eBay'),
        (SUPPLIER_AMAZON, 'Amazon'),
        (SUPPLIER_ALIEXPRESS, 'AliExpress'),
        (SUPPLIER_OTHER, 'Other'),
    ]

    description = models.CharField(max_length=200)
    supplier = models.CharField(max_length=50, choices=SUPPLIER_CHOICES, default=SUPPLIER_OTHER)
    supplier_other = models.CharField(
        max_length=100, blank=True, help_text='Supplier name if "Other"'
    )
    order_date = models.DateField()
    expected_date = models.DateField(null=True, blank=True)
    received_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_ORDERED)
    tracking_number = models.CharField(max_length=200, blank=True)
    total_cost = models.DecimalField(max_digits=10, decimal_places=2)
    for_item = models.ForeignKey(
        Item, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='orders',
        help_text='Item this order is for (optional)'
    )
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-order_date', '-created_at']

    def __str__(self):
        return self.description

    def get_absolute_url(self):
        return reverse('inventory:order_detail', kwargs={'pk': self.pk})

    @property
    def supplier_display(self):
        if self.supplier == self.SUPPLIER_OTHER and self.supplier_other:
            return self.supplier_other
        return self.get_supplier_display()


class Sale(models.Model):
    PLATFORM_EBAY = 'ebay'
    PLATFORM_FACEBOOK = 'facebook'
    PLATFORM_CRAIGSLIST = 'craigslist'
    PLATFORM_OFFERUP = 'offerup'
    PLATFORM_LOCAL = 'local'
    PLATFORM_OTHER = 'other'

    PLATFORM_CHOICES = [
        (PLATFORM_EBAY, 'eBay'),
        (PLATFORM_FACEBOOK, 'Facebook Marketplace'),
        (PLATFORM_CRAIGSLIST, 'Craigslist'),
        (PLATFORM_OFFERUP, 'OfferUp'),
        (PLATFORM_LOCAL, 'Local / Cash'),
        (PLATFORM_OTHER, 'Other'),
    ]

    item = models.ForeignKey(
        Item, on_delete=models.SET_NULL, null=True, blank=True, related_name='sales'
    )
    part = models.ForeignKey(
        Part, on_delete=models.SET_NULL, null=True, blank=True, related_name='sales'
    )
    description = models.CharField(
        max_length=200, blank=True,
        help_text='What was sold (if not linked to an item/part above)'
    )
    sale_date = models.DateField()
    sale_price = models.DecimalField(max_digits=10, decimal_places=2)
    platform = models.CharField(max_length=20, choices=PLATFORM_CHOICES, default=PLATFORM_OTHER)
    fees = models.DecimalField(
        max_digits=10, decimal_places=2, default=0,
        help_text='Platform fees, shipping costs, etc.'
    )
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-sale_date', '-created_at']

    def __str__(self):
        label = str(self.item or self.part or self.description or 'Sale')
        return f'{label} — ${self.sale_price}'

    def get_absolute_url(self):
        return reverse('inventory:sale_detail', kwargs={'pk': self.pk})

    @property
    def net_amount(self):
        return self.sale_price - self.fees


class Auction(models.Model):
    STATUS_ACTIVE = 'active'
    STATUS_ENDED_SOLD = 'ended_sold'
    STATUS_ENDED_UNSOLD = 'ended_unsold'
    STATUS_CANCELLED = 'cancelled'

    STATUS_CHOICES = [
        (STATUS_ACTIVE, 'Active'),
        (STATUS_ENDED_SOLD, 'Ended — Sold'),
        (STATUS_ENDED_UNSOLD, 'Ended — Unsold'),
        (STATUS_CANCELLED, 'Cancelled'),
    ]

    item = models.ForeignKey(
        Item, on_delete=models.SET_NULL, null=True, blank=True, related_name='auctions'
    )
    part = models.ForeignKey(
        Part, on_delete=models.SET_NULL, null=True, blank=True, related_name='auctions'
    )
    title = models.CharField(max_length=200, help_text='eBay listing title')
    ebay_item_id = models.CharField(max_length=50, blank=True, help_text='eBay item number')
    starting_bid = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )
    buy_it_now = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True,
        help_text='Buy It Now price, if set'
    )
    start_date = models.DateField()
    end_date = models.DateField()
    final_price = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True,
        help_text='Winning bid / final sale price'
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_ACTIVE)
    sale = models.OneToOneField(
        Sale, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='auction',
        help_text='Sale record created when this auction converted'
    )
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-end_date', '-created_at']

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('inventory:auction_detail', kwargs={'pk': self.pk})

    @property
    def is_active(self):
        return self.status == self.STATUS_ACTIVE

    @property
    def ebay_url(self):
        if self.ebay_item_id:
            return f'https://www.ebay.com/itm/{self.ebay_item_id}'
        return None


class ModelNote(models.Model):
    make = models.CharField(max_length=100)
    model = models.CharField(max_length=100)
    category = models.ForeignKey(
        Category, on_delete=models.SET_NULL, null=True, blank=True, related_name='model_notes'
    )
    notes = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['make', 'model']
        unique_together = [['make', 'model']]

    def __str__(self):
        return f'{self.make} {self.model}'

    def get_absolute_url(self):
        return reverse('inventory:modelnote_detail', kwargs={'pk': self.pk})
