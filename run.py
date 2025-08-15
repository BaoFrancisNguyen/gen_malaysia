#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MALAYSIA ELECTRICITY GENERATOR - SCRIPT DE DÉMARRAGE REFACTORISÉ
================================================================

Script de démarrage pour l'architecture factorisée avec structure modulaire.
Version unique et corrigée.

Version: 3.0.0 - Architecture Factorisée
"""

import sys
import os
import subprocess
from pathlib import Path

# Chemin du projet
PROJECT_ROOT = Path(__file__).parent.absolute()


def check_python_version():
    """Vérifie que Python 3.8+ est utilisé"""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 ou supérieur requis")
        print(f"   Version actuelle: {sys.version}")
        return False
    
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")
    return True


def check_dependencies():
    """Vérifie les dépendances Python essentielles"""
    required_packages = [
        'flask',
        'pandas', 
        'numpy',
        'requests',
        'overpass',
        'pyarrow',  # Pour Parquet
        'openpyxl'  # Pour Excel
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
            print(f"✅ {package}")
        except ImportError:
            missing_packages.append(package)
            print(f"❌ {package} manquant")
    
    if missing_packages:
        print(f"\n📦 Installation des dépendances manquantes...")
        try:
            subprocess.check_call([
                sys.executable, '-m', 'pip', 'install'
            ] + missing_packages)
            print("✅ Dépendances installées avec succès")
            return True
        except subprocess.CalledProcessError:
            print("❌ Erreur installation dépendances")
            print("💡 Installez manuellement avec:")
            print(f"   pip install {' '.join(missing_packages)}")
            return False
    
    return True


def create_project_structure():
    """Crée la structure de dossiers selon l'architecture factorisée"""
    required_dirs = [
        # Dossiers principaux
        'src',
        'src/core',
        'src/models',
        'src/services', 
        'src/utils',
        'templates',
        'static',
        'static/css',
        'static/js',
        'exports', 
        'logs',
        'tests'
    ]
    
    print("📁 Création de la structure du projet...")
    
    for directory in required_dirs:
        dir_path = PROJECT_ROOT / directory
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            print(f"✅ Créé: {directory}/")
        else:
            print(f"✅ Existe: {directory}/")
    
    # Création des fichiers __init__.py pour les packages Python
    init_files = [
        'src/__init__.py',
        'src/core/__init__.py',
        'src/models/__init__.py',
        'src/services/__init__.py',
        'src/utils/__init__.py',
        'tests/__init__.py'
    ]
    
    for init_file in init_files:
        init_path = PROJECT_ROOT / init_file
        if not init_path.exists():
            init_path.write_text('# -*- coding: utf-8 -*-\n')
            print(f"✅ Créé: {init_file}")
    
    return True


def check_architecture_files():
    """Vérifie que les fichiers de l'architecture factorisée existent"""
    required_files = {
        'app.py': 'Application Flask principale',
        'config.py': 'Configuration centralisée',
        'src/core/osm_handler.py': 'Gestionnaire OSM',
        'src/core/generator.py': 'Générateurs de données',
        'src/core/data_exporter.py': 'Exporteur de données',
        'src/services/osm_service.py': 'Service OSM',
        'src/services/generation_service.py': 'Service de génération',
        'src/services/export_service.py': 'Service d\'export',
        'src/utils/helpers.py': 'Fonctions d\'aide',
        'src/utils/validators.py': 'Validateurs'
    }
    
    missing_files = []
    
    for file_path, description in required_files.items():
        full_path = PROJECT_ROOT / file_path
        if not full_path.exists():
            missing_files.append((file_path, description))
            print(f"❌ Manquant: {file_path} - {description}")
        else:
            print(f"✅ Existe: {file_path}")
    
    if missing_files:
        print(f"\n⚠️ {len(missing_files)} fichiers manquants de l'architecture")
        print("💡 Utilisez les artefacts fournis pour créer les fichiers manquants")
        return False
    
    print("✅ Architecture factorisée complète")
    return True


