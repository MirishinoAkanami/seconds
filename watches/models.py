from django.db import models
import random
import string


def _generate_order_id():
    return 'ORD-' + ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))


class WatchItem(models.Model):
    CONDITION_CHOICES = [
        ('new', 'Brand New'),
        ('used', 'Pre-owned'),
        ('restored', 'Restored / Cleaned'),
        ('limited', 'Limited Edition'),
    ]
    name = models.CharField(max_length=200)
    brand = models.CharField(max_length=100, blank=True)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    image = models.ImageField(upload_to='watches/', blank=True, null=True)
    condition = models.CharField(max_length=20, choices=CONDITION_CHOICES, default='new')
    stock_quantity = models.PositiveIntegerField(default=1)
    is_available = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def is_low_stock(self):
        return 0 < self.stock_quantity <= 2

    @property
    def is_out_of_stock(self):
        return self.stock_quantity == 0

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['-created_at']


class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('verified', 'Verified'),
        ('preparing', 'Preparing'),
        ('out_for_delivery', 'Out for Delivery'),
        ('ready_for_pickup', 'Ready for Pickup'),
        ('delivered', 'Delivered'),
        ('rejected', 'Rejected'),
        ('cancelled', 'Cancelled'),
    ]
    PAYMENT_CHOICES = [
        ('gcash', 'GCash'),
        ('shop', 'Pay at Shop'),
    ]
    DELIVERY_CHOICES = [
        ('pickup', 'Pick up at Store'),
        ('delivery', 'Home Delivery'),
    ]

    order_id = models.CharField(max_length=20, unique=True, default=_generate_order_id, editable=False)
    user = models.ForeignKey('accounts.CustomUser', on_delete=models.CASCADE, related_name='orders')
    watch_item = models.ForeignKey(WatchItem, on_delete=models.CASCADE, related_name='orders')
    payment_method = models.CharField(max_length=10, choices=PAYMENT_CHOICES)
    delivery_option = models.CharField(max_length=20, choices=DELIVERY_CHOICES)
    delivery_address = models.TextField(blank=True)
    delivery_fee = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    gcash_screenshot = models.ImageField(upload_to='gcash/', blank=True, null=True)
    gcash_ref_number = models.CharField(max_length=100, blank=True)
    notes = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    admin_note = models.CharField(max_length=300, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def total_amount(self):
        return self.watch_item.price + self.delivery_fee

    @property
    def status_steps(self):
        if self.delivery_option == 'delivery':
            return ['pending', 'verified', 'preparing', 'out_for_delivery', 'delivered']
        return ['pending', 'verified', 'preparing', 'ready_for_pickup', 'delivered']

    @property
    def current_step_index(self):
        try:
            return self.status_steps.index(self.status)
        except ValueError:
            return -1

    def __str__(self):
        return f'{self.order_id} — {self.user.username} — {self.watch_item.name}'

    class Meta:
        ordering = ['-created_at']
