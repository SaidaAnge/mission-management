from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.template.loader import get_template
from django.conf import settings
from django.views import View
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from .forms import InterventionForm, PieceJointeForm, RapportInterventionForm, RapportValidationForm
from .forms import RetardInterventionForm, RetardResolutionForm, InterventionRetardForm
from .models import Client, Mission, Intervention, PieceJointe, RapportIntervention, RapportFichierJoint
from .models import Utilisateur, RetardIntervention
from .permissions import admin_required, employe_required, is_admin, can_view_mission, can_view_intervention
import os
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from datetime import datetime, timedelta
from .models import Notification
from django.db import models
from .forms import UtilisateurCreationForm
from django.core.exceptions import PermissionDenied
from .forms import UtilisateurProfilForm
from .forms import InterventionCompteRenduForm
from django.utils import timezone
from django.contrib.auth.models import User
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.urls import reverse
from django.core.mail import send_mail
from .forms import PasswordResetByUsernameForm
import random
from django.contrib.auth.hashers import make_password

# pyright: ignore[reportAttributeAccessIssue]

# Supprimer toute vue ou code utilisant InscriptionForm
# (Aucune vue d'inscription personnalisée n'est nécessaire ici)

@login_required
def dashboard(request):
    user = request.user
    unread_notifications_count = get_unread_notifications_count(request)
    
    if is_admin(user):
        # Dashboard administrateur - toutes les missions et interventions
        missions = Mission.objects.all().order_by('-date_creation')[:2]
        interventions = Intervention.objects.all().order_by('-date_creation')[:2]
        total_missions = Mission.objects.count()
        total_interventions = Intervention.objects.count()
        missions_en_cours = Mission.objects.filter(statut='en_cours').count()
        interventions_en_cours = Intervention.objects.filter(statut='en_cours').count()
    else:
        # Dashboard employé/freelance - seulement ses missions et interventions
        missions = Mission.objects.filter(assigne_a=user).order_by('-date_creation')[:2]
        interventions = Intervention.objects.filter(intervenant=user).order_by('-date_creation')[:2]
        total_missions = Mission.objects.filter(assigne_a=user).count()
        total_interventions = Intervention.objects.filter(intervenant=user).count()
        missions_en_cours = Mission.objects.filter(assigne_a=user, statut='en_cours').count()
        interventions_en_cours = Intervention.objects.filter(intervenant=user, statut='en_cours').count()
    
    context = {
        'user': user,
        'role': user.role,
        'missions': missions,
        'interventions': interventions,
        'total_missions': total_missions,
        'total_interventions': total_interventions,
        'missions_en_cours': missions_en_cours,
        'interventions_en_cours': interventions_en_cours,
        'unread_notifications_count': unread_notifications_count,
    }
    return render(request, 'core/dashboard.html', context)

@login_required
def client_list(request):
    clients = Client.objects.all().order_by('-id')
    context = {
        'clients': clients,
        'user': request.user,
    }
    return render(request, 'core/client_list.html', context)

@login_required
def client_create(request):
    if request.method == 'POST':
        nom = request.POST.get('nom')
        contact = request.POST.get('contact')
        email = request.POST.get('email')
        telephone = request.POST.get('telephone')
        adresse = request.POST.get('adresse')
        
        Client.objects.create(
            nom=nom,
            contact=contact,
            email=email,
            telephone=telephone,
            adresse=adresse
        )
        messages.success(request, 'Client créé avec succès !')
        return redirect('client_list')
    
    context = {
        'user': request.user,
    }
    return render(request, 'core/client_form.html', context)

@login_required
def client_edit(request, client_id):
    client = get_object_or_404(Client, id=client_id)
    
    if request.method == 'POST':
        client.nom = request.POST.get('nom')
        client.contact = request.POST.get('contact')
        client.email = request.POST.get('email')
        client.telephone = request.POST.get('telephone')
        client.adresse = request.POST.get('adresse')
        client.save()
        
        messages.success(request, 'Client modifié avec succès !')
        return redirect('client_list')
    
    context = {
        'client': client,
        'user': request.user,
    }
    return render(request, 'core/client_form.html', context)

@login_required
def client_delete(request, client_id):
    client = get_object_or_404(Client, id=client_id)
    client.delete()
    messages.success(request, 'Client supprimé avec succès !')
    return redirect('client_list')

# Vues pour les missions
@login_required
def mission_list(request):
    user = request.user
    
    if is_admin(user):
        # Administrateur voit toutes les missions
        missions = Mission.objects.all().order_by('-date_creation')
    else:
        # Employé/freelance ne voit que ses missions assignées
        missions = Mission.objects.filter(assigne_a=user).order_by('-date_creation')
    
    context = {
        'missions': missions,
        'user': request.user,
    }
    return render(request, 'core/mission_list.html', context)

@login_required
def mission_detail(request, mission_id):
    mission = get_object_or_404(Mission, id=mission_id)
    
    # Vérifier les permissions
    if not can_view_mission(request.user, mission):
        messages.error(request, "Vous n'avez pas les permissions pour voir cette mission.")
        return redirect('mission_list')
    
    context = {
        'mission': mission,
        'user': request.user,
    }
    return render(request, 'core/mission_detail.html', context)

@login_required
def mission_create(request):
    if request.method == 'POST':
        client_id = request.POST.get('client')
        titre = request.POST.get('titre')
        description = request.POST.get('description')
        nature = request.POST.get('nature')
        date = request.POST.get('date')
        lieu = request.POST.get('lieu')
        frequence = request.POST.get('frequence')
        assigne_a_id = request.POST.get('assigne_a')
        
        client = get_object_or_404(Client, id=client_id)
        assigne_a = None
        if assigne_a_id:
            assigne_a = get_object_or_404(Utilisateur, id=assigne_a_id)
        
        mission = Mission.objects.create(
            client=client,
            titre=titre,
            description=description,
            nature=nature,
            date=date,
            lieu=lieu,
            frequence=frequence,
            assigne_a=assigne_a
        )
        messages.success(request, 'Mission créée avec succès !')
        
        # Créer une notification pour l'utilisateur assigné
        if assigne_a:
            create_notification(
                assigne_a,
                f"Nouvelle mission assignée : {mission.titre}",
                "mission_assignment"
            )
        
        return redirect('mission_list')
    
    clients = Client.objects.all()
    utilisateurs = Utilisateur.objects.filter(role__in=['employe', 'freelance'])
    context = {
        'clients': clients,
        'utilisateurs': utilisateurs,
        'user': request.user,
    }
    return render(request, 'core/mission_form.html', context)

