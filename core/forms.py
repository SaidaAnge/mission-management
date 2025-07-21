from django import forms
from django.forms import modelformset_factory
from django.contrib.auth.forms import UserCreationForm
from .models import Utilisateur, Mission, Intervention, RapportIntervention, PieceJointe, RetardIntervention
from datetime import date

class UtilisateurCreationForm(UserCreationForm):
    class Meta:
        model = Utilisateur
        fields = ('username', 'email', 'first_name', 'last_name', 'role', 'telephone', 'password1', 'password2')
        labels = {
            'username': "Nom d'utilisateur",
            'email': "Adresse email",
            'first_name': "Prénom",
            'last_name': "Nom",
            'role': "Rôle",
            'telephone': "Téléphone",
            'password1': "Mot de passe",
            'password2': "Confirmer le mot de passe",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'

class MissionForm(forms.ModelForm):
    class Meta:
        model = Mission
        fields = ['client', 'titre', 'description', 'nature', 'date', 'lieu', 'frequence', 'assigne_a', 'statut']
        widgets = {
            'date': forms.DateInput(attrs={
                'class': 'form-input',
                'type': 'date',
                'min': date.today().isoformat(),
                'placeholder': 'Date de début'
            }),
        }
        labels = {
            'client': 'Client',
            'titre': 'Titre de la mission',
            'description': 'Description',
            'nature': 'Nature de la mission',
            'date': 'Date de début',
            'lieu': 'Lieu',
            'frequence': 'Fréquence',
            'assigne_a': 'Assigné à',
            'statut': 'Statut',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['date'].widget.attrs['min'] = date.today().isoformat()
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'

class InterventionForm(forms.ModelForm):
    class Meta:
        model = Intervention
        fields = [
            'titre', 'mission', 'intervenant', 'date', 'date_echeance', 'priorite',
            'ressources_utilisees', 'statut'
        ]
        widgets = {
            'titre': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Titre de l\'intervention'
            }),
            'mission': forms.Select(attrs={
                'class': 'form-select',
                'placeholder': 'Sélectionnez une mission'
            }),
            'intervenant': forms.Select(attrs={
                'class': 'form-select',
                'placeholder': 'Sélectionnez un intervenant'
            }),
            'date': forms.DateInput(attrs={
                'class': 'form-input',
                'type': 'date',
                'min': date.today().isoformat(),
                'placeholder': 'Date d\'intervention'
            }),
            'date_echeance': forms.DateInput(attrs={
                'class': 'form-input',
                'type': 'date',
                'min': date.today().isoformat(),
                'placeholder': 'Date au plus tard'
            }),
            'priorite': forms.Select(attrs={
                'class': 'form-select',
            }),
            'ressources_utilisees': forms.Textarea(attrs={
                'class': 'form-textarea',
                'placeholder': 'Ressources à utiliser',
                'rows': 3
            }),
            'statut': forms.Select(attrs={
                'class': 'form-select',
                'placeholder': 'Statut'
            }),
        }
        labels = {
            'titre': 'Titre de l\'intervention',
            'mission': 'Mission associée',
            'intervenant': 'Intervenant',
            'date': 'Date d\'intervention',
            'date_echeance': 'Date au plus tard',
            'priorite': 'Priorité',
            'ressources_utilisees': 'Ressources à utiliser',
            'statut': 'Statut',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['date'].widget.attrs['min'] = date.today().isoformat()
        self.fields['date_echeance'].widget.attrs['min'] = date.today().isoformat()
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'

class PieceJointeForm(forms.ModelForm):
    class Meta:
        model = PieceJointe
        fields = ['titre', 'fichier', 'type_fichier', 'description']
        widgets = {
            'titre': forms.TextInput(attrs={'class': 'form-control'}),
            'fichier': forms.FileInput(attrs={'class': 'form-control'}),
            'type_fichier': forms.Select(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

class RapportInterventionForm(forms.ModelForm):
    class Meta:
        model = RapportIntervention
        fields = [
            'travaux_realises',
            'resultat_final',
            'ressources_utilisees',
            'ameliorations_a_faire',
        ]
        widgets = {
            'travaux_realises': forms.Textarea(attrs={'class': 'form-control', 'rows': 5, 'placeholder': "Travaux réalisés"}),
            'resultat_final': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': "Résultat final"}),
            'ressources_utilisees': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': "Ressources utilisées"}),
            'ameliorations_a_faire': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': "Améliorations à faire"}),
        }
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Le champ motif_rejet n'est pas inclus dans ce formulaire par défaut. S'il doit être géré, il faut l'ajouter explicitement dans les fields.

class UtilisateurProfilForm(forms.ModelForm):
    class Meta:
        model = Utilisateur
        fields = ('username', 'email', 'first_name', 'last_name', 'telephone', 'photo')
        labels = {
            'username': "Nom d'utilisateur",
            'email': "Adresse email",
            'first_name': "Prénom",
            'last_name': "Nom",
            'telephone': "Téléphone",
            'photo': "Photo de profil",
        }
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control' 

class InterventionCompteRenduForm(forms.ModelForm):
    class Meta:
        model = Intervention
        fields = ['heure_arrivee', 'heure_depart', 'ressources_utilisees', 'difficultes', 'etat_intervention']
        labels = {
            'heure_arrivee': "Heure d'arrivée",
            'heure_depart': "Heure de départ",
            'ressources_utilisees': "Ressources utilisées",
            'difficultes': "Difficultés rencontrées",
            'etat_intervention': "État de l'intervention",
        }
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control' 

# Formset pour les pièces jointes
PieceJointeFormSet = modelformset_factory(
    PieceJointe,
    form=PieceJointeForm,
    extra=1,
    can_delete=True
)

class RapportValidationForm(forms.Form):
    ACTION_CHOICES = [
        ('valider', 'Valider'),
        ('rejeter', 'Rejeter'),
    ]
    
    action = forms.ChoiceField(
        choices=ACTION_CHOICES,
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'}),
        label="Action à effectuer"
    )
    
    commentaire_validation = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Commentaire de validation (facultatif)'
        }),
        required=False,
        label="Commentaire de validation"
    )
    
    motif_rejet = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Motif du rejet (obligatoire)'
        }),
        required=False,
        label="Motif du rejet"
    )
    
    def clean(self):
        cleaned_data = super().clean()
        action = cleaned_data.get('action')
        motif_rejet = cleaned_data.get('motif_rejet')
        commentaire_validation = cleaned_data.get('commentaire_validation')
        
        if action == 'rejeter' and not motif_rejet:
            raise forms.ValidationError("Le motif du rejet est obligatoire.")
        
        return cleaned_data 

