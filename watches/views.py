import base64
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.files.base import ContentFile
from django.db.models import Count, Sum, Q
from django.utils import timezone
from datetime import timedelta
from .models import WatchItem, Order
from .forms import WatchItemForm
from accounts.models import StoreSettings


def _is_admin(user):
    return user.is_superuser or getattr(user, 'role', '') == 'admin'


def _save_watch_image(request, item):
    data = request.POST.get('cropped_image_data', '')
    if data and data.startswith('data:image'):
        fmt, imgstr = data.split(';base64,')
        ext = fmt.split('/')[-1]
        item.image = ContentFile(base64.b64decode(imgstr), name=f'watch_{item.pk}.{ext}')
    return item


# ─── Watch Catalog ────────────────────────────────────────
def watch_list(request):
    query = request.GET.get('q', '').strip()
    condition_filter = request.GET.get('condition', '')
    sort = request.GET.get('sort', 'newest')

    if request.user.is_authenticated and _is_admin(request.user):
        qs = WatchItem.objects.all()
    else:
        qs = WatchItem.objects.filter(is_available=True, stock_quantity__gt=0)

    if query:
        qs = qs.filter(name__icontains=query) | qs.filter(brand__icontains=query)
    if condition_filter:
        qs = qs.filter(condition=condition_filter)

    sort_map = {
        'newest': '-created_at',
        'oldest': 'created_at',
        'price_asc': 'price',
        'price_desc': '-price',
        'name': 'name',
    }
    qs = qs.order_by(sort_map.get(sort, '-created_at'))

    store = StoreSettings.get_settings()
    return render(request, 'watches/watch_list.html', {
        'items': qs,
        'query': query,
        'condition_filter': condition_filter,
        'sort': sort,
        'store': store,
        'condition_choices': WatchItem.CONDITION_CHOICES,
    })


def watch_detail(request, pk):
    item = get_object_or_404(WatchItem, pk=pk)
    store = StoreSettings.get_settings()
    share_url = request.build_absolute_uri(f'/watches/item/{pk}/')
    fb_share_url = f"https://www.facebook.com/sharer/sharer.php?u={share_url}"
    related = WatchItem.objects.filter(
        is_available=True, stock_quantity__gt=0, condition=item.condition
    ).exclude(pk=pk)[:4]
    return render(request, 'watches/watch_detail.html', {
        'item': item,
        'store': store,
        'fb_share_url': fb_share_url,
        'related': related,
    })


# ─── Watch Admin CRUD ─────────────────────────────────────
@login_required
def watch_add(request):
    if not _is_admin(request.user):
        return redirect('dashboard')
    if request.method == 'POST':
        form = WatchItemForm(request.POST, request.FILES)
        if form.is_valid():
            item = form.save(commit=False)
            item.save()
            item = _save_watch_image(request, item)
            item.save()
            messages.success(request, f'"{item.name}" added to catalog.')
            return redirect('watch_list')
        for field, errs in form.errors.items():
            for e in errs:
                messages.error(request, f'{field}: {e}')
    else:
        form = WatchItemForm()
    return render(request, 'watches/watch_form.html', {'form': form, 'title': 'Add Watch'})


@login_required
def watch_edit(request, pk):
    if not _is_admin(request.user):
        return redirect('dashboard')
    item = get_object_or_404(WatchItem, pk=pk)
    if request.method == 'POST':
        form = WatchItemForm(request.POST, request.FILES, instance=item)
        if form.is_valid():
            item = form.save(commit=False)
            item = _save_watch_image(request, item)
            item.save()
            messages.success(request, f'"{item.name}" updated.')
            return redirect('watch_list')
        for field, errs in form.errors.items():
            for e in errs:
                messages.error(request, f'{field}: {e}')
    else:
        form = WatchItemForm(instance=item)
    return render(request, 'watches/watch_form.html', {'form': form, 'title': 'Edit Watch', 'item': item})


@login_required
def watch_delete(request, pk):
    if not _is_admin(request.user):
        return redirect('dashboard')
    item = get_object_or_404(WatchItem, pk=pk)
    if request.method == 'POST':
        name = item.name
        item.delete()
        messages.success(request, f'"{name}" deleted.')
        return redirect('watch_list')
    return render(request, 'watches/watch_confirm_delete.html', {'item': item})


