#!/usr/bin/env python
"""
Script de test pour vérifier le flux de réinitialisation de mot de passe
"""
import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mission_manager.settings')
django.setup()

from django.test import Client
from core.models import Utilisateur
from django.urls import reverse

def test_forgot_password_flow():
    """Test du flux de réinitialisation de mot de passe"""
    client = Client()
    
    # Créer un utilisateur de test
    user, created = Utilisateur.objects.get_or_create(
        username='testuser',
        defaults={
            'email': 'test@example.com',
            'first_name': 'Test',
            'last_name': 'User',
            'role': 'employe'
        }
    )
    
    print("=== Test du flux de réinitialisation de mot de passe ===")
    
    # Test 1: Accès à la page initiale
    print("\n1. Test d'accès à la page initiale...")
    try:
        response = client.get(reverse('forgot_password'))
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            print("   ✅ Page accessible")
        else:
            print("   ❌ Erreur d'accès")
    except Exception as e:
        print(f"   ❌ Erreur: {e}")
    
    # Test 2: Soumission du nom d'utilisateur
    print("\n2. Test de soumission du nom d'utilisateur...")
    try:
        response = client.post(reverse('forgot_password'), {
            'step': 'username',
            'username': 'testuser'
        })
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            print("   ✅ Nom d'utilisateur accepté")
        else:
            print("   ❌ Erreur de soumission")
    except Exception as e:
        print(f"   ❌ Erreur: {e}")
    
    print("\n=== Test terminé ===")
    
    # Nettoyer
    if created:
        user.delete()

if __name__ == '__main__':
    test_forgot_password_flow() 