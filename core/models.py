from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import FileExtensionValidator
from datetime import datetime
from django.utils import timezone

class Utilisateur(AbstractUser):
    ROLE_CHOICES = (
        ('administrateur', 'Administrateur'),
        ('employe', 'Employé'),
        ('freelance', 'Freelance'),
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, verbose_name="Rôle")
    telephone = models.CharField(max_length=20, blank=True, verbose_name="Téléphone")
    photo = models.ImageField(upload_to='photos_profil/', blank=True, null=True, verbose_name="Photo de profil")

    class Meta:
        verbose_name = "Utilisateur"
        verbose_name_plural = "Utilisateurs"
    
    def __str__(self):
        return f"{self.first_name} {self.last_name}" if self.first_name and self.last_name else self.username

class Client(models.Model):
    nom = models.CharField(max_length=255, verbose_name="Nom de l'entreprise")
    contact = models.CharField(max_length=255, verbose_name="Personne à contacter")
    email = models.EmailField(verbose_name="Email")
    telephone = models.CharField(max_length=20, verbose_name="Téléphone")
    adresse = models.TextField(verbose_name="Adresse")

    class Meta:
        verbose_name = "Client"
        verbose_name_plural = "Clients"
    
    def __str__(self):
        return self.nom

class Mission(models.Model):
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='missions', verbose_name="Client")
    titre = models.CharField(max_length=255, verbose_name="Titre de la mission")
    description = models.TextField(verbose_name="Description")
    nature = models.CharField(max_length=255, verbose_name="Nature de la mission")
    date = models.DateField(verbose_name="Date de début")
    lieu = models.CharField(max_length=255, verbose_name="Lieu")
    frequence = models.CharField(max_length=100, blank=True, verbose_name="Fréquence")
    assigne_a = models.ForeignKey(Utilisateur, on_delete=models.SET_NULL, null=True, related_name='missions', verbose_name="Assigné à")
    statut = models.CharField(
        max_length=50,
        choices=[('en_attente', 'En attente'), ('en_cours', 'En cours'), ('terminee', 'Terminée')],
        default='en_attente',
        verbose_name="Statut"
    )
    date_creation = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")

    class Meta:
        verbose_name = "Mission"
        verbose_name_plural = "Missions"
    
    def __str__(self):
        return self.titre

