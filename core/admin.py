from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Utilisateur, RapportIntervention, RapportImage, RapportFichierJoint

class UtilisateurAdmin(UserAdmin):
    model = Utilisateur
    list_display = ('username', 'email', 'role', 'telephone', 'is_active', 'is_staff')
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ("Informations personnelles", {'fields': ('first_name', 'last_name', 'email')}),
        ("Permissions", {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ("Dates importantes", {'fields': ('last_login', 'date_joined')}),
        ("Informations supplémentaires", {'fields': ('role', 'telephone')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'role', 'telephone', 'password1', 'password2'),
        }),
    )

    def get_fieldsets(self, request, obj=None):
        return self.fieldsets

class RapportImageInline(admin.TabularInline):
    model = RapportImage
    extra = 1

class RapportFichierJointInline(admin.TabularInline):
    model = RapportFichierJoint
    extra = 1

@admin.register(RapportIntervention)
class RapportInterventionAdmin(admin.ModelAdmin):
    list_display = ('id', 'intervention', 'statut', 'date_creation', 'date_modification')
    list_filter = ('statut',)
    search_fields = ('intervention__titre', 'objectif', 'travaux_realises')
    inlines = [RapportImageInline, RapportFichierJointInline]

@admin.register(RapportImage)
class RapportImageAdmin(admin.ModelAdmin):
    list_display = ('id', 'rapport', 'type_image', 'image', 'description')
    list_filter = ('type_image',)
    search_fields = ('rapport__id', 'description')

@admin.register(RapportFichierJoint)
class RapportFichierJointAdmin(admin.ModelAdmin):
    list_display = ('id', 'rapport', 'fichier', 'description')
    search_fields = ('rapport__id', 'description')

admin.site.register(Utilisateur, UtilisateurAdmin)
