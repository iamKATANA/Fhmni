#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tests pour le système de routage intelligent de Wakif AI
Vérifie que les recherches se font seulement quand nécessaire
"""

import sys
import io

# Force UTF-8 output
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from search_router import needs_search


def test_should_search():
    """Tests des cas où une recherche DOIT être faite"""
    
    test_cases = [
        # Actualités / Nouvelles
        ("شنو أخبار اليوم؟", True, "Doit chercher - nouvelles"),
        ("اش اخبار الطقس دابا؟", True, "Doit chercher - météo actuelle"),
        ("كاينة أخبار جديدة؟", True, "Doit chercher - actualités"),
        
        # Temps réel
        ("شنو السعر دابا؟", True, "Doit chercher - prix actuel"),
        ("آش دراجة السيارة دابا؟", True, "Doit chercher - prix temps réel"),
        ("الساعة شنو دابا؟", True, "Doit chercher - heure actuelle"),
        
        # Événements à venir
        ("شنو لي غاد يوقع غدا؟", True, "Doit chercher - événement futur"),
        ("شنو بصح الحفلة من غدا؟", True, "Doit chercher - planification"),
        
        # Français
        ("Quelles sont les dernières nouvelles?", True, "Doit chercher - dernier FR"),
        ("Quel est le prix actuel de l'or?", True, "Doit chercher - prix actuel FR"),
    ]
    
    print("[OK] Tests: CAS OU IL FAUT CHERCHER")
    print("=" * 50)
    
    for message, expected, description in test_cases:
        result = needs_search(message)
        status = "[OK]" if result == expected else "[FAIL]"
        print(f"{status} {description}")
        print(f"   Message: '{message}'")
        print(f"   Resultat: {result} (attendu: {expected})")
        print()


def test_should_not_search():
    """Tests des cas où une recherche ne DOIT PAS être faite"""
    
    test_cases = [
        # Explications générales
        ("شنو معنا الحب؟", False, "Ne doit pas chercher - concept"),
        ("فاش الفرق بين الذهب والفضة؟", False, "Ne doit pas chercher - explication"),
        ("كيفاش نطبخ الطاجين؟", False, "Ne doit pas chercher - recette générale"),
        
        # Questions générales
        ("مرحبا، شنو أخبارك؟", False, "Ne doit pas chercher - conversation"),
        ("كاينة شي حاجة تقدر تساعدني بها؟", False, "Ne doit pas chercher - question générale"),
        
        # Français
        ("Comment fonctionne le cerveau?", False, "Ne doit pas chercher - explication générale"),
        ("Quelle est la capitale de la France?", False, "Ne doit pas chercher - connaissance générale"),
        
        # Anglais
        ("What is artificial intelligence?", False, "Ne doit pas chercher - concept général"),
    ]
    
    print("\n[FAIL] Tests: CAS OU IL NE FAUT PAS CHERCHER")
    print("=" * 50)
    
    for message, expected, description in test_cases:
        result = needs_search(message)
        status = "[OK]" if result == expected else "[FAIL]"
        print(f"{status} {description}")
        print(f"   Message: '{message}'")
        print(f"   Resultat: {result} (attendu: {expected})")
        print()


def test_with_history():
    """Tests avec l'historique de conversation"""
    
    print("\n[INFO] Tests: AVEC HISTORIQUE DE CONVERSATION")
    print("=" * 50)
    
    # Premier message: devrait chercher
    msg1 = "شنو اخبار الطقس؟"
    result1 = needs_search(msg1, history=[])
    print(f"Message 1: '{msg1}'")
    print(f"Resultat: {result1} (devrait chercher au premier passage)")
    print()
    
    # Deuxième message: même sujet, avec historique
    msg2 = "و كاينة احتمالية دلماطار نهار غدا؟"
    history = [
        {"role": "user", "content": msg1},
        {"role": "assistant", "content": "الطقس دابا..."}
    ]
    result2 = needs_search(msg2, history=history)
    print(f"Message 2: '{msg2}'")
    print(f"Resultat: {result2} (peut skip si sujet déjà couvert)")
    print()


def main():
    print("\n" + "=" * 50)
    print("TESTS DU ROUTEUR INTELLIGENT DE WAKIF AI")
    print("=" * 50 + "\n")
    
    test_should_search()
    test_should_not_search()
    test_with_history()
    
    print("\n" + "=" * 50)
    print("[OK] Tests termines!")
    print("=" * 50 + "\n")


if __name__ == "__main__":
    main()