class Intervention(models.Model):
    PRIORITE_CHOICES = [
        ('normale', 'Normale'),
        ('urgente', 'Urgente'),
    ]
    titre = models.CharField(max_length=255, verbose_name="Titre de l'intervention")
    mission = models.ForeignKey(Mission, on_delete=models.CASCADE, related_name='interventions', verbose_name="Mission")
    intervenant = models.ForeignKey(Utilisateur, on_delete=models.SET_NULL, null=True, related_name='interventions', verbose_name="Intervenant")
    date = models.DateField(verbose_name="Date d'intervention")
    date_echeance = models.DateField(verbose_name="Date au plus tard de réalisation")
    priorite = models.CharField(max_length=10, choices=PRIORITE_CHOICES, default='normale', verbose_name="Priorité")
    ressources_utilisees = models.TextField(blank=True, verbose_name="Ressources à utiliser")
    statut = models.CharField(
        max_length=50,
        choices=[('en_attente', 'En attente'), ('en_cours', 'En cours'), ('terminee', 'Terminée')],
        default='en_attente',
        verbose_name="Statut"
    )
    date_creation = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")
    date_cloture = models.DateTimeField(null=True, blank=True, verbose_name="Date de clôture")
    cree_par = models.ForeignKey(Utilisateur, on_delete=models.SET_NULL, null=True, related_name='interventions_creees', verbose_name="Créé par")
    heure_arrivee = models.TimeField(null=True, blank=True, verbose_name="Heure d'arrivée")
    heure_depart = models.TimeField(null=True, blank=True, verbose_name="Heure de départ")
    difficultes = models.TextField(blank=True, verbose_name="Difficultés rencontrées")
    ETAT_CHOICES = [
        ('en_attente', 'En attente'),
        ('en_cours', 'En cours'),
        ('terminee', 'Terminée'),
        ('resolue', 'Résolue'),
        ('non_resolue', 'Non résolue'),
    ]
    etat_intervention = models.CharField(max_length=20, choices=ETAT_CHOICES, default='en_attente', verbose_name="État de l'intervention")
    date_debut = models.DateTimeField(null=True, blank=True, verbose_name="Date et heure de début")
    date_fin = models.DateTimeField(null=True, blank=True, verbose_name="Date et heure de fin")
    
    # Champs pour la gestion des retards
    en_retard = models.BooleanField(default=False, verbose_name="En retard")
    date_retard = models.DateTimeField(null=True, blank=True, verbose_name="Date de début du retard")
    duree_retard = models.DurationField(null=True, blank=True, verbose_name="Durée du retard")
    motif_retard = models.TextField(blank=True, verbose_name="Motif du retard")
    retard_resolu = models.BooleanField(default=False, verbose_name="Retard résolu")

    class Meta:
        verbose_name = "Intervention"
        verbose_name_plural = "Interventions"
    
    def __str__(self):
        return self.titre

    def calculer_duree_travail(self):
        if self.date_debut and self.date_fin:
            duree = self.date_fin - self.date_debut
            jours = duree.days
            heures = duree.seconds // 3600
            minutes = (duree.seconds % 3600) // 60
            if jours:
                return f"{jours}j {heures}h {minutes}min"
            return f"{heures}h {minutes}min"
        return "Non renseigné"
    
    def verifier_retard(self):
        """Vérifie si l'intervention est en retard"""
        if self.date_echeance and self.statut != 'terminee':
            aujourd_hui = timezone.now().date()
            if aujourd_hui > self.date_echeance:
                if not self.en_retard:
                    self.en_retard = True
                    self.date_retard = timezone.now()
                    self.save()
                    
                    # Créer un retard automatique
                    from .models import RetardIntervention, Notification
                    retard = RetardIntervention.objects.create(
                        intervention=self,
                        type_retard='fin',
                        date_debut_retard=timezone.now(),
                        motif=f"Intervention non effectuée à la date d'échéance ({self.date_echeance.strftime('%d/%m/%Y')})",
                        impact="Impact sur le planning et la satisfaction client",
                        actions_correctives="Contacter l'intervenant pour reprogrammer",
                        responsable=self.intervenant
                    )
                    
                    # Créer des notifications
                    if self.intervenant:
                        Notification.objects.create(
                            utilisateur=self.intervenant,
                            message=f"Votre intervention '{self.titre}' est en retard depuis le {self.date_echeance.strftime('%d/%m/%Y')}",
                            type_notification="retard_automatique"
                        )
                    
                    # Notifier les administrateurs
                    admins = Utilisateur.objects.filter(role='administrateur')
                    for admin in admins:
                        Notification.objects.create(
                            utilisateur=admin,
                            message=f"Intervention en retard automatique : {self.titre} (Intervenant: {self.intervenant})",
                            type_notification="retard_automatique_admin"
                        )
                    
                return True
        return False
    
    def calculer_duree_retard(self):
        """Calcule la durée du retard en cours"""
        if self.en_retard and self.date_retard and not self.retard_resolu:
            duree = timezone.now() - self.date_retard
            return duree
        return None

class RetardIntervention(models.Model):
    TYPE_RETARD_CHOICES = [
        ('debut', 'Retard au début'),
        ('fin', 'Retard à la fin'),
        ('duree', 'Dépassement de durée'),
        ('planification', 'Problème de planification'),
        ('technique', 'Problème technique'),
        ('client', 'Problème client'),
        ('autre', 'Autre'),
    ]
    
    intervention = models.ForeignKey(Intervention, on_delete=models.CASCADE, related_name='retards', verbose_name="Intervention")
    type_retard = models.CharField(max_length=20, choices=TYPE_RETARD_CHOICES, verbose_name="Type de retard")
    date_debut_retard = models.DateTimeField(verbose_name="Date de début du retard")
    date_fin_retard = models.DateTimeField(null=True, blank=True, verbose_name="Date de fin du retard")
    duree_retard = models.DurationField(null=True, blank=True, verbose_name="Durée du retard")
    motif = models.TextField(verbose_name="Motif du retard")
    impact = models.TextField(blank=True, verbose_name="Impact sur la mission")
    actions_correctives = models.TextField(blank=True, verbose_name="Actions correctives")
    responsable = models.ForeignKey(Utilisateur, on_delete=models.SET_NULL, null=True, related_name='retards_responsable', verbose_name="Responsable")
    date_creation = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")
    resolu = models.BooleanField(default=False, verbose_name="Résolu")

    class Meta:
        verbose_name = "Retard d'intervention"
        verbose_name_plural = "Retards d'intervention"
    
    def __str__(self):
        return f"Retard - {self.intervention.titre} - {self.get_type_retard_display()}"
    
    def calculer_duree(self):
        """Calcule la durée du retard"""
        if self.date_fin_retard:
            return self.date_fin_retard - self.date_debut_retard
        elif not self.resolu:
            return timezone.now() - self.date_debut_retard
        return None

