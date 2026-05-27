import base64
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.files.base import ContentFile
from .models import SariItem, StockLog
from .forms import SariItemForm


def _is_admin(user):
    return user.is_superuser or getattr(user, 'role', '') == 'admin'


def _save_item_image(request, item):
    data = request.POST.get('cropped_image_data', '')
    if data and data.startswith('data:image'):
        fmt, imgstr = data.split(';base64,')
        ext = fmt.split('/')[-1]
        item.image = ContentFile(base64.b64decode(imgstr), name=f'inv_{item.pk}.{ext}')
    return item


@login_required
def inventory_list(request):
    if not _is_admin(request.user):
        return redirect('dashboard')

    query = request.GET.get('q', '').strip()
    category_filter = request.GET.get('category', '')
    stock_filter = request.GET.get('stock', '')

    qs = SariItem.objects.all()
    if query:
        qs = qs.filter(name__icontains=query)
    if category_filter:
        qs = qs.filter(category=category_filter)
    if stock_filter == 'low':
        low_ids = [item.pk for item in qs if item.is_low_stock]
        qs = qs.filter(pk__in=low_ids)
    elif stock_filter == 'out':
        qs = qs.filter(stock_quantity=0)

    all_items = SariItem.objects.all()
    total_items = all_items.count()
    out_of_stock = all_items.filter(stock_quantity=0).count()
    low_stock_count = sum(1 for i in all_items if i.is_low_stock)
    categories = SariItem.CATEGORY_CHOICES

    return render(request, 'inventory/inventory_list.html', {
        'items': qs,
        'query': query,
        'category_filter': category_filter,
        'stock_filter': stock_filter,
        'categories': categories,
        'total_items': total_items,
        'out_of_stock': out_of_stock,
        'low_stock_count': low_stock_count,
    })


@login_required
def item_add(request):
    if not _is_admin(request.user):
        return redirect('dashboard')
    if request.method == 'POST':
        form = SariItemForm(request.POST, request.FILES)
        if form.is_valid():
            item = form.save(commit=False)
            item.save()
            item = _save_item_image(request, item)
            item.save()
            StockLog.objects.create(
                item=item, action='add',
                quantity_changed=item.stock_quantity,
                notes='Initial stock entry'
            )
            messages.success(request, f'"{item.name}" added to inventory.')
            return redirect('inventory_list')
        for field, errs in form.errors.items():
            for e in errs:
                messages.error(request, f'{field}: {e}')
    else:
        form = SariItemForm()
    return render(request, 'inventory/item_form.html', {'form': form, 'title': 'Add Item'})


@login_required
def item_edit(request, pk):
    if not _is_admin(request.user):
        return redirect('dashboard')
    item = get_object_or_404(SariItem, pk=pk)
    old_qty = item.stock_quantity
    if request.method == 'POST':
        form = SariItemForm(request.POST, request.FILES, instance=item)
        if form.is_valid():
            updated = form.save(commit=False)
            updated = _save_item_image(request, updated)
            updated.save()
            diff = updated.stock_quantity - old_qty
            if diff != 0:
                StockLog.objects.create(
                    item=updated, action='adjust',
                    quantity_changed=diff,
                    notes=request.POST.get('stock_note', '').strip() or 'Manual edit'
                )
            messages.success(request, f'"{updated.name}" updated.')
            return redirect('inventory_list')
        for field, errs in form.errors.items():
            for e in errs:
                messages.error(request, f'{field}: {e}')
    else:
        form = SariItemForm(instance=item)
    logs = item.logs.all()[:10]
    return render(request, 'inventory/item_form.html', {
        'form': form, 'title': 'Edit Item', 'item': item, 'logs': logs
    })


@login_required
def item_delete(request, pk):
    if not _is_admin(request.user):
        return redirect('dashboard')
    item = get_object_or_404(SariItem, pk=pk)
    if request.method == 'POST':
        name = item.name
        item.delete()
        messages.success(request, f'"{name}" removed from inventory.')
        return redirect('inventory_list')
    return render(request, 'inventory/item_confirm_delete.html', {'item': item})


@login_required
def quick_stock_update(request, pk):
    if not _is_admin(request.user):
        return redirect('dashboard')
    item = get_object_or_404(SariItem, pk=pk)
    if request.method == 'POST':
        action = request.POST.get('action')
        try:
            qty = int(request.POST.get('quantity', 1))
        except (ValueError, TypeError):
            qty = 1
        note = request.POST.get('notes', '').strip()

        if action == 'add':
            item.stock_quantity += qty
            log_action = 'add'
            change = qty
        elif action == 'remove':
            item.stock_quantity = max(0, item.stock_quantity - qty)
            log_action = 'remove'
            change = -qty
        else:
            messages.error(request, 'Invalid action.')
            return redirect('inventory_list')

        item.save()
        StockLog.objects.create(
            item=item, action=log_action,
            quantity_changed=change,
            notes=note or f'Quick {action}'
        )
        messages.success(request, f'Stock updated for "{item.name}".')
    return redirect('inventory_list')
