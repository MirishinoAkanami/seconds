from .models import StoreSettings


def global_context(request):
    store = StoreSettings.get_settings()
    return {
        'store': store,
        'is_admin_user': (
            request.user.is_authenticated and
            (request.user.is_superuser or getattr(request.user, 'role', '') == 'admin')
        ),
    }