@login_required
def mission_edit(request, mission_id):
    mission = get_object_or_404(Mission, id=mission_id)
    
    if request.method == 'POST':
        client_id = request.POST.get('client')
        titre = request.POST.get('titre')
        description = request.POST.get('description')
        nature = request.POST.get('nature')
        date = request.POST.get('date')
        lieu = request.POST.get('lieu')
        frequence = request.POST.get('frequence')
        assigne_a_id = request.POST.get('assigne_a')
        statut = request.POST.get('statut')
        
        mission.client = get_object_or_404(Client, id=client_id)
        mission.titre = titre
        mission.description = description
        mission.nature = nature
        mission.date = date
        mission.lieu = lieu
        mission.frequence = frequence
        mission.statut = statut
        
        ancien_assigne_a = mission.assigne_a  # Sauvegarde de l'ancien assigné
        if assigne_a_id:
            mission.assigne_a = get_object_or_404(Utilisateur, id=assigne_a_id)
        else:
            mission.assigne_a = None
        
        mission.save()
        messages.success(request, 'Mission modifiée avec succès !')
        
        # Notifier le nouvel assigné si l'assignation a changé
        if mission.assigne_a and mission.assigne_a != ancien_assigne_a:
            create_notification(
                mission.assigne_a,
                f"Vous avez été assigné à la mission : {mission.titre}",
                "mission_assignment"
            )
        return redirect('mission_list')
    
    clients = Client.objects.all()
    utilisateurs = Utilisateur.objects.filter(role__in=['employe', 'freelance'])
    context = {
        'mission': mission,
        'clients': clients,
        'utilisateurs': utilisateurs,
        'user': request.user,
    }
    return render(request, 'core/mission_form.html', context)

@login_required
def mission_delete(request, mission_id):
    mission = get_object_or_404(Mission, id=mission_id)
    mission.delete()
    messages.success(request, 'Mission supprimée avec succès !')
    return redirect('mission_list')

# Vues pour les interventions
@login_required
def intervention_list(request):
    user = request.user
    if is_admin(user):
        # Administrateur voit toutes les interventions
        interventions = Intervention.objects.all().order_by('-date')
    elif Mission.objects.filter(assigne_a=user).exists():
        # Chef de projet : voit les interventions de ses missions (créées ou assignées à lui ou à d'autres)
        missions_ids = Mission.objects.filter(assigne_a=user).values_list('id', flat=True)
        interventions = Intervention.objects.filter(mission_id__in=missions_ids).order_by('-date')
    else:
        # Employé/freelance : ne voit que ses interventions assignées
        interventions = Intervention.objects.filter(intervenant=user).order_by('-date')
    context = {
        'interventions': interventions,
        'user': request.user,
    }
    return render(request, 'core/intervention_list.html', context)

@login_required
def intervention_detail(request, intervention_id):
    intervention = get_object_or_404(Intervention, id=intervention_id)
    
    # Vérifier les permissions
    if not can_view_intervention(request.user, intervention):
        messages.error(request, "Vous n'avez pas les permissions pour voir cette intervention.")
        return redirect('intervention_list')
    
    pieces_jointes = intervention.pieces_jointes.all()
    context = {
        'intervention': intervention,
        'pieces_jointes': pieces_jointes,
        'user': request.user,
    }
    return render(request, 'core/intervention_detail.html', context)

@login_required
def intervention_create(request):
    from .forms import PieceJointeFormSet
    is_admin_user = is_admin(request.user)
    mission_id = request.GET.get('mission_id')
    mission_instance = None
    if is_admin_user:
        if mission_id:
            try:
                mission_instance = Mission.objects.get(id=mission_id)
            except Mission.DoesNotExist:
                mission_instance = None
    else:
        if not mission_id:
            messages.error(request, "Vous devez passer par une mission à laquelle vous êtes assigné pour ajouter une intervention.")
            return redirect('mission_list')
        try:
            mission_instance = Mission.objects.get(id=mission_id, assigne_a=request.user)
        except Mission.DoesNotExist:
            messages.error(request, "Mission non trouvée ou vous n'êtes pas assigné à cette mission.")
            return redirect('mission_list')

    if request.method == 'POST':
        form = InterventionForm(request.POST)
        formset = PieceJointeFormSet(request.POST, request.FILES, queryset=PieceJointe.objects.none())
        if form.is_valid() and formset.is_valid():
            intervention = form.save(commit=False)
            intervention.cree_par = request.user
            if not is_admin_user:
                intervention.mission = mission_instance
            if not (is_admin_user or (intervention.mission.assigne_a == request.user)):
                raise PermissionDenied("Vous n'êtes pas chef de projet de cette mission.")
            intervention.save()
            form.save_m2m()
            # Pièces jointes
            for piece_form in formset:
                if piece_form.cleaned_data and not piece_form.cleaned_data.get('DELETE', False):
                    piece = piece_form.save(commit=False)
                    piece.intervention = intervention
                    piece.save()
            # Notification
            if intervention.intervenant:
                create_notification(
                    intervention.intervenant,
                    f"Nouvelle intervention assignée : {intervention.titre}",
                    "intervention_assignment"
                )
            messages.success(request, 'Intervention créée avec succès !')
            return redirect('intervention_detail', intervention_id=intervention.id)
    else:
        if mission_instance:
            form = InterventionForm(initial={'mission': mission_instance})
        else:
            form = InterventionForm()
        if is_admin_user:
            form.fields['mission'].queryset = Mission.objects.all()
        elif mission_instance:
            form.fields['mission'].queryset = Mission.objects.filter(id=mission_instance.id)
            form.fields['mission'].empty_label = None
        formset = PieceJointeFormSet(queryset=PieceJointe.objects.none())
    return render(request, 'core/intervention_form.html', {
        'form': form,
        'formset': formset,
        'user': request.user,
        'mission_instance': mission_instance,
        'is_admin_user': is_admin_user,
    })

@login_required
def intervention_edit(request, intervention_id):
    intervention = get_object_or_404(Intervention, id=intervention_id)
    if not (is_admin(request.user) or intervention.cree_par == request.user):
        raise PermissionDenied("Vous n'avez pas le droit de modifier cette intervention.")
    if hasattr(intervention, 'rapport') and intervention.rapport.statut == 'valide':
        messages.error(request, "Cette intervention est verrouillée car son rapport a été validé. Aucune modification n'est possible.")
        return redirect('intervention_detail', intervention_id=intervention.id)
    if request.method == 'POST':
        form = InterventionForm(request.POST, instance=intervention)
        if form.is_valid():
            form.save()
            
            # Gestion des pièces jointes
            piece_jointe_titre = request.POST.get('piece_jointe_titre')
            piece_jointe_type = request.POST.get('piece_jointe_type')
            piece_jointe_fichier = request.FILES.get('piece_jointe_fichier')
            piece_jointe_description = request.POST.get('piece_jointe_description')
            
            if piece_jointe_titre and piece_jointe_fichier and piece_jointe_type:
                PieceJointe.objects.create(
                    intervention=intervention,
                    titre=piece_jointe_titre,
                    fichier=piece_jointe_fichier,
                    type_fichier=piece_jointe_type,
                    description=piece_jointe_description or ''
                )
            
            messages.success(request, 'Intervention modifiée avec succès !')
            return redirect('intervention_detail', intervention_id=intervention.id)
    else:
        form = InterventionForm(instance=intervention)
    return render(request, 'core/intervention_form.html', {
        'form': form,
        'intervention': intervention,
        'user': request.user,
    })

@login_required
def intervention_delete(request, intervention_id):
    intervention = get_object_or_404(Intervention, id=intervention_id)
    if not (is_admin(request.user) or intervention.cree_par == request.user):
        raise PermissionDenied("Vous n'avez pas le droit de supprimer cette intervention.")
    if hasattr(intervention, 'rapport') and intervention.rapport.statut == 'valide':
        messages.error(request, "Cette intervention est verrouillée car son rapport a été validé. Suppression impossible.")
        return redirect('intervention_detail', intervention_id=intervention.id)
    intervention.delete()
    messages.success(request, 'Intervention supprimée avec succès !')
    return redirect('intervention_list')

