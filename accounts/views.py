import base64
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.files.base import ContentFile
from django.http import JsonResponse
from .forms import RegisterForm, ProfileForm
from .models import CustomUser, Announcement, StoreSettings, DEFAULT_AI_KNOWLEDGE


def _is_admin(user):
    return user.is_superuser or getattr(user, 'role', '') == 'admin'


def _save_cropped_image(request, user):
    data = request.POST.get('cropped_image_data', '')
    if data and data.startswith('data:image'):
        fmt, imgstr = data.split(';base64,')
        ext = fmt.split('/')[-1]
        user.profile_picture = ContentFile(
            base64.b64decode(imgstr), name=f'profile_{user.pk}.{ext}'
        )
    return user


def home_redirect(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    return redirect('guest_home')


def guest_home(request):
    from watches.models import WatchItem
    watches = WatchItem.objects.filter(is_available=True, stock_quantity__gt=0).order_by('-created_at')[:6]
    announcements = Announcement.objects.order_by('-is_pinned', '-created_at')[:4]
    store = StoreSettings.get_settings()
    return render(request, 'accounts/guest_home.html', {
        'watches': watches, 'announcements': announcements, 'store': store
    })


def register_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.agreed_to_terms = False
            user.save()
            login(request, user)
            return redirect('agreement')
    else:
        form = RegisterForm()
    return render(request, 'accounts/register.html', {'form': form})


def agreement_view(request):
    if not request.user.is_authenticated:
        return redirect('login')
    if request.method == 'POST':
        if 'agree' in request.POST:
            request.user.agreed_to_terms = True
            request.user.save()
            return redirect('dashboard')
        messages.error(request, 'You must agree to the terms to continue.')
    return render(request, 'accounts/agreement.html')


def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            return redirect(request.GET.get('next', 'dashboard'))
        messages.error(request, 'Invalid username or password.')
    return render(request, 'accounts/login.html')


@login_required
def logout_view(request):
    if request.method == 'POST':
        logout(request)
        return redirect('login')
    return render(request, 'accounts/confirm_logout.html')


@login_required
def dashboard_view(request):
    if not request.user.agreed_to_terms and not request.user.is_superuser:
        return redirect('agreement')
    from watches.models import WatchItem, Order
    from inventory.models import SariItem
    if _is_admin(request.user):
        announcements = Announcement.objects.order_by('-is_pinned', '-created_at')
        watches_on_sale = WatchItem.objects.filter(is_available=True, stock_quantity__gt=0).count()
        low_stock_watches = WatchItem.objects.filter(is_available=True, stock_quantity__gt=0, stock_quantity__lte=2)
        out_of_stock_watches = WatchItem.objects.filter(stock_quantity=0)
        low_stock_sari = SariItem.objects.filter(stock_quantity__lte=5)
        pending_orders = Order.objects.filter(status='pending').count()
        total_watches = WatchItem.objects.count()
        total_sari = SariItem.objects.count()
        return render(request, 'accounts/dashboard_admin.html', {
            'announcements': announcements,
            'watches_on_sale': watches_on_sale,
            'low_stock_watches': low_stock_watches,
            'out_of_stock_watches': out_of_stock_watches,
            'low_stock_sari': low_stock_sari,
            'pending_orders': pending_orders,
            'total_watches': total_watches,
            'total_sari': total_sari,
        })
    else:
        announcements = Announcement.objects.order_by('-is_pinned', '-created_at')[:5]
        featured = WatchItem.objects.filter(is_available=True, stock_quantity__gt=0).order_by('-created_at')[:4]
        my_orders = Order.objects.filter(user=request.user).order_by('-created_at')[:5]
        return render(request, 'accounts/dashboard_user.html', {
            'announcements': announcements, 'featured': featured, 'my_orders': my_orders,
        })


@login_required
def announcement_create(request):
    if not _is_admin(request.user):
        return redirect('dashboard')
    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        content = request.POST.get('content', '').strip()
        image = request.FILES.get('image')
        is_pinned = request.POST.get('is_pinned') == 'on'
        if title and content:
            Announcement.objects.create(
                author=request.user, title=title, content=content,
                image=image, is_pinned=is_pinned
            )
            messages.success(request, 'Announcement posted.')
        return redirect('dashboard')
    return render(request, 'accounts/announcement_form.html', {'title': 'New Announcement'})


@login_required
def announcement_edit(request, pk):
    if not _is_admin(request.user):
        return redirect('dashboard')
    ann = get_object_or_404(Announcement, pk=pk)
    if request.method == 'POST':
        ann.title = request.POST.get('title', ann.title).strip()
        ann.content = request.POST.get('content', ann.content).strip()
        ann.is_pinned = request.POST.get('is_pinned') == 'on'
        if request.FILES.get('image'):
            ann.image = request.FILES['image']
        ann.save()
        messages.success(request, 'Announcement updated.')
        return redirect('dashboard')
    return render(request, 'accounts/announcement_form.html', {'ann': ann, 'title': 'Edit Announcement'})


@login_required
def announcement_delete(request, pk):
    if not _is_admin(request.user):
        return redirect('dashboard')
    ann = get_object_or_404(Announcement, pk=pk)
    if request.method == 'POST':
        ann.delete()
        messages.success(request, 'Announcement deleted.')
    return redirect('dashboard')


@login_required
def profile_view(request):
    return render(request, 'accounts/profile.html')


@login_required
def profile_edit(request):
    if request.method == 'POST':
        form = ProfileForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            user = form.save(commit=False)
            user = _save_cropped_image(request, user)
            user.save()
            messages.success(request, 'Profile updated.')
            return redirect('profile')
        for field, errs in form.errors.items():
            for e in errs:
                messages.error(request, f'{field}: {e}')
    else:
        form = ProfileForm(instance=request.user)
    return render(request, 'accounts/profile_edit.html', {'form': form})


# ── Store Settings — each section saves only its own fields ──────────────────
@login_required
def store_settings_view(request):
    if not _is_admin(request.user):
        return redirect('dashboard')

    settings_obj = StoreSettings.get_settings()
    active_tab = 'store'  # default tab to show after save

    if request.method == 'POST':
        section = request.POST.get('section', 'store')
        active_tab = section

        if section == 'store':
            settings_obj.store_name = request.POST.get('store_name', '').strip() or settings_obj.store_name
            settings_obj.store_hours = request.POST.get('store_hours', '').strip() or settings_obj.store_hours
            settings_obj.store_address = request.POST.get('store_address', settings_obj.store_address).strip()
            settings_obj.facebook_page_url = request.POST.get('facebook_page_url', '').strip()
            settings_obj.save(update_fields=['store_name', 'store_hours', 'store_address', 'facebook_page_url', 'updated_at'])
            messages.success(request, 'Store information saved.')

        elif section == 'gcash':
            settings_obj.gcash_number = request.POST.get('gcash_number', '').strip() or settings_obj.gcash_number
            settings_obj.gcash_name = request.POST.get('gcash_name', '').strip() or settings_obj.gcash_name
            try:
                settings_obj.delivery_fee = float(request.POST.get('delivery_fee', settings_obj.delivery_fee))
            except (ValueError, TypeError):
                pass
            settings_obj.delivery_area = request.POST.get('delivery_area', '').strip() or settings_obj.delivery_area
            settings_obj.save(update_fields=['gcash_number', 'gcash_name', 'delivery_fee', 'delivery_area', 'updated_at'])
            messages.success(request, 'GCash & Delivery settings saved.')

        elif section == 'ai':
            ai_info = request.POST.get('ai_store_info', '').strip()
            api_key = request.POST.get('groq_api_key', '').strip()
            settings_obj.ai_store_info = ai_info
            settings_obj.groq_api_key = api_key
            settings_obj.save(update_fields=['ai_store_info', 'groq_api_key', 'updated_at'])
            messages.success(request, 'AI knowledge base saved.')

        return redirect(f'/store-settings/#{active_tab}')

    return render(request, 'accounts/store_settings.html', {
        'settings': settings_obj,
        'default_ai_knowledge': DEFAULT_AI_KNOWLEDGE,
    })


# ── Order Management ─────────────────────────────────────────────────────────
@login_required
def orders_view(request):
    if not _is_admin(request.user):
        return redirect('dashboard')
    from watches.models import Order
    qs = Order.objects.select_related('user', 'watch_item').order_by('-created_at')
    status_filter = request.GET.get('status', '')
    search_query = request.GET.get('q', '').strip()
    if status_filter:
        qs = qs.filter(status=status_filter)
    if search_query:
        qs = (
            qs.filter(order_id__icontains=search_query) |
            qs.filter(user__username__icontains=search_query) |
            qs.filter(watch_item__name__icontains=search_query)
        )
    return render(request, 'accounts/orders.html', {
        'orders': qs,
        'status_filter': status_filter,
        'search_query': search_query,
        'status_choices': Order.STATUS_CHOICES,
    })


@login_required
def order_update(request, pk):
    if not _is_admin(request.user):
        return redirect('dashboard')
    from watches.models import Order
    order = get_object_or_404(Order, pk=pk)
    if request.method == 'POST':
        new_status = request.POST.get('status')
        admin_note = request.POST.get('admin_note', '').strip()
        valid = [s[0] for s in Order.STATUS_CHOICES]
        if new_status in valid:
            order.status = new_status
            order.admin_note = admin_note
            order.save()
            messages.success(request, f'Order {order.order_id} updated to {new_status}.')
    return redirect('orders')


# -- AI Chat (Groq - Free) --
def ai_chat(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'POST only'}, status=405)

    import json, os
    try:
        body = json.loads(request.body)
        user_message = body.get('message', '').strip()
    except Exception:
        user_message = request.POST.get('message', '').strip()

    if not user_message:
        return JsonResponse({'reply': 'Please type a question.'})

    store = StoreSettings.get_settings()
    ai_knowledge = store.get_ai_knowledge()

    from django.conf import settings as dj_settings
    api_key = (
        store.groq_api_key.strip()
        or os.environ.get('GROQ_API_KEY', '')
        or getattr(dj_settings, 'GROQ_API_KEY', '')
    )

    if not api_key:
        return JsonResponse({
            'reply': 'The AI assistant needs a Groq API key. It is free! The admin can add it in Store Settings > AI Assistant tab.'
        })

    lines = [
        'You are the friendly store assistant for "' + store.store_name + '" (SECONDS).',
        'You help customers with watches, repair services, ordering, GCash, and delivery.',
        '',
        'Store Info:',
        'Name: ' + store.store_name,
        'Hours: ' + store.store_hours,
        'Delivery Area: ' + store.delivery_area,
        'Address: ' + store.store_address,
        'GCash: ' + store.gcash_number + ' (' + store.gcash_name + ')',
        'Delivery Fee: P' + str(store.delivery_fee),
        '',
        'Knowledge Base:',
        ai_knowledge,
        '',
        'Rules:',
        '1. Only answer about watches, watch services, ordering, GCash, delivery, store info.',
        '2. For off-topic questions, politely say you can only help with store-related questions.',
        '3. NEVER share sari-sari inventory info.',
        '4. For repair prices, note they are estimates varying by watch type/brand/condition.',
        '5. Be friendly, helpful, concise.',
        '6. Respond in the same language as the customer (Filipino or English).',
        '7. If unsure, suggest contacting the store at ' + store.gcash_number + '.',
        '8. Keep answers short and clear - this is a chat widget.',
    ]
    system_prompt = '\n'.join(lines)

    try:
        from groq import Groq
        client = Groq(api_key=api_key)
        chat = client.chat.completions.create(
            model='llama-3.1-8b-instant',
            messages=[
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': user_message},
            ],
            max_tokens=400,
            temperature=0.7,
        )
        reply = chat.choices[0].message.content.strip()

    except Exception as e:
        err = str(e).lower()
        if 'invalid' in err or 'auth' in err or '401' in err or 'api_key' in err:
            reply = 'The AI assistant API key is invalid. Please ask the store admin to check Store Settings > AI Assistant.'
        elif 'quota' in err or '429' in err or 'rate' in err:
            reply = 'The assistant is busy right now. Please try again in a moment.'
        else:
            reply = 'Sorry, the assistant is unavailable. Please contact us at ' + store.gcash_number + '.'

    return JsonResponse({'reply': reply})