# ─── Orders (User) ────────────────────────────────────────
@login_required
def order_create(request, pk):
    item = get_object_or_404(WatchItem, pk=pk, is_available=True)
    store = StoreSettings.get_settings()

    if item.stock_quantity <= 0:
        messages.error(request, 'This watch is out of stock.')
        return redirect('watch_detail', pk=pk)

    if request.method == 'POST':
        payment_method = request.POST.get('payment_method', 'gcash')
        delivery_option = request.POST.get('delivery_option', 'pickup')
        delivery_address = request.POST.get('delivery_address', '').strip()
        gcash_ref = request.POST.get('gcash_ref_number', '').strip()
        notes = request.POST.get('notes', '').strip()
        screenshot = request.FILES.get('gcash_screenshot')
        fee = store.delivery_fee if delivery_option == 'delivery' else 0

        Order.objects.create(
            user=request.user,
            watch_item=item,
            payment_method=payment_method,
            delivery_option=delivery_option,
            delivery_address=delivery_address if delivery_option == 'delivery' else '',
            delivery_fee=fee,
            gcash_screenshot=screenshot,
            gcash_ref_number=gcash_ref,
            notes=notes,
        )
        messages.success(request, f'Reservation for "{item.name}" submitted! We\'ll contact you soon.')
        return redirect('my_orders')

    return render(request, 'watches/order_form.html', {'item': item, 'store': store})


@login_required
def my_orders(request):
    if _is_admin(request.user):
        return redirect('orders')
    orders = Order.objects.filter(user=request.user).select_related('watch_item')
    return render(request, 'watches/my_orders.html', {'orders': orders})


@login_required
def order_cancel(request, pk):
    order = get_object_or_404(Order, pk=pk, user=request.user)
    if request.method == 'POST' and order.status == 'pending':
        order.status = 'cancelled'
        order.save()
        messages.success(request, 'Order cancelled.')
    return redirect('my_orders')


# ─── Sales Statistics (Admin) ─────────────────────────────
@login_required
def sales_stats(request):
    if not _is_admin(request.user):
        return redirect('dashboard')

    now = timezone.now()
    thirty_days_ago = now - timedelta(days=30)
    seven_days_ago = now - timedelta(days=7)

    all_orders = Order.objects.select_related('watch_item', 'user')
    verified_orders = all_orders.filter(status__in=['verified', 'preparing', 'out_for_delivery', 'ready_for_pickup', 'delivered'])

    # Totals
    total_orders = all_orders.count()
    total_verified = verified_orders.count()
    total_revenue = sum(o.total_amount for o in verified_orders)
    pending_count = all_orders.filter(status='pending').count()
    cancelled_count = all_orders.filter(status__in=['cancelled', 'rejected']).count()
    delivered_count = all_orders.filter(status='delivered').count()

    # Last 30 days
    recent_orders = all_orders.filter(created_at__gte=thirty_days_ago)
    recent_revenue = sum(o.total_amount for o in recent_orders.filter(status__in=['verified', 'preparing', 'out_for_delivery', 'ready_for_pickup', 'delivered']))

    # Last 7 days
    week_orders = all_orders.filter(created_at__gte=seven_days_ago).count()

    # Top watches by orders
    top_watches = (
        WatchItem.objects
        .annotate(order_count=Count('orders'))
        .order_by('-order_count')[:5]
    )

    # Payment method breakdown
    gcash_count = verified_orders.filter(payment_method='gcash').count()
    shop_count = verified_orders.filter(payment_method='shop').count()

    # Delivery breakdown
    delivery_count = verified_orders.filter(delivery_option='delivery').count()
    pickup_count = verified_orders.filter(delivery_option='pickup').count()

    # Recent orders list
    recent_list = all_orders.order_by('-created_at')[:10]

    return render(request, 'watches/sales_stats.html', {
        'total_orders': total_orders,
        'total_verified': total_verified,
        'total_revenue': total_revenue,
        'pending_count': pending_count,
        'cancelled_count': cancelled_count,
        'delivered_count': delivered_count,
        'recent_revenue': recent_revenue,
        'week_orders': week_orders,
        'top_watches': top_watches,
        'gcash_count': gcash_count,
        'shop_count': shop_count,
        'delivery_count': delivery_count,
        'pickup_count': pickup_count,
        'recent_list': recent_list,
    })
