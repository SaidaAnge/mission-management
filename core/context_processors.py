from .models import Notification

def unread_notifications(request):
    if request.user.is_authenticated:
        count = Notification.objects.filter(utilisateur=request.user, lue=False).count()
    else:
        count = 0
    return {'unread_notifications_count': count} 