# Vues pour les pièces jointes
@login_required
def piece_jointe_create(request, intervention_id):
    intervention = get_object_or_404(Intervention, id=intervention_id)
    
    if request.method == 'POST':
        form = PieceJointeForm(request.POST, request.FILES)
        if form.is_valid():
            piece_jointe = form.save(commit=False)
            piece_jointe.intervention = intervention
            piece_jointe.save()
            messages.success(request, 'Pièce jointe ajoutée avec succès !')
            return redirect('intervention_detail', intervention_id=intervention.id)
    else:
        form = PieceJointeForm()
    
    context = {
        'form': form,
        'intervention': intervention,
        'user': request.user,
    }
    return render(request, 'core/piece_jointe_form.html', context)

@login_required
def piece_jointe_delete(request, piece_jointe_id):
    piece_jointe = get_object_or_404(PieceJointe, id=piece_jointe_id)
    intervention_id = piece_jointe.intervention.id
    if hasattr(piece_jointe.intervention, 'rapport') and piece_jointe.intervention.rapport.statut == 'valide':
        messages.error(request, "Impossible de supprimer une pièce jointe : l'intervention est verrouillée car son rapport a été validé.")
        return redirect('intervention_detail', intervention_id=intervention_id)
    piece_jointe.delete()
    messages.success(request, 'Pièce jointe supprimée avec succès !')
    return redirect('intervention_detail', intervention_id=intervention_id)

# Vues pour les rapports
@login_required
def rapports_dashboard(request):
    """Vue pour afficher le dashboard des rapports pour l'utilisateur connecté"""
    user = request.user
    rapports = []
    if user.role in ['employe', 'freelance']:
        # L'intervenant ne voit que ses rapports
        rapports = RapportIntervention.objects.filter(
            intervention__intervenant=user,
            statut__in=['brouillon', 'soumis', 'rejete', 'valide']
        ).select_related('intervention', 'intervention__mission').order_by('-date_creation')
        missions = None
    else:
        # L'admin voit tout
        rapports = RapportIntervention.objects.all().select_related('intervention', 'intervention__mission').order_by('-date_creation')
        missions = Mission.objects.all().order_by('-date_creation')
    context = {
        'rapports': rapports,
        'missions': missions,
        'user': user,
    }
    return render(request, 'core/rapports_dashboard.html', context)

@login_required
def rapport_mission(request, mission_id):
    """Vue pour afficher le rapport d'une mission spécifique"""
    mission = get_object_or_404(Mission, id=mission_id)
    interventions = mission.interventions.all().order_by('-date')
    
    context = {
        'mission': mission,
        'interventions': interventions,
        'user': request.user,
    }
    return render(request, 'core/rapport_mission.html', context)

@login_required
def rapport_intervention(request, intervention_id):
    """Vue pour afficher le rapport d'une intervention spécifique"""
    intervention = get_object_or_404(Intervention, id=intervention_id)
    pieces_jointes = intervention.pieces_jointes.all()
    rapport = getattr(intervention, 'rapport', None)
    
    context = {
        'intervention': intervention,
        'pieces_jointes': pieces_jointes,
        'rapport': rapport,
        'user': request.user,
    }
    return render(request, 'core/rapport_intervention.html', context)

@login_required
def rapport_intervention_create(request, intervention_id):
    """Vue pour créer un rapport d'intervention détaillé"""
    intervention = get_object_or_404(Intervention, id=intervention_id)
    # Vérifier que seul l'intervenant assigné peut créer le rapport
    if request.user != intervention.intervenant:
        messages.error(request, "Vous n'êtes pas autorisé à créer le rapport pour cette intervention.")
        return redirect('intervention_detail', intervention_id=intervention.id)
    # Vérifier si un rapport existe déjà
    if hasattr(intervention, 'rapport'):
        messages.warning(request, 'Un rapport existe déjà pour cette intervention.')
        return redirect('rapport_intervention', intervention_id=intervention.id)
    if request.method == 'POST':
        form = RapportInterventionForm(request.POST, request.FILES)
        action = request.POST.get('action')
        
        # Debug: afficher les erreurs du formulaire
        if not form.is_valid():
            print("Erreurs du formulaire:", form.errors)
            messages.error(request, f"Erreurs de validation: {form.errors}")
            context = {
                'form': form,
                'intervention': intervention,
                'user': request.user,
            }
            return render(request, 'core/rapport_intervention_form.html', context)
        
        if form.is_valid():
            rapport = form.save(commit=False)
            rapport.intervention = intervention
            if action == 'soumettre':
                rapport.statut = 'soumis'
                messages.success(request, 'Rapport soumis à l\'administrateur !')
            else:
                rapport.statut = 'brouillon'
                messages.info(request, 'Rapport enregistré en brouillon.')
            rapport.save()
            
            # Gérer les fichiers uploadés
            preuves = request.FILES.getlist('preuves')
            print(f"Nombre de fichiers uploadés: {len(preuves)}")
            for preuve in preuves:
                try:
                    RapportFichierJoint.objects.create(
                        rapport=rapport,
                        fichier=preuve,
                        description=f"Preuve ajoutée le {timezone.now().strftime('%d/%m/%Y')}"
                    )
                    print(f"Fichier {preuve.name} enregistré avec succès")
                except Exception as e:
                    print(f"Erreur lors de l'enregistrement du fichier {preuve.name}: {e}")
                    messages.error(request, f"Erreur lors de l'enregistrement du fichier {preuve.name}: {e}")
            
            return redirect('rapports_dashboard')
    else:
        form = RapportInterventionForm()
    context = {
        'form': form,
        'intervention': intervention,
        'user': request.user,
    }
    return render(request, 'core/rapport_intervention_form.html', context)

@login_required
def rapport_intervention_edit(request, intervention_id):
    """Vue pour éditer un rapport d'intervention détaillé"""
    intervention = get_object_or_404(Intervention, id=intervention_id)
    rapport = getattr(intervention, 'rapport', None)
    if not rapport:
        messages.error(request, 'Aucun rapport trouvé pour cette intervention.')
        return redirect('rapport_intervention', intervention_id=intervention.id)
    # Vérifier que seul l'intervenant assigné peut modifier, et seulement si statut brouillon ou rejeté
    if request.user != intervention.intervenant or rapport.statut not in ['brouillon', 'rejete']:
        messages.error(request, "Vous n'êtes pas autorisé à modifier ce rapport.")
        return redirect('rapport_intervention', intervention_id=intervention.id)
    if rapport.statut == 'valide':
        messages.error(request, "Ce rapport a été validé et ne peut plus être modifié.")
        return redirect('rapport_intervention', intervention_id=intervention.id)
    if request.method == 'POST':
        form = RapportInterventionForm(request.POST, request.FILES, instance=rapport)
        action = request.POST.get('action')
        
        # Debug: afficher les erreurs du formulaire
        if not form.is_valid():
            print("Erreurs du formulaire:", form.errors)
            messages.error(request, f"Erreurs de validation: {form.errors}")
            context = {
                'form': form,
                'intervention': intervention,
                'rapport': rapport,
                'user': request.user,
            }
            return render(request, 'core/rapport_intervention_form.html', context)
        
        if form.is_valid():
            rapport = form.save(commit=False)
            if action == 'soumettre':
                rapport.statut = 'soumis'
                messages.success(request, 'Rapport soumis à l\'administrateur !')
            else:
                rapport.statut = 'brouillon'
                messages.info(request, 'Rapport enregistré en brouillon.')
            rapport.save()
            
            # Gérer les fichiers uploadés
            preuves = request.FILES.getlist('preuves')
            print(f"Nombre de fichiers uploadés: {len(preuves)}")
            for preuve in preuves:
                try:
                    RapportFichierJoint.objects.create(
                        rapport=rapport,
                        fichier=preuve,
                        description=f"Preuve ajoutée le {timezone.now().strftime('%d/%m/%Y')}"
                    )
                    print(f"Fichier {preuve.name} enregistré avec succès")
                except Exception as e:
                    print(f"Erreur lors de l'enregistrement du fichier {preuve.name}: {e}")
                    messages.error(request, f"Erreur lors de l'enregistrement du fichier {preuve.name}: {e}")
            
            return redirect('rapport_intervention', intervention_id=intervention.id)
    else:
        form = RapportInterventionForm(instance=rapport)
    context = {
        'form': form,
        'intervention': intervention,
        'rapport': rapport,
        'user': request.user,
    }
    return render(request, 'core/rapport_intervention_form.html', context)