def create_template_if_missing():
    """Crée le template index.html s'il est manquant"""
    template_file = PROJECT_ROOT / 'templates' / 'index.html'
    
    if template_file.exists():
        print("✅ Template index.html existe")
        return True
    
    print("⚠️ Template index.html manquant")
    print("💡 Utilisez le template HTML fourni dans les artefacts")
    
    # Créer un template minimal de fallback
    minimal_template = '''<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <title>Malaysia Electricity Generator v3.0 - Factorisé</title>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/bootstrap/5.3.0/css/bootstrap.min.css" rel="stylesheet">
</head>
<body>
    <div class="container mt-5">
        <h1 class="text-center mb-4">🇲🇾 Malaysia Electricity Generator v3.0</h1>
        <div class="alert alert-info text-center">
            <h4>Architecture Factorisée Active</h4>
            <p><strong>✨ Caractéristiques:</strong></p>
            <ul class="list-unstyled">
                <li>📁 4 fichiers d'export distincts</li>
                <li>🏗️ Architecture modulaire propre</li>
                <li>⚡ Séparation des responsabilités</li>
                <li>🔧 Code factorisation correcte</li>
            </ul>
            
            <h5 class="mt-4">API REST Disponible:</h5>
            <ul class="list-unstyled">
                <li><code>GET /api/zones</code> - Liste des zones Malaysia</li>
                <li><code>POST /api/buildings/&lt;zone&gt;</code> - Charger bâtiments OSM</li>
                <li><code>POST /api/generate</code> - Générer données électriques + météo</li>
                <li><code>POST /api/export</code> - Exporter les fichiers</li>
                <li><code>GET /api/status</code> - Statut de l'application</li>
            </ul>
            
            <button onclick="testAPI()" class="btn btn-primary mt-3">Tester l'API</button>
            <div id="result" class="mt-3"></div>
        </div>
    </div>
    
    <script>
        async function testAPI() {
            try {
                const response = await fetch('/api/status');
                const data = await response.json();
                document.getElementById('result').innerHTML = 
                    `<div class="alert alert-success">✅ API Active v${data.version}<br>
                     Cache: ${data.cache.buildings_loaded} bâtiments</div>`;
            } catch (error) {
                document.getElementById('result').innerHTML = 
                    `<div class="alert alert-danger">❌ Erreur: ${error}</div>`;
            }
        }
    </script>
</body>
</html>'''
    
    try:
        with open(template_file, 'w', encoding='utf-8') as f:
            f.write(minimal_template)
        print("✅ Template minimal créé")
        return True
    except Exception as e:
        print(f"❌ Erreur création template: {e}")
        return False


def main():
    """Fonction principale de démarrage"""
    print("="*70)
    print("🇲🇾 MALAYSIA ELECTRICITY GENERATOR v3.0 - ARCHITECTURE FACTORISÉE")
    print("="*70)
    print("🔍 Vérification de l'environnement et de l'architecture...")
    print()
    
    # Vérifications préalables
    if not check_python_version():
        sys.exit(1)
    
    print()
    if not check_dependencies():
        print("\n💡 Installez les dépendances et relancez")
        sys.exit(1)
    
    print()
    if not create_project_structure():
        sys.exit(1)
    
    print()
    if not check_architecture_files():
        print("\n💡 Architecture incomplète - utilisez les artefacts fournis")
        # Continue quand même pour permettre les tests partiels
    
    print()
    create_template_if_missing()
    
    print("\n" + "="*70)
    print("🚀 DÉMARRAGE DE L'APPLICATION FACTORISÉE")
    print("="*70)
    
    try:
        # Import et démarrage
        from app import app
        
        print("✅ Application Flask importée")
        print("\n📋 ARCHITECTURE REFACTORISÉE:")
        print("   🏗️ Structure modulaire avec séparation des responsabilités")
        print("   📁 Core: OSMHandler, ElectricityGenerator, WeatherGenerator, DataExporter")
        print("   🔧 Services: OSMService, GenerationService, ExportService")
        print("   🛠️ Utils: helpers, validators centralisés")
        print("   ⚙️ Config: configuration centralisée")
        print()
        print("📤 4 FICHIERS D'EXPORT DISTINCTS:")
        print("   • buildings_metadata - Métadonnées bâtiments OSM")
        print("   • electricity_consumption - Séries temporelles électriques") 
        print("   • water_consumption - Séries temporelles eau")
        print("   • weather_simulation - Données météo (33 colonnes)")
        print()
        print("🌐 URL: http://127.0.0.1:5000")
        print("📁 Exports: exports/")
        print("📋 Logs: logs/")
        print("🏗️ Architecture: structure modulaire factorisée")
        print()
        print("▶️  Ctrl+C pour arrêter")
        print("="*70)
        
        # Lancement serveur Flask
        app.run(
            host='127.0.0.1',
            port=5000,
            debug=True,
            threaded=True
        )
        
    except ImportError as e:
        print(f"❌ Erreur import app: {e}")
        print("💡 Vérifiez que tous les fichiers de l'architecture sont présents")
        print("   Utilisez les artefacts fournis pour créer les modules manquants")
        sys.exit(1)
        
    except KeyboardInterrupt:
        print("\n\n👋 Arrêt de l'application")
        
    except Exception as e:
        print(f"\n❌ Erreur démarrage: {e}")
        import traceback
        traceback.print_exc()
        print("\n💡 Vérifiez que l'architecture factorisée est complète")
        sys.exit(1)


if __name__ == '__main__':
    main()