def ai_debug(request):
    """Temporary debug view - remove after fixing"""
    import os
    from django.conf import settings as dj_settings
    store = StoreSettings.get_settings()
    api_key = (
        store.groq_api_key.strip()
        or os.environ.get('GROQ_API_KEY', '')
        or getattr(dj_settings, 'GROQ_API_KEY', '')
    )
    key_preview = api_key[:8] + '...' + api_key[-4:] if len(api_key) > 12 else f'[{len(api_key)} chars]'
    
    result = {
        'key_in_db': bool(store.groq_api_key.strip()),
        'key_preview': key_preview if api_key else 'EMPTY',
        'key_length': len(api_key),
        'store_name': store.store_name,
    }
    
    if api_key:
        try:
            from groq import Groq
            client = Groq(api_key=api_key)
            chat = client.chat.completions.create(
                model='llama-3.1-8b-instant',
                messages=[{'role': 'user', 'content': 'Say "API key works!" in one sentence.'}],
                max_tokens=50,
            )
            result['test_response'] = chat.choices[0].message.content.strip()
            result['status'] = 'SUCCESS'
        except Exception as e:
            result['status'] = 'FAILED'
            result['error'] = str(e)
    else:
        result['status'] = 'NO KEY'
    
    from django.http import JsonResponse
    return JsonResponse(result)

def ai_list_models(request):
    """Debug: list available models for the current API key"""
    import os
    from django.conf import settings as dj_settings
    from django.http import JsonResponse
    
    store = StoreSettings.get_settings()
    api_key = store.groq_api_key.strip() or os.environ.get('GROQ_API_KEY', '')
    
    if not api_key:
        return JsonResponse({'error': 'No API key set'})
    
    try:
        from google import genai
        client = genai.Client(api_key=api_key)
        
        # List all available models
        models = client.models.list()
        model_names = []
        for m in models:
            model_names.append({
                'name': m.name,
                'display_name': getattr(m, 'display_name', ''),
                'supported_actions': getattr(m, 'supported_actions', []),
            })
        return JsonResponse({'models': model_names, 'count': len(model_names)})
    except Exception as e:
        return JsonResponse({'error': str(e)})
