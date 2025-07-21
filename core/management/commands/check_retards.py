from django.core.management.base import BaseCommand
from django.utils import timezone
from core.models import Intervention, RetardIntervention, Notification
from datetime import date

class Command(BaseCommand):
    help = 'Vérifie automatiquement les interventions en retard et crée des notifications'

    def handle(self, *args, **options):
        today = date.today()
        interventions_en_retard = []
        
        # Récupérer toutes les interventions non terminées avec échéance dépassée
        interventions = Intervention.objects.filter(
            statut__in=['en_attente', 'en_cours'],
            date_echeance__lt=today,
            en_retard=False  # Pas encore marquées comme en retard
        )
        
        for intervention in interventions:
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
            
            # Pour les administrateurs
            from core.models import Utilisateur
            admins = Utilisateur.objects.filter(role='administrateur')
            for admin in admins:
                Notification.objects.create(
                    utilisateur=admin,
                    message=f"Intervention en retard automatique : {intervention.titre} (Intervenant: {intervention.intervenant})",
                    type_notification="retard_automatique_admin"
                )
            
            interventions_en_retard.append(intervention)
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Vérification terminée. {len(interventions_en_retard)} intervention(s) marquée(s) comme en retard.'
            )
        )
        
        if interventions_en_retard:
            self.stdout.write("Interventions en retard détectées :")
            for intervention in interventions_en_retard:
                self.stdout.write(f"- {intervention.titre} (Échéance: {intervention.date_echeance})") 