class PasswordResetByUsernameForm(forms.Form):
    username = forms.CharField(label="Nom d'utilisateur", max_length=150) 

class RetardInterventionForm(forms.ModelForm):
    class Meta:
        model = RetardIntervention
        fields = [
            'type_retard', 'date_debut_retard', 'motif', 'impact', 
            'actions_correctives', 'responsable'
        ]
        widgets = {
            'type_retard': forms.Select(attrs={
                'class': 'form-select',
                'placeholder': 'Type de retard'
            }),
            'date_debut_retard': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local',
                'placeholder': 'Date et heure de début du retard'
            }),
            'motif': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Décrivez le motif du retard...'
            }),
            'impact': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Impact sur la mission (facultatif)'
            }),
            'actions_correctives': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Actions correctives prévues (facultatif)'
            }),
            'responsable': forms.Select(attrs={
                'class': 'form-select',
                'placeholder': 'Responsable du retard'
            }),
        }
        labels = {
            'type_retard': 'Type de retard',
            'date_debut_retard': 'Date de début du retard',
            'motif': 'Motif du retard',
            'impact': 'Impact sur la mission',
            'actions_correctives': 'Actions correctives',
            'responsable': 'Responsable',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'

class RetardResolutionForm(forms.ModelForm):
    class Meta:
        model = RetardIntervention
        fields = ['date_fin_retard', 'resolu']
        widgets = {
            'date_fin_retard': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local',
                'placeholder': 'Date et heure de fin du retard'
            }),
            'resolu': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }
        labels = {
            'date_fin_retard': 'Date de fin du retard',
            'resolu': 'Marquer comme résolu',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            if not isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs['class'] = 'form-control'

class InterventionRetardForm(forms.ModelForm):
    class Meta:
        model = Intervention
        fields = ['motif_retard', 'retard_resolu']
        widgets = {
            'motif_retard': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Décrivez le motif du retard...'
            }),
            'retard_resolu': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }
        labels = {
            'motif_retard': 'Motif du retard',
            'retard_resolu': 'Retard résolu',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            if not isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs['class'] = 'form-control' 