@admin_required
def rapport_intervention_validate(request, intervention_id):
    """Vue pour valider ou rejeter un rapport d'intervention (admin)"""
    intervention = get_object_or_404(Intervention, id=intervention_id)
    rapport = getattr(intervention, 'rapport', None)
    
    if not rapport:
        messages.error(request, 'Aucun rapport trouvé pour cette intervention.')
        return redirect('rapport_intervention', intervention_id=intervention.id)
    
    if rapport.statut != 'soumis':
        messages.warning(request, "Seuls les rapports soumis peuvent être validés ou rejetés.")
        return redirect('rapport_intervention', intervention_id=intervention.id)
    
    if rapport.statut == 'valide':
        messages.error(request, "Ce rapport a déjà été validé et ne peut plus être modifié.")
        return redirect('rapport_intervention', intervention_id=intervention.id)
    
    if request.method == 'POST':
        form = RapportValidationForm(request.POST)
        if form.is_valid():
            action = form.cleaned_data['action']
            commentaire_validation = form.cleaned_data['commentaire_validation']
            motif_rejet = form.cleaned_data['motif_rejet']
            
            if action == 'valider':
                rapport.statut = 'valide'
                rapport.commentaire_validation = commentaire_validation
                rapport.motif_rejet = ''
                rapport.valide_par = request.user
                rapport.rejete_par = None
                rapport.date_validation = timezone.now()
                rapport.save()
                
                # Créer une notification pour l'intervenant
                if intervention.intervenant:
                    create_notification(
                        intervention.intervenant,
                        f"Votre rapport d'intervention '{intervention.titre}' a été validé. {commentaire_validation if commentaire_validation else ''}",
                        "rapport_valide"
                    )
                
                messages.success(request, 'Rapport validé avec succès !')
                
            elif action == 'rejeter':
                rapport.statut = 'rejete'
                rapport.motif_rejet = motif_rejet
                rapport.commentaire_validation = ''
                rapport.rejete_par = request.user
                rapport.valide_par = None
                rapport.date_validation = timezone.now()
                rapport.save()
                
                # Créer une notification pour l'intervenant
                if intervention.intervenant:
                    create_notification(
                        intervention.intervenant,
                        f"Votre rapport d'intervention '{intervention.titre}' a été rejeté. Motif : {motif_rejet}",
                        "rapport_rejete"
                    )
                
                messages.success(request, 'Rapport rejeté avec succès !')
            
            return redirect('rapport_intervention', intervention_id=intervention.id)
    else:
        form = RapportValidationForm()
    
    context = {
        'intervention': intervention,
        'rapport': rapport,
        'form': form,
        'user': request.user,
    }
    return render(request, 'core/rapport_intervention_validate.html', context)

@login_required
def rapport_intervention_submit(request, intervention_id):
    """Vue pour soumettre un rapport d'intervention (intervenant)"""
    intervention = get_object_or_404(Intervention, id=intervention_id)
    rapport = getattr(intervention, 'rapport', None)
    if not rapport:
        messages.error(request, 'Aucun rapport trouvé pour cette intervention.')
        return redirect('rapport_intervention', intervention_id=intervention.id)
    # Vérifier que seul l'intervenant assigné peut soumettre, et seulement si statut brouillon ou rejeté
    if request.user != intervention.intervenant or rapport.statut not in ['brouillon', 'rejete']:
        messages.error(request, "Vous n'êtes pas autorisé à soumettre ce rapport.")
        return redirect('rapport_intervention', intervention_id=intervention.id)
    if rapport.statut == 'valide':
        messages.error(request, "Ce rapport a été validé et ne peut plus être soumis.")
        return redirect('rapport_intervention', intervention_id=intervention.id)
    if request.method == 'POST':
        rapport.statut = 'soumis'
        # Réinitialiser les champs de validation si le rapport était rejeté
        if rapport.statut == 'rejete':
            rapport.motif_rejet = ''
            rapport.commentaire_validation = ''
            rapport.valide_par = None
            rapport.rejete_par = None
            rapport.date_validation = None
        rapport.save()
        # Notifier tous les administrateurs
        admins = Utilisateur.objects.filter(role='administrateur')
        for admin in admins:
            create_notification(
                admin,
                f"Nouveau rapport d'intervention soumis pour la mission : {intervention.mission.titre}",
                "nouveau_rapport_intervention"
            )
        messages.success(request, 'Rapport soumis avec succès. Il est maintenant en attente de validation.')
        return redirect('rapport_intervention', intervention_id=intervention.id)
    context = {
        'intervention': intervention,
        'rapport': rapport,
        'user': request.user,
    }
    return render(request, 'core/rapport_intervention_submit.html', context)

@login_required
def generer_pdf_mission(request, mission_id):
    """Génère un PDF pour une mission spécifique"""
    mission = get_object_or_404(Mission, id=mission_id)
    interventions = mission.interventions.all().order_by('-date')
    
    # Créer le PDF
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()
    story = []
    
    # Titre du rapport
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        spaceAfter=30,
        alignment=TA_CENTER,
        textColor=colors.darkblue
    )
    story.append(Paragraph(f"Rapport de Mission: {mission.titre}", title_style))
    story.append(Spacer(1, 20))
    
    # Informations de la mission
    mission_data = [
        ['Client:', mission.client.nom],
        ['Titre:', mission.titre],
        ['Description:', mission.description],
        ['Nature:', mission.nature],
        ['Date de début:', mission.date.strftime('%d/%m/%Y')],
        ['Lieu:', mission.lieu],
        ['Fréquence:', mission.frequence or 'Non spécifiée'],
        ['Assigné à:', f"{mission.assigne_a.first_name} {mission.assigne_a.last_name}" if mission.assigne_a else 'Non assigné'],
        ['Statut:', mission.get_statut_display()],
        ['Date de création:', mission.date_creation.strftime('%d/%m/%Y à %H:%M')],
    ]
    
    mission_table = Table(mission_data, colWidths=[2*inch, 4*inch])
    mission_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))
    story.append(mission_table)
    story.append(Spacer(1, 20))
    
    # Interventions
    if interventions:
        story.append(Paragraph("Interventions réalisées:", styles['Heading2']))
        story.append(Spacer(1, 10))
        
        for intervention in interventions:
            intervention_data = [
                ['Titre:', intervention.titre],
                ['Date:', intervention.date.strftime('%d/%m/%Y')],
                ['Lieu:', intervention.lieu],
                ['Intervenant:', f"{intervention.intervenant.first_name} {intervention.intervenant.last_name}" if intervention.intervenant else 'Non spécifié'],
                ['Statut:', intervention.get_statut_display()],
                ['Compte rendu:', intervention.compte_rendu or 'Aucun compte rendu'],
                ['Ressources utilisées:', intervention.ressources_utilisees or 'Aucune ressource spécifiée'],
            ]
            
            intervention_table = Table(intervention_data, colWidths=[2*inch, 4*inch])
            intervention_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, -1), colors.lightblue),
                ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ]))
            story.append(intervention_table)
            story.append(Spacer(1, 10))
    else:
        story.append(Paragraph("Aucune intervention réalisée pour cette mission.", styles['Normal']))
    
    # Générer le PDF
    doc.build(story)
    
    # Préparer la réponse
    pdf = buffer.getvalue()
    buffer.close()
    
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="rapport_mission_{mission.id}.pdf"'
    response.write(pdf)
    return response

