from django.urls import path
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth import views as auth_views
from .views import (
    dashboard, 
    client_list, client_create, client_edit, client_delete,
    mission_list, mission_detail, mission_create, mission_edit, mission_delete,
    intervention_list, intervention_detail, intervention_create, intervention_edit, intervention_delete,
    piece_jointe_create, piece_jointe_delete,
    rapports_dashboard, rapport_mission, generer_pdf_mission,
    rapport_intervention, generer_pdf_intervention,
    rapport_intervention_create, rapport_intervention_edit, rapport_intervention_validate,
    notification_list, notification_mark_read, notification_mark_all_read, notification_delete,
    search, user_list, user_create,
    profil_utilisateur,
    intervention_compte_rendu,
    rapport_intervention_submit,
    commencer_intervention,
    terminer_intervention,
    password_reset_by_username,
    ForgotPasswordView,
    # Nouvelles vues pour les retards
    retard_list, retard_create, retard_detail, retard_edit, retard_resolve,
    intervention_retard_manage, dashboard_retards, check_retards_automatiques
)

urlpatterns = [
    path('connexion/', LoginView.as_view(template_name='core/connexion.html'), name='connexion'),
    path('deconnexion/', LogoutView.as_view(next_page='connexion'), name='logout'),
    path('dashboard/', dashboard, name='dashboard'),
    path('profil/', profil_utilisateur, name='profil_utilisateur'),
    
    # URLs Clients
    path('clients/', client_list, name='client_list'),
    path('clients/creer/', client_create, name='client_create'),
    path('clients/<int:client_id>/modifier/', client_edit, name='client_edit'),
    path('clients/<int:client_id>/supprimer/', client_delete, name='client_delete'),
    
    # URLs Missions
    path('missions/', mission_list, name='mission_list'),
    path('missions/<int:mission_id>/', mission_detail, name='mission_detail'),
    path('missions/creer/', mission_create, name='mission_create'),
    path('missions/<int:mission_id>/modifier/', mission_edit, name='mission_edit'),
    path('missions/<int:mission_id>/supprimer/', mission_delete, name='mission_delete'),
    
    # URLs Interventions
    path('interventions/', intervention_list, name='intervention_list'),
    path('interventions/<int:intervention_id>/', intervention_detail, name='intervention_detail'),
    path('interventions/creer/', intervention_create, name='intervention_create'),
    path('interventions/<int:intervention_id>/modifier/', intervention_edit, name='intervention_edit'),
    path('interventions/<int:intervention_id>/supprimer/', intervention_delete, name='intervention_delete'),
    path('interventions/<int:intervention_id>/compte-rendu/', intervention_compte_rendu, name='intervention_compte_rendu'),
    path('interventions/<int:intervention_id>/commencer/', commencer_intervention, name='commencer_intervention'),
    path('interventions/<int:intervention_id>/terminer/', terminer_intervention, name='terminer_intervention'),
    
    # URLs Pièces jointes
    path('interventions/<int:intervention_id>/pieces-jointes/ajouter/', piece_jointe_create, name='piece_jointe_create'),
    path('pieces-jointes/<int:piece_jointe_id>/supprimer/', piece_jointe_delete, name='piece_jointe_delete'),
    
    # URLs Rapports
    path('rapports/', rapports_dashboard, name='rapports_dashboard'),
    path('missions/<int:mission_id>/rapport/', rapport_mission, name='rapport_mission'),
    path('missions/<int:mission_id>/rapport/pdf/', generer_pdf_mission, name='generer_pdf_mission'),
    path('interventions/<int:intervention_id>/rapport/', rapport_intervention, name='rapport_intervention'),
    path('interventions/<int:intervention_id>/rapport/pdf/', generer_pdf_intervention, name='generer_pdf_intervention'),
    path('interventions/<int:intervention_id>/rapport/creer/', rapport_intervention_create, name='rapport_intervention_create'),
    path('interventions/<int:intervention_id>/rapport/modifier/', rapport_intervention_edit, name='rapport_intervention_edit'),
    path('interventions/<int:intervention_id>/rapport/valider/', rapport_intervention_validate, name='rapport_intervention_validate'),
    path('interventions/<int:intervention_id>/rapport/soumettre/', rapport_intervention_submit, name='rapport_intervention_submit'),
    
    # URLs Retards
    path('retards/', retard_list, name='retard_list'),
    path('retards/dashboard/', dashboard_retards, name='dashboard_retards'),
    path('retards/verifier/', check_retards_automatiques, name='check_retards_automatiques'),
    path('interventions/<int:intervention_id>/retard/creer/', retard_create, name='retard_create'),
    path('retards/<int:retard_id>/', retard_detail, name='retard_detail'),
    path('retards/<int:retard_id>/modifier/', retard_edit, name='retard_edit'),
    path('retards/<int:retard_id>/resoudre/', retard_resolve, name='retard_resolve'),
    path('interventions/<int:intervention_id>/retard/gerer/', intervention_retard_manage, name='intervention_retard_manage'),
    
    # URLs Notifications
    path('notifications/', notification_list, name='notification_list'),
    path('notifications/<int:notification_id>/lire/', notification_mark_read, name='notification_mark_read'),
    path('notifications/tout-lire/', notification_mark_all_read, name='notification_mark_all_read'),
    path('notifications/<int:notification_id>/supprimer/', notification_delete, name='notification_delete'),
    
    # URL Recherche
    path('recherche/', search, name='search'),
]

urlpatterns += [
    path('utilisateurs/', user_list, name='user_list'),
    path('utilisateurs/ajouter/', user_create, name='user_create'),
    path('mot-de-passe-oublie/', password_reset_by_username, name='password_reset_by_username'),
    path('mot-de-passe-oublie-v2/', ForgotPasswordView.as_view(), name='forgot_password'),
]