class PieceJointe(models.Model):
    TYPE_CHOICES = [
        ('photo', 'Photo'),
        ('document', 'Document'),
        ('video', 'Vidéo'),
        ('autre', 'Autre'),
    ]
    intervention = models.ForeignKey(Intervention, on_delete=models.CASCADE, related_name='pieces_jointes', verbose_name="Intervention")
    titre = models.CharField(max_length=255, verbose_name="Titre du fichier")
    fichier = models.FileField(upload_to='pieces_jointes/', verbose_name="Fichier")
    type_fichier = models.CharField(
        max_length=20,
        choices=TYPE_CHOICES,
        default='document',
        verbose_name="Type de fichier"
    )
    description = models.TextField(blank=True, verbose_name="Description")
    date_ajout = models.DateTimeField(auto_now_add=True, verbose_name="Date d'ajout")

    class Meta:
        verbose_name = "Pièce jointe"
        verbose_name_plural = "Pièces jointes"
    
    def __str__(self):
        return self.titre

class Preuve(models.Model):
    intervention = models.ForeignKey(Intervention, on_delete=models.CASCADE, related_name='preuves', verbose_name="Intervention")
    fichier = models.FileField(upload_to='preuves/', verbose_name="Fichier")
    type_preuve = models.CharField(
        max_length=20,
        choices=[('avant', 'Avant'), ('apres', 'Après')],
        verbose_name="Type de preuve"
    )
    date_ajout = models.DateTimeField(auto_now_add=True, verbose_name="Date d'ajout")

    class Meta:
        verbose_name = "Preuve"
        verbose_name_plural = "Preuves"

class Notification(models.Model):
    utilisateur = models.ForeignKey(Utilisateur, on_delete=models.CASCADE, related_name='notifications', verbose_name="Utilisateur")
    message = models.CharField(max_length=255, verbose_name="Message")
    type_notification = models.CharField(max_length=50, verbose_name="Type de notification")
    lue = models.BooleanField(default=False, verbose_name="Lue")
    date_creation = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")

    class Meta:
        verbose_name = "Notification"
        verbose_name_plural = "Notifications"

class RapportIntervention(models.Model):
    STATUT_CHOICES = [
        ('brouillon', 'Brouillon'),
        ('soumis', 'Soumis'),
        ('valide', 'Validé'),
        ('rejete', 'Rejeté'),
    ]
    intervention = models.OneToOneField(Intervention, on_delete=models.CASCADE, related_name='rapport')
    travaux_realises = models.TextField("Travaux réalisés", blank=True)
    resultat_final = models.TextField("Résultat final", blank=True)
    ressources_utilisees = models.TextField("Ressources utilisées", blank=True)
    ameliorations_a_faire = models.TextField("Améliorations à faire", blank=True)
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default="brouillon")
    motif_rejet = models.TextField("Motif du rejet", blank=True)
    commentaire_validation = models.TextField("Commentaire de validation", blank=True)
    valide_par = models.ForeignKey(Utilisateur, on_delete=models.SET_NULL, null=True, related_name='rapports_valides', verbose_name="Validé par")
    rejete_par = models.ForeignKey(Utilisateur, on_delete=models.SET_NULL, null=True, related_name='rapports_rejetes', verbose_name="Rejeté par")
    date_validation = models.DateTimeField(null=True, blank=True, verbose_name="Date de validation")
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Rapport d'intervention #{self.pk}"

    def clean(self):
        from django.core.exceptions import ValidationError
        if self.statut == "rejete" and not self.motif_rejet:
            raise ValidationError({"motif_rejet": "Le motif du rejet est obligatoire si le rapport est rejeté."})

class RapportImage(models.Model):
    TYPE_CHOICES = [
        ("avant", "Avant"),
        ("apres", "Après"),
    ]
    rapport = models.ForeignKey(RapportIntervention, on_delete=models.CASCADE, related_name="images")
    image = models.ImageField(upload_to="rapports/images/", validators=[FileExtensionValidator(["jpg", "jpeg", "png", "gif"])])
    type_image = models.CharField(max_length=10, choices=TYPE_CHOICES)
    description = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return f"Image {self.type_image} #{self.pk}"

class RapportFichierJoint(models.Model):
    rapport = models.ForeignKey(RapportIntervention, on_delete=models.CASCADE, related_name="fichiers_joints")
    fichier = models.FileField(upload_to="rapports/fichiers/", validators=[FileExtensionValidator(["pdf", "doc", "docx", "xls", "xlsx", "jpg", "jpeg", "png"])])
    description = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return f"Fichier joint #{self.pk}" 