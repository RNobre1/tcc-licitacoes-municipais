from django.conf import settings


def system_name(request):
    return {
        "system_name": settings.SYSTEM_NAME,
    }
