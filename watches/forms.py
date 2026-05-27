from django import forms
from .models import WatchItem


class WatchItemForm(forms.ModelForm):
    class Meta:
        model = WatchItem
        fields = ('name', 'brand', 'description', 'price', 'image', 'condition', 'stock_quantity', 'is_available')
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
            'price': forms.NumberInput(attrs={'step': '0.01', 'min': '0'}),
            'stock_quantity': forms.NumberInput(attrs={'min': '0', 'value': '1'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.instance.pk:
            self.fields['stock_quantity'].initial = 1
        for name, field in self.fields.items():
            if not isinstance(field.widget, (forms.CheckboxInput, forms.FileInput)):
                field.widget.attrs.setdefault('class', 'form-input')
