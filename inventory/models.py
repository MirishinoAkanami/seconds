from django.db import models


class SariItem(models.Model):
    CATEGORY_CHOICES = [
        ('rice_grains', 'Rice & Grains'),
        ('canned_goods', 'Canned Goods'),
        ('condiments', 'Condiments & Sauces'),
        ('noodles_pasta', 'Noodles & Pasta'),
        ('snacks', 'Snacks & Chips'),
        ('biscuits', 'Biscuits & Cookies'),
        ('candy', 'Candy & Sweets'),
        ('chocolate', 'Chocolate'),
        ('bread_bakery', 'Bread & Bakery'),
        ('beverage_hot', 'Coffee & Tea'),
        ('beverage_cold', 'Juice & Soft Drinks'),
        ('water', 'Water & Ice'),
        ('dairy', 'Dairy & Eggs'),
        ('frozen', 'Frozen Goods'),
        ('household', 'Household Supplies'),
        ('cleaning', 'Cleaning Products'),
        ('personal', 'Personal Care'),
        ('medicine', 'Medicine & Essentials'),
        ('school', 'School Supplies'),
        ('tobacco', 'Tobacco & Lighter'),
        ('load', 'Load & E-Wallet'),
        ('other', 'Other'),
    ]
    name = models.CharField(max_length=200)
    category = models.CharField(max_length=30, choices=CATEGORY_CHOICES, default='other')
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock_quantity = models.PositiveIntegerField(default=0)
    unit = models.CharField(max_length=50, default='piece')
    low_stock_threshold = models.PositiveIntegerField(default=5)
    image = models.ImageField(upload_to='inventory/', blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['category', 'name']

    @property
    def is_low_stock(self):
        return 0 < self.stock_quantity <= self.low_stock_threshold

    @property
    def is_out_of_stock(self):
        return self.stock_quantity == 0

    def __str__(self):
        return self.name


class StockLog(models.Model):
    ACTION_CHOICES = [
        ('add', 'Stock Added'),
        ('remove', 'Stock Removed'),
        ('adjust', 'Manual Adjustment'),
    ]
    item = models.ForeignKey(SariItem, on_delete=models.CASCADE, related_name='logs')
    action = models.CharField(max_length=10, choices=ACTION_CHOICES)
    quantity_changed = models.IntegerField()
    notes = models.CharField(max_length=300, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.get_action_display()} — {self.item.name} ({self.quantity_changed:+d})'
