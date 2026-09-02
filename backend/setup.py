#!/usr/bin/env python3
"""
Script de configuration initial pour Wakif AI
Configure tout ce qui est nécessaire pour démarrer
"""

import os
import sys
import subprocess

def print_header(text):
    print("\n" + "=" * 60)
    print(f"🇲🇦 {text}")
    print("=" * 60 + "\n")

def run_command(cmd, description):
    print(f"⏳ {description}...")
    try:
        subprocess.run(cmd, shell=True, check=True)
        print(f"✅ {description} - OK\n")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} - ÉCHOUÉ\n")
        return False

def check_python_version():
    print_header("Vérification de Python")
    version = sys.version_info
    if version.major == 3 and version.minor >= 8:
        print(f"✅ Python {version.major}.{version.minor} détecté")
        return True
    else:
        print(f"❌ Python 3.8+ requis (trouvé: {version.major}.{version.minor})")
        return False

def check_ollama():
    print_header("Vérification d'Ollama")
    if os.path.exists("ollama") or subprocess.run("ollama --version", shell=True, capture_output=True).returncode == 0:
        print("✅ Ollama est installé")
        return True
    else:
        print("⚠️ Ollama n'est pas détecté")
        print("Télécharge Ollama depuis: https://ollama.ai")
        return False

def setup_environment():
    print_header("Configuration de l'environnement")
    
    env_file = ".env"
    if not os.path.exists(env_file):
        print("📝 Création du fichier .env...")
        with open(env_file, 'w') as f:
            f.write("""# Configuration Wakif AI
BRAVE_API_KEY=BSAcFTixd0I6LMOEpASq6uLALTvt2H9
CACHE_TTL_MINUTES=120
HOST=0.0.0.0
PORT=8000
DEBUG=False
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=atlas-9b
LOG_LEVEL=INFO
""")
        print("✅ Fichier .env créé")
    else:
        print("✅ Fichier .env existe déjà")

def install_dependencies():
    print_header("Installation des dépendances Python")
    
    if not run_command("pip install -r requirements.txt", "Installation des packages"):
        print("⚠️ Certains packages n'ont pas pu être installés")
        print("Essaye: pip install -r requirements_new.txt")
        return False
    
    return True

def test_setup():
    print_header("Test de la configuration")
    
    tests = [
        ("python -m fastapi --version", "Vérification de FastAPI"),
        ("python -c \"import ollama; print('Ollama OK')\"", "Vérification de Ollama Client"),
        ("python -c \"import requests; print('Requests OK')\"", "Vérification de Requests"),
    ]
    
    all_passed = True
    for cmd, desc in tests:
        if not run_command(cmd, desc):
            all_passed = False
    
    return all_passed

def print_next_steps():
    print_header("Prochaines étapes")
    
    print("""
1️⃣ Lance Ollama (en terminal séparé):
   ollama serve
   
2️⃣ Télécharge le modèle Atlas (optionnel):
   ollama pull atlas-9b
   
3️⃣ Lance le serveur Wakif:
   uvicorn main:app --reload
   
4️⃣ Accède à l'interface:
   http://localhost:8000/docs
   
5️⃣ Teste avec cURL:
   curl -X POST "http://localhost:8000/chat" \\
     -H "Content-Type: application/json" \\
     -d '{"message": "السلام عليكم", "user_id": "test"}'

📚 Consulte le README pour plus de détails!
    """)

def main():
    print("\n")
    print("  🇲🇦 WAKIF AI - Script de Configuration")
    print("  =====================================")
    print("  أفضل مساعد ذكي مغربي - Setup Assistant")
    print("  " + "=" * 41 + "\n")
    
    checks = [
        ("Vérification Python", check_python_version),
        ("Vérification Ollama", check_ollama),
        ("Configuration de l'environnement", setup_environment),
        ("Installation des dépendances", install_dependencies),
        ("Test de la configuration", test_setup),
    ]
    
    for check_name, check_func in checks:
        try:
            if not check_func():
                if "Ollama" not in check_name:
                    print(f"⚠️ {check_name} - Non bloquant\n")
        except Exception as e:
            print(f"❌ Erreur: {e}\n")
    
    print_next_steps()
    
    print("\n✅ Configuration terminée!")
    print("   Pour des questions: https://github.com/YourRepo\n")

if __name__ == "__main__":
    main()
