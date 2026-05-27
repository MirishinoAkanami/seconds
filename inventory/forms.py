from django import forms
from .models import SariItem


class SariItemForm(forms.ModelForm):
    class Meta:
        model = SariItem
        fields = ('name', 'category', 'price', 'stock_quantity', 'unit', 'low_stock_threshold', 'image')
        widgets = {
            'price': forms.NumberInput(attrs={'step': '0.01', 'min': '0'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            if not isinstance(field.widget, forms.FileInput):
                field.widget.attrs.setdefault('class', 'form-input')
