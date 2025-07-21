#!/usr/bin/env python
"""
Script pour vérifier automatiquement les interventions en retard
À exécuter quotidiennement via cron ou task scheduler
"""

import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mission_manager.settings')
django.setup()

from django.utils import timezone
from core.models import Intervention, RetardIntervention, Notification, Utilisateur
from datetime import date

def check_retards_quotidien():
    """Vérifie les interventions en retard et crée des notifications"""
    today = date.today()
    interventions_en_retard = []
    
    print(f"Vérification des retards pour le {today.strftime('%d/%m/%Y')}")
    
    # Récupérer toutes les interventions non terminées avec échéance dépassée
    interventions = Intervention.objects.filter(
        statut__in=['en_attente', 'en_cours'],
        date_echeance__lt=today,
        en_retard=False  # Pas encore marquées comme en retard
    )
    
    print(f"Trouvé {interventions.count()} intervention(s) en retard")
    
    for intervention in interventions:
        print(f"Traitement de l'intervention: {intervention.titre}")
        
        # Marquer l'intervention comme en retard
        intervention.en_retard = True
        intervention.date_retard = timezone.now()
        intervention.save()
        
        # Créer un retard automatique
        retard = RetardIntervention.objects.create(
            intervention=intervention,
            type_retard='fin',  # Retard à la fin
            date_debut_retard=timezone.now(),
            motif=f"Intervention non effectuée à la date d'échéance ({intervention.date_echeance.strftime('%d/%m/%Y')})",
            impact="Impact sur le planning et la satisfaction client",
            actions_correctives="Contacter l'intervenant pour reprogrammer",
            responsable=intervention.intervenant
        )
        
        # Créer des notifications
        # Pour l'intervenant
        if intervention.intervenant:
            Notification.objects.create(
                utilisateur=intervention.intervenant,
                message=f"Votre intervention '{intervention.titre}' est en retard depuis le {intervention.date_echeance.strftime('%d/%m/%Y')}",
                type_notification="retard_automatique"
            )
            print(f"Notification créée pour {intervention.intervenant}")
        
        # Pour les administrateurs
        admins = Utilisateur.objects.filter(role='administrateur')
        for admin in admins:
            Notification.objects.create(
                utilisateur=admin,
                message=f"Intervention en retard automatique : {intervention.titre} (Intervenant: {intervention.intervenant})",
                type_notification="retard_automatique_admin"
            )
            print(f"Notification créée pour l'admin {admin}")
        
        interventions_en_retard.append(intervention)
    
    print(f"Vérification terminée. {len(interventions_en_retard)} intervention(s) marquée(s) comme en retard.")
    return len(interventions_en_retard)

if __name__ == "__main__":
    count = check_retards_quotidien()
    print(f"Script terminé avec {count} intervention(s) traitée(s)") 