@login_required
def generer_pdf_intervention(request, intervention_id):
    """Génère un PDF pour une intervention spécifique"""
    intervention = get_object_or_404(Intervention, id=intervention_id)
    pieces_jointes = intervention.pieces_jointes.all()
    
    # Créer le PDF
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()
    story = []
    
    # Titre du rapport
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        spaceAfter=30,
        alignment=TA_CENTER,
        textColor=colors.darkblue
    )
    story.append(Paragraph(f"Rapport d'Intervention: {intervention.titre}", title_style))
    story.append(Spacer(1, 20))
    
    # Informations de l'intervention
    intervention_data = [
        ['Mission:', intervention.mission.titre],
        ['Titre:', intervention.titre],
        ['Date:', intervention.date.strftime('%d/%m/%Y')],
        ['Lieu:', intervention.lieu],
        ['Intervenant:', f"{intervention.intervenant.first_name} {intervention.intervenant.last_name}" if intervention.intervenant else 'Non spécifié'],
        ['Statut:', intervention.get_statut_display()],
        ['Date de création:', intervention.date_creation.strftime('%d/%m/%Y à %H:%M')],
        ['Date de clôture:', intervention.date_cloture.strftime('%d/%m/%Y à %H:%M') if intervention.date_cloture else 'Non clôturée'],
    ]
    
    intervention_table = Table(intervention_data, colWidths=[2*inch, 4*inch])
    intervention_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))
    story.append(intervention_table)
    story.append(Spacer(1, 20))
    
    # Compte rendu
    story.append(Paragraph("Compte rendu:", styles['Heading2']))
    story.append(Paragraph(intervention.compte_rendu or 'Aucun compte rendu disponible.', styles['Normal']))
    story.append(Spacer(1, 20))
    
    # Ressources utilisées
    story.append(Paragraph("Ressources utilisées:", styles['Heading2']))
    story.append(Paragraph(intervention.ressources_utilisees or 'Aucune ressource spécifiée.', styles['Normal']))
    story.append(Spacer(1, 20))
    
    # Pièces jointes
    if pieces_jointes:
        story.append(Paragraph("Pièces jointes:", styles['Heading2']))
        story.append(Spacer(1, 10))
        
        pieces_data = [['Titre', 'Type', 'Description', 'Date d\'ajout']]
        for piece in pieces_jointes:
            pieces_data.append([
                piece.titre,
                piece.get_type_fichier_display(),
                piece.description or 'Aucune description',
                piece.date_ajout.strftime('%d/%m/%Y')
            ])
        
        pieces_table = Table(pieces_data, colWidths=[1.5*inch, 1*inch, 2*inch, 1*inch])
        pieces_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightblue),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]))
        story.append(pieces_table)
    else:
        story.append(Paragraph("Aucune pièce jointe disponible.", styles['Normal']))
    
    # Générer le PDF
    doc.build(story)
    
    # Préparer la réponse
    pdf = buffer.getvalue()
    buffer.close()
    
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="rapport_intervention_{intervention.id}.pdf"'
    response.write(pdf)
    return response 

@login_required
def notification_list(request):
    """Vue pour afficher la liste des notifications de l'utilisateur"""
    notifications = request.user.notifications.all().order_by('-date_creation')
    
    # Marquer toutes les notifications comme lues
    unread_notifications = notifications.filter(lue=False)
    unread_notifications.update(lue=True)
    
    context = {
        'notifications': notifications,
        'user': request.user,
    }
    return render(request, 'core/notification_list.html', context)

@login_required
def notification_mark_read(request, notification_id):
    """Vue pour marquer une notification comme lue"""
    notification = get_object_or_404(Notification, id=notification_id, utilisateur=request.user)
    notification.lue = True
    notification.save()
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'success': True})
    
    return redirect('notification_list')

@login_required
def notification_mark_all_read(request):
    """Vue pour marquer toutes les notifications comme lues"""
    request.user.notifications.filter(lue=False).update(lue=True)
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'success': True})
    
    return redirect('notification_list')

@login_required
def notification_delete(request, notification_id):
    """Vue pour supprimer une notification"""
    notification = get_object_or_404(Notification, id=notification_id, utilisateur=request.user)
    notification.delete()
    
    messages.success(request, 'Notification supprimée avec succès.')
    return redirect('notification_list')

def create_notification(utilisateur, message, type_notification):
    """Fonction utilitaire pour créer une notification"""
    Notification.objects.create(
        utilisateur=utilisateur,
        message=message,
        type_notification=type_notification
    )



def get_unread_notifications_count(request):
    """Fonction pour obtenir le nombre de notifications non lues"""
    if request.user.is_authenticated:
        return request.user.notifications.filter(lue=False).count()
    return 0 

@login_required
def search(request):
    """Vue pour la recherche globale"""
    query = request.GET.get('q', '')
    results = {
        'missions': [],
        'interventions': [],
        'clients': []
    }
    
    if query:
        # Recherche dans les missions
        results['missions'] = Mission.objects.filter(
            models.Q(titre__icontains=query) |
            models.Q(description__icontains=query) |
            models.Q(nature__icontains=query) |
            models.Q(client__nom__icontains=query)
        )[:10]
        
        # Recherche dans les interventions
        results['interventions'] = Intervention.objects.filter(
            models.Q(titre__icontains=query) |
            models.Q(compte_rendu__icontains=query) |
            models.Q(mission__titre__icontains=query) |
            models.Q(mission__client__nom__icontains=query)
        )[:10]
        
        # Recherche dans les clients
        results['clients'] = Client.objects.filter(
            models.Q(nom__icontains=query) |
            models.Q(contact__icontains=query) |
            models.Q(email__icontains=query)
        )[:10]
    
    context = {
        'query': query,
        'results': results,
        'user': request.user,
    }
    return render(request, 'core/search_results.html', context) 

@admin_required
def user_list(request):
    utilisateurs = Utilisateur.objects.all().order_by('-date_joined')
    context = {
        'utilisateurs': utilisateurs,
        'user': request.user,
    }
    return render(request, 'core/user_list.html', context)

@admin_required
def user_create(request):
    if request.method == 'POST':
        form = UtilisateurCreationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Utilisateur créé avec succès.")
            return redirect('user_list')
    else:
        form = UtilisateurCreationForm()
    return render(request, 'core/user_form.html', {'form': form}) 

@login_required
def profil_utilisateur(request):
    user = request.user
    # Suppression de la photo si demandé
    if request.method == 'POST' and 'supprimer_photo' in request.POST:
        user.photo.delete(save=True)
        messages.success(request, 'Photo de profil supprimée.')
        return redirect('profil_utilisateur')
    if request.method == 'POST' and 'modifier_profil' in request.POST:
        form = UtilisateurProfilForm(request.POST, request.FILES, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profil mis à jour avec succès.')
            return redirect('profil_utilisateur')
    else:
        form = UtilisateurProfilForm(instance=user)
    return render(request, 'core/profil_utilisateur.html', {'form': form, 'user': user}) 

@login_required
def intervention_compte_rendu(request, intervention_id):
    intervention = get_object_or_404(Intervention, id=intervention_id)
    # Seul l'intervenant assigné peut accéder à ce formulaire
    if request.user != intervention.intervenant:
        messages.error(request, "Vous n'êtes pas autorisé à remplir ce compte rendu.")
        return redirect('intervention_detail', intervention_id=intervention.id)
    # La mission doit être terminée
    if intervention.mission.statut != 'terminee':
        messages.warning(request, "Vous ne pouvez remplir le compte rendu que lorsque la mission est terminée.")
        return redirect('intervention_detail', intervention_id=intervention.id)
    if request.method == 'POST':
        form = InterventionCompteRenduForm(request.POST, instance=intervention)
        if form.is_valid():
            form.save()
            # Notification au chef de projet ou à l'admin
            chef = intervention.mission.assigne_a or Utilisateur.objects.filter(role='administrateur').first()
            if chef:
                from .views import create_notification
                create_notification(
                    chef,
                    f"Compte rendu soumis pour l'intervention '{intervention.titre}'",
                    "compte_rendu_intervention"
                )
            messages.success(request, "Compte rendu soumis avec succès.")
            return redirect('intervention_detail', intervention_id=intervention.id)
    else:
        form = InterventionCompteRenduForm(instance=intervention)
    return render(request, 'core/intervention_compte_rendu.html', {'form': form, 'intervention': intervention, 'user': request.user}) 

@login_required
def commencer_intervention(request, intervention_id):
    """Vue pour passer une intervention à 'en cours' et enregistrer la date et l'heure de début"""
    intervention = get_object_or_404(Intervention, id=intervention_id)
    if request.user != intervention.intervenant:
        messages.error(request, "Vous n'êtes pas autorisé à commencer cette intervention.")
        return redirect('intervention_list')
    if intervention.statut != 'en_attente':
        messages.warning(request, "L'intervention n'est pas en attente.")
        return redirect('intervention_list')
    intervention.statut = 'en_cours'
    intervention.date_debut = timezone.now()
    intervention.save()
    # Si la mission est en attente, la passer à en cours
    if intervention.mission.statut == 'en_attente':
        intervention.mission.statut = 'en_cours'
        intervention.mission.save()
    messages.success(request, "Intervention commencée. Date et heure de début enregistrées.")
    return redirect('intervention_list') 

@login_required
def terminer_intervention(request, intervention_id):
    """Vue pour passer une intervention à 'terminée' et enregistrer la date et l'heure de fin"""
    intervention = get_object_or_404(Intervention, id=intervention_id)
    if request.user != intervention.intervenant:
        messages.error(request, "Vous n'êtes pas autorisé à terminer cette intervention.")
        return redirect('intervention_list')
    if intervention.statut != 'en_cours':
        messages.warning(request, "L'intervention n'est pas en cours.")
        return redirect('intervention_list')
    intervention.statut = 'terminee'
    intervention.date_fin = timezone.now()
    intervention.save()
    messages.success(request, "Intervention terminée. Date et heure de fin enregistrées.")
    return redirect('intervention_list') 

def mask_email(email):
    """Masque partiellement une adresse email pour la confidentialité."""
    if not email or '@' not in email:
        return email
    name, domain = email.split('@', 1)
    if len(name) <= 2:
        masked_name = name[0] + '*' * (len(name)-1)
    else:
        masked_name = name[0] + '*' * (len(name)-2) + name[-1]
    return f"{masked_name}@{domain}"


def password_reset_by_username(request):
    email = None
    masked_email = None
    username = ''
    email_found = False
    code_sent = False
    code_verified = False
    show_password_form = False
    error_message = ''

    if request.method == 'POST':
        form = PasswordResetByUsernameForm(request.POST)
        username = request.POST.get('username', '')
        # 1. Envoi du code
        if 'send_code' in request.POST:
            try:
                user = Utilisateur.objects.get(username=username)
                email = user.email
                masked_email = mask_email(email)
                email_found = True
                # Générer un code à 6 chiffres
                code = str(random.randint(100000, 999999))
                request.session['reset_code'] = code
                request.session['reset_username'] = username
                # Envoyer le code par email
                send_mail(
                    "Code de réinitialisation de votre mot de passe",
                    f"Votre code de réinitialisation est : {code}",
                    settings.DEFAULT_FROM_EMAIL,
                    [user.email],
                )
                code_sent = True
            except Utilisateur.DoesNotExist:
                form.add_error('username', "Aucun utilisateur avec ce nom d'utilisateur.")
        # 2. Vérification du code
        elif 'verify_code' in request.POST:
            code_sent = True
            username = request.session.get('reset_username')
            code_input = request.POST.get('code', '')
            if code_input == request.session.get('reset_code'):
                code_verified = True
                show_password_form = True
            else:
                error_message = "Code incorrect. Veuillez réessayer."
        # 3. Changement du mot de passe
        elif 'set_password' in request.POST:
            show_password_form = True
            username = request.session.get('reset_username')
            password1 = request.POST.get('password1')
            password2 = request.POST.get('password2')
            if password1 and password2 and password1 == password2:
                try:
                    user = Utilisateur.objects.get(username=username)
                    user.set_password(password1)
                    user.save()
                    # Nettoyer la session
                    request.session.pop('reset_code', None)
                    request.session.pop('reset_username', None)
                    return redirect('connexion')
                except Utilisateur.DoesNotExist:
                    error_message = "Utilisateur introuvable."
            else:
                error_message = "Les mots de passe ne correspondent pas."
        else:
            # Recherche de l'email
            try:
                user = Utilisateur.objects.get(username=username)
                email = user.email
                masked_email = mask_email(email)
                email_found = True
            except Utilisateur.DoesNotExist:
                form.add_error('username', "Aucun utilisateur avec ce nom d'utilisateur.")
    else:
        form = PasswordResetByUsernameForm()
    return render(request, 'core/password_reset_by_username.html', {
        'form': form,
        'email': email,
        'masked_email': masked_email,
        'username': username,
        'email_found': email_found,
        'code_sent': code_sent,
        'code_verified': code_verified,
        'show_password_form': show_password_form,
        'error_message': error_message,
    })


class ForgotPasswordView(View):
    """
    Vue pour gérer le flux complet de réinitialisation de mot de passe
    """
    template_name = 'core/forgot_password.html'
    
    def get(self, request):
        """Affiche le formulaire initial de saisie du nom d'utilisateur"""
        return render(request, self.template_name, {
            'step': 'username',
            'show_back_link': True,
        })
    
    def post(self, request):
        """Gère les différentes étapes du processus de réinitialisation"""
        step = request.POST.get('step', 'username')
        
        if step == 'username':
            return self.handle_username_step(request)
        elif step == 'confirm_email':
            return self.handle_confirm_email_step(request)
        elif step == 'verify_code':
            return self.handle_verify_code_step(request)
        elif step == 'new_password':
            return self.handle_new_password_step(request)
        else:
            return self.get(request)
    
    def handle_username_step(self, request):
        """Étape 1: Saisie du nom d'utilisateur"""
        username = request.POST.get('username', '').strip()
        
        if not username:
            messages.error(request, "Veuillez saisir un nom d'utilisateur.")
            return render(request, self.template_name, {
                'step': 'username',
                'username': username,
                'show_back_link': True,
            })
        
        try:
            user = Utilisateur.objects.get(username=username)
            email = user.email
            masked_email = mask_email(email)
            
            # Stocker les informations en session
            request.session['reset_username'] = username
            request.session['reset_email'] = email
            request.session['reset_masked_email'] = masked_email
            
            return render(request, self.template_name, {
                'step': 'confirm_email',
                'username': username,
                'email': email,
                'masked_email': masked_email,
                'show_back_link': True,
            })
            
        except Utilisateur.DoesNotExist:
            messages.error(request, "Aucun utilisateur trouvé avec ce nom d'utilisateur.")
            return render(request, self.template_name, {
                'step': 'username',
                'username': username,
                'show_back_link': True,
            })
    
    def handle_confirm_email_step(self, request):
        """Étape 2: Confirmation de l'email et envoi du code"""
        username = request.session.get('reset_username')
        email = request.session.get('reset_email')
        masked_email = request.session.get('reset_masked_email')
        
        if not all([username, email]):
            messages.error(request, "Session expirée. Veuillez recommencer.")
            return redirect('forgot_password')
        
        # Générer un code à 6 chiffres
        code = str(random.randint(100000, 999999))
        
        # Stocker le code et l'heure d'envoi en session
        request.session['reset_code'] = code
        request.session['reset_code_sent_at'] = timezone.now().isoformat()
        
        # Envoyer le code par email
        try:
            send_mail(
                "Code de réinitialisation de votre mot de passe",
                f"""Bonjour {username},

Vous avez demandé la réinitialisation de votre mot de passe.

Votre code de réinitialisation est : {code}

Ce code expirera dans 15 minutes.

Si vous n'avez pas demandé cette réinitialisation, ignorez cet email.

Cordialement,
L'équipe Mission Manager""",
                settings.DEFAULT_FROM_EMAIL,
                [email],
                fail_silently=False,
            )
            
            messages.success(request, f"Un code de réinitialisation a été envoyé à {masked_email}")
            
            return render(request, self.template_name, {
                'step': 'verify_code',
                'username': username,
                'masked_email': masked_email,
                'show_back_link': True,
            })
            
        except Exception as e:
            messages.error(request, "Erreur lors de l'envoi du code. Veuillez réessayer.")
            return render(request, self.template_name, {
                'step': 'confirm_email',
                'username': username,
                'email': email,
                'masked_email': masked_email,
                'show_back_link': True,
            })
    
    def handle_verify_code_step(self, request):
        """Étape 3: Vérification du code"""
        username = request.session.get('reset_username')
        masked_email = request.session.get('reset_masked_email')
        stored_code = request.session.get('reset_code')
        code_sent_at = request.session.get('reset_code_sent_at')
        
        if not all([username, stored_code, code_sent_at]):
            messages.error(request, "Session expirée. Veuillez recommencer.")
            return redirect('forgot_password')
        
        # Vérifier l'expiration du code (15 minutes)
        sent_time = datetime.fromisoformat(code_sent_at)
        if timezone.now() - sent_time > timedelta(minutes=15):
            messages.error(request, "Le code a expiré. Veuillez demander un nouveau code.")
            # Nettoyer la session
            for key in ['reset_code', 'reset_code_sent_at']:
                request.session.pop(key, None)
            return render(request, self.template_name, {
                'step': 'confirm_email',
                'username': username,
                'masked_email': masked_email,
                'show_back_link': True,
            })
        
        code_input = request.POST.get('code', '').strip()
        
        if not code_input:
            messages.error(request, "Veuillez saisir le code reçu.")
            return render(request, self.template_name, {
                'step': 'verify_code',
                'username': username,
                'masked_email': masked_email,
                'show_back_link': True,
            })
        
        if code_input == stored_code:
            # Code correct, passer à l'étape du nouveau mot de passe
            request.session['code_verified'] = True
            return render(request, self.template_name, {
                'step': 'new_password',
                'username': username,
                'show_back_link': True,
            })
        else:
            messages.error(request, "Code incorrect. Veuillez réessayer.")
            return render(request, self.template_name, {
                'step': 'verify_code',
                'username': username,
                'masked_email': masked_email,
                'show_back_link': True,
            })
    
    def handle_new_password_step(self, request):
        """Étape 4: Saisie du nouveau mot de passe"""
        username = request.session.get('reset_username')
        code_verified = request.session.get('code_verified')
        
        if not username or not code_verified:
            messages.error(request, "Session expirée. Veuillez recommencer.")
            return redirect('forgot_password')
        
        password1 = request.POST.get('password1', '').strip()
        password2 = request.POST.get('password2', '').strip()
        
        if not password1 or not password2:
            messages.error(request, "Veuillez saisir et confirmer votre nouveau mot de passe.")
            return render(request, self.template_name, {
                'step': 'new_password',
                'username': username,
                'show_back_link': True,
            })
        
        if password1 != password2:
            messages.error(request, "Les mots de passe ne correspondent pas.")
            return render(request, self.template_name, {
                'step': 'new_password',
                'username': username,
                'show_back_link': True,
            })
        
        if len(password1) < 8:
            messages.error(request, "Le mot de passe doit contenir au moins 8 caractères.")
            return render(request, self.template_name, {
                'step': 'new_password',
                'username': username,
                'show_back_link': True,
            })
        
        # Mettre à jour le mot de passe
        try:
            user = Utilisateur.objects.get(username=username)
            user.set_password(password1)
            user.save()
            
            # Nettoyer la session
            for key in ['reset_username', 'reset_email', 'reset_masked_email', 
                       'reset_code', 'reset_code_sent_at', 'code_verified']:
                request.session.pop(key, None)
            
            messages.success(request, "Votre mot de passe a été réinitialisé avec succès. Vous pouvez maintenant vous connecter.")
            return redirect('connexion')
            
        except Utilisateur.DoesNotExist:
            messages.error(request, "Utilisateur introuvable.")
            return redirect('forgot_password') 

@login_required
def retard_list(request):
    """Liste des retards d'intervention"""
    user = request.user
    
    if is_admin(user):
        # Administrateur voit tous les retards
        retards = RetardIntervention.objects.all().order_by('-date_creation')
    else:
        # Employé/freelance ne voit que ses retards
        retards = RetardIntervention.objects.filter(responsable=user).order_by('-date_creation')
    
    context = {
        'retards': retards,
        'user': request.user,
    }
    return render(request, 'core/retard_list.html', context)

@login_required
def retard_create(request, intervention_id):
    """Créer un nouveau retard pour une intervention"""
    intervention = get_object_or_404(Intervention, id=intervention_id)
    
    # Vérifier les permissions
    if not can_view_intervention(request.user, intervention):
        messages.error(request, "Vous n'avez pas les permissions pour cette intervention.")
        return redirect('intervention_list')
    
    if request.method == 'POST':
        form = RetardInterventionForm(request.POST)
        if form.is_valid():
            retard = form.save(commit=False)
            retard.intervention = intervention
            retard.responsable = request.user
            retard.save()
            
            # Marquer l'intervention comme en retard
            intervention.en_retard = True
            intervention.date_retard = timezone.now()
            intervention.save()
            
            # Créer une notification pour les administrateurs
            if is_admin(request.user):
                create_notification(
                    request.user,
                    f"Nouveau retard signalé pour l'intervention: {intervention.titre}",
                    "retard"
                )
            
            messages.success(request, 'Retard enregistré avec succès !')
            return redirect('intervention_detail', intervention_id=intervention_id)
    else:
        form = RetardInterventionForm(initial={'date_debut_retard': timezone.now()})
    
    context = {
        'form': form,
        'intervention': intervention,
        'user': request.user,
    }
    return render(request, 'core/retard_form.html', context)

@login_required
def retard_detail(request, retard_id):
    """Détails d'un retard"""
    retard = get_object_or_404(RetardIntervention, id=retard_id)
    
    # Vérifier les permissions
    if not is_admin(request.user) and retard.responsable != request.user:
        messages.error(request, "Vous n'avez pas les permissions pour voir ce retard.")
        return redirect('retard_list')
    
    context = {
        'retard': retard,
        'user': request.user,
    }
    return render(request, 'core/retard_detail.html', context)

@login_required
def retard_edit(request, retard_id):
    """Modifier un retard"""
    retard = get_object_or_404(RetardIntervention, id=retard_id)
    
    # Vérifier les permissions
    if not is_admin(request.user) and retard.responsable != request.user:
        messages.error(request, "Vous n'avez pas les permissions pour modifier ce retard.")
        return redirect('retard_list')
    
    if request.method == 'POST':
        form = RetardInterventionForm(request.POST, instance=retard)
        if form.is_valid():
            form.save()
            messages.success(request, 'Retard modifié avec succès !')
            return redirect('retard_detail', retard_id=retard_id)
    else:
        form = RetardInterventionForm(instance=retard)
    
    context = {
        'form': form,
        'retard': retard,
        'user': request.user,
    }
    return render(request, 'core/retard_form.html', context)

@login_required
def retard_resolve(request, retard_id):
    """Résoudre un retard"""
    retard = get_object_or_404(RetardIntervention, id=retard_id)
    
    # Vérifier les permissions
    if not is_admin(request.user) and retard.responsable != request.user:
        messages.error(request, "Vous n'avez pas les permissions pour résoudre ce retard.")
        return redirect('retard_list')
    
    if request.method == 'POST':
        form = RetardResolutionForm(request.POST, instance=retard)
        if form.is_valid():
            retard = form.save(commit=False)
            if retard.resolu:
                retard.date_fin_retard = timezone.now()
                retard.duree_retard = retard.calculer_duree()
                
                # Marquer l'intervention comme retard résolu
                intervention = retard.intervention
                intervention.retard_resolu = True
                intervention.save()
            
            retard.save()
            messages.success(request, 'Retard résolu avec succès !')
            return redirect('retard_detail', retard_id=retard_id)
    else:
        form = RetardResolutionForm(instance=retard)
    
    context = {
        'form': form,
        'retard': retard,
        'user': request.user,
    }
    return render(request, 'core/retard_resolution_form.html', context)

@login_required
def intervention_retard_manage(request, intervention_id):
    """Gérer les retards d'une intervention"""
    intervention = get_object_or_404(Intervention, id=intervention_id)
    
    # Vérifier les permissions
    if not can_view_intervention(request.user, intervention):
        messages.error(request, "Vous n'avez pas les permissions pour cette intervention.")
        return redirect('intervention_list')
    
    if request.method == 'POST':
        form = InterventionRetardForm(request.POST, instance=intervention)
        if form.is_valid():
            intervention = form.save()
            if intervention.retard_resolu:
                intervention.en_retard = False
                intervention.save()
            messages.success(request, 'Gestion du retard mise à jour !')
            return redirect('intervention_detail', intervention_id=intervention_id)
    else:
        form = InterventionRetardForm(instance=intervention)
    
    context = {
        'form': form,
        'intervention': intervention,
        'user': request.user,
    }
    return render(request, 'core/intervention_retard_form.html', context)

@login_required
def dashboard_retards(request):
    """Dashboard des retards"""
    user = request.user
    
    if is_admin(user):
        # Statistiques pour administrateur
        total_retards = RetardIntervention.objects.count()
        retards_en_cours = RetardIntervention.objects.filter(resolu=False).count()
        retards_resolus = RetardIntervention.objects.filter(resolu=True).count()
        interventions_en_retard = Intervention.objects.filter(en_retard=True, retard_resolu=False).count()
    else:
        # Statistiques pour employé/freelance
        total_retards = RetardIntervention.objects.filter(responsable=user).count()
        retards_en_cours = RetardIntervention.objects.filter(responsable=user, resolu=False).count()
        retards_resolus = RetardIntervention.objects.filter(responsable=user, resolu=True).count()
        interventions_en_retard = Intervention.objects.filter(
            intervenant=user, en_retard=True, retard_resolu=False
        ).count()
    
    # Retards récents
    if is_admin(user):
        retards_recents = RetardIntervention.objects.all().order_by('-date_creation')[:5]
    else:
        retards_recents = RetardIntervention.objects.filter(responsable=user).order_by('-date_creation')[:5]
    
    context = {
        'total_retards': total_retards,
        'retards_en_cours': retards_en_cours,
        'retards_resolus': retards_resolus,
        'interventions_en_retard': interventions_en_retard,
        'retards_recents': retards_recents,
        'user': request.user,
    }
    return render(request, 'core/dashboard_retards.html', context) 

@admin_required
def check_retards_automatiques(request):
    """Vérifie manuellement les interventions en retard (pour les administrateurs)"""
    if request.method == 'POST':
        interventions_traitees = []
        
        # Récupérer toutes les interventions non terminées avec échéance dépassée
        interventions = Intervention.objects.filter(
            statut__in=['en_attente', 'en_cours'],
            date_echeance__lt=timezone.now().date(),
            en_retard=False
        )
        
        for intervention in interventions:
            # Utiliser la méthode du modèle
            if intervention.verifier_retard():
                interventions_traitees.append(intervention)
        
        messages.success(
            request, 
            f'{len(interventions_traitees)} intervention(s) marquée(s) comme en retard automatiquement.'
        )
        return redirect('retard_list')
    
    # Afficher les interventions qui seraient marquées comme en retard
    interventions_en_retard = Intervention.objects.filter(
        statut__in=['en_attente', 'en_cours'],
        date_echeance__lt=timezone.now().date(),
        en_retard=False
    )
    
    context = {
        'interventions_en_retard': interventions_en_retard,
        'user': request.user,
    }
    return render(request, 'core/check_retards.html', context) 