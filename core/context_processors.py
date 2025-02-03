# core/context_processors.py

from .models import Session


def user_sessions(request):
    if request.user.is_authenticated:
        return {"sessions": Session.objects.filter(user=request.user)}
    return {"sessions": []}
