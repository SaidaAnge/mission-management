from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages
from django.http import HttpResponseForbidden
from django.utils import timezone

def admin_required(view_func):
    """
    Décorateur pour restreindre l'accès aux administrateurs uniquement
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('connexion')
        
        if request.user.role != 'administrateur':
            messages.error(request, "Accès refusé. Vous devez être administrateur pour accéder à cette page.")
            return HttpResponseForbidden("Accès refusé".encode())
        
        return view_func(request, *args, **kwargs)
    return _wrapped_view

def employe_required(view_func):
    """
    Décorateur pour restreindre l'accès aux employés et freelances uniquement
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('connexion')
        
        if request.user.role not in ['employe', 'freelance']:
            messages.error(request, "Accès refusé. Cette page est réservée aux employés et freelances.")
            return HttpResponseForbidden("Accès refusé".encode())
        
        return view_func(request, *args, **kwargs)
    return _wrapped_view

def is_admin(user):
    """
    Vérifie si l'utilisateur est administrateur
    """
    return user.is_authenticated and user.role == 'administrateur'

def is_employe_or_freelance(user):
    """
    Vérifie si l'utilisateur est employé ou freelance
    """
    return user.is_authenticated and user.role in ['employe', 'freelance']

def can_assign_mission(user):
    """
    Vérifie si l'utilisateur peut assigner des missions
    """
    return is_admin(user)

def can_create_mission(user):
    """
    Vérifie si l'utilisateur peut créer des missions
    """
    return is_admin(user)

def can_edit_mission(user, mission):
    """
    Vérifie si l'utilisateur peut éditer une mission
    """
    if is_admin(user):
        return True
    return user == mission.assigne_a

def can_view_mission(user, mission):
    """
    Vérifie si l'utilisateur peut voir une mission
    """
    if is_admin(user):
        return True
    return user == mission.assigne_a

def can_edit_intervention(user, intervention):
    """
    Vérifie si l'utilisateur peut éditer une intervention
    """
    if is_admin(user):
        return True
    return user == intervention.intervenant

def can_view_intervention(user, intervention):
    """
    Vérifie si l'utilisateur peut voir une intervention
    """
    if is_admin(user):
        return True
    return user == intervention.intervenant 