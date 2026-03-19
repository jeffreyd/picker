from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Row, Column, Submit, Field
from .models import Category, Item, Part, PartOrder, Sale, ModelNote, Auction


class ItemForm(forms.ModelForm):
    acquisition_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))

    class Meta:
        model = Item
        fields = [
            'name', 'make', 'model', 'category',
            'acquisition_date', 'acquisition_source',
            'condition', 'status', 'cost_basis', 'notes',
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Row(
                Column('name', css_class='col-md-6'),
                Column('category', css_class='col-md-6'),
            ),
            Row(
                Column('make', css_class='col-md-6'),
                Column('model', css_class='col-md-6'),
            ),
            Row(
                Column('acquisition_date', css_class='col-md-4'),
                Column('condition', css_class='col-md-4'),
                Column('status', css_class='col-md-4'),
            ),
            Row(
                Column('acquisition_source', css_class='col-md-8'),
                Column('cost_basis', css_class='col-md-4'),
            ),
            'notes',
            Submit('submit', 'Save Item', css_class='btn btn-primary'),
        )


class PartForm(forms.ModelForm):
    class Meta:
        model = Part
        fields = [
            'name', 'description', 'source_item', 'used_in_item',
            'condition', 'status', 'notes',
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            'name',
            Row(
                Column('source_item', css_class='col-md-6'),
                Column('used_in_item', css_class='col-md-6'),
            ),
            Row(
                Column('condition', css_class='col-md-6'),
                Column('status', css_class='col-md-6'),
            ),
            'description',
            'notes',
            Submit('submit', 'Save Part', css_class='btn btn-primary'),
        )


class PartOrderForm(forms.ModelForm):
    order_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))
    expected_date = forms.DateField(
        required=False, widget=forms.DateInput(attrs={'type': 'date'})
    )
    received_date = forms.DateField(
        required=False, widget=forms.DateInput(attrs={'type': 'date'})
    )

    class Meta:
        model = PartOrder
        fields = [
            'description', 'supplier', 'supplier_other',
            'order_date', 'expected_date', 'received_date',
            'status', 'tracking_number', 'total_cost',
            'for_item', 'notes',
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            'description',
            Row(
                Column('supplier', css_class='col-md-6'),
                Column('supplier_other', css_class='col-md-6'),
            ),
            Row(
                Column('order_date', css_class='col-md-4'),
                Column('expected_date', css_class='col-md-4'),
                Column('received_date', css_class='col-md-4'),
            ),
            Row(
                Column('status', css_class='col-md-4'),
                Column('total_cost', css_class='col-md-4'),
                Column('tracking_number', css_class='col-md-4'),
            ),
            'for_item',
            'notes',
            Submit('submit', 'Save Order', css_class='btn btn-primary'),
        )


class SaleForm(forms.ModelForm):
    sale_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))

    class Meta:
        model = Sale
        fields = [
            'item', 'part', 'description',
            'sale_date', 'sale_price', 'platform', 'fees', 'notes',
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Row(
                Column('item', css_class='col-md-6'),
                Column('part', css_class='col-md-6'),
            ),
            'description',
            Row(
                Column('sale_date', css_class='col-md-4'),
                Column('sale_price', css_class='col-md-4'),
                Column('fees', css_class='col-md-4'),
            ),
            'platform',
            'notes',
            Submit('submit', 'Save Sale', css_class='btn btn-primary'),
        )


class ModelNoteForm(forms.ModelForm):
    class Meta:
        model = ModelNote
        fields = ['make', 'model', 'category', 'notes']
        widgets = {
            'notes': forms.Textarea(attrs={'rows': 8}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Row(
                Column('make', css_class='col-md-4'),
                Column('model', css_class='col-md-4'),
                Column('category', css_class='col-md-4'),
            ),
            'notes',
            Submit('submit', 'Save Note', css_class='btn btn-primary'),
        )


class AuctionForm(forms.ModelForm):
    start_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))
    end_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))

    class Meta:
        model = Auction
        fields = [
            'title', 'item', 'part',
            'ebay_item_id', 'starting_bid', 'buy_it_now',
            'start_date', 'end_date',
            'status', 'final_price',
            'notes',
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            'title',
            Row(
                Column('item', css_class='col-md-6'),
                Column('part', css_class='col-md-6'),
            ),
            Row(
                Column('ebay_item_id', css_class='col-md-4'),
                Column('starting_bid', css_class='col-md-4'),
                Column('buy_it_now', css_class='col-md-4'),
            ),
            Row(
                Column('start_date', css_class='col-md-4'),
                Column('end_date', css_class='col-md-4'),
                Column('status', css_class='col-md-4'),
            ),
            'final_price',
            'notes',
            Submit('submit', 'Save Auction', css_class='btn btn-primary'),
        )


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            'name',
            Submit('submit', 'Save Category', css_class='btn btn-primary'),
        )
