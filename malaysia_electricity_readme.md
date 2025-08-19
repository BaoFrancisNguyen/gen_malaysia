# Malaysia Electricity Generator

Générateur de données de consommation électrique et d'eau pour la Malaisie utilisant les données OpenStreetMap.

## Table des matières

- [Prérequis](#prérequis)
- [Installation](#installation)
- [Configuration](#configuration)
- [Utilisation](#utilisation)
- [API](#api)
- [Fonctionnalités](#fonctionnalités)
- [Structure du projet](#structure-du-projet)
- [Dépannage](#dépannage)

## Prérequis

- Python 3.8 ou supérieur
- 4 GB de RAM minimum (8 GB recommandé pour les grandes zones)
- Connexion Internet (pour accéder aux données OSM)

## Installation

### 1. Cloner le projet

```bash
git clone <url-du-repo>
cd malaysia-electricity-generator
```

### 2. Installation automatique

Utilisez le script de démarrage qui configure automatiquement l'environnement :

```bash
python run.py
```

Le script vérifie et installe automatiquement :
- Les dépendances Python
- La structure des dossiers
- Les fichiers de configuration

### 3. Installation manuelle

Si vous préférez installer manuellement :

```bash
# Créer un environnement virtuel
python -m venv malaysia-electricity-env
source malaysia-electricity-env/bin/activate  # Linux/Mac
# ou
malaysia-electricity-env\Scripts\activate     # Windows

# Installer les dépendances
pip install -r requirements.txt
```

### Dépendances principales

- **Flask 3.0.0** - Framework web
- **pandas 2.1.4** - Manipulation de données
- **numpy 1.25.2** - Calculs scientifiques
- **requests 2.31.0** - Requêtes HTTP
- **overpass 0.7** - API OpenStreetMap
- **pyarrow 14.0.1** - Format Parquet
- **openpyxl 3.1.2** - Format Excel

## Configuration

### Variables d'environnement (optionnel)

Créez un fichier `.env` pour personnaliser la configuration :

```bash
SECRET_KEY=votre-clé-secrète
MAX_BUILDINGS_PER_ZONE=50000
MAX_GENERATION_DAYS=365
LOG_LEVEL=INFO
```

### Dossiers créés automatiquement

- `exports/` - Fichiers de données exportés
- `logs/` - Journaux de l'application
- `static/` - Ressources web statiques
- `templates/` - Templates HTML

## Utilisation

### Démarrage de l'application

```bash
python app.py
```

L'application sera accessible sur `http://localhost:5000`

### Interface web

1. **Sélection de zone** : Choisissez une zone administrative de Malaisie
2. **Chargement des bâtiments** : Récupère les données OSM
3. **Configuration** : Définissez la période et les paramètres
4. **Génération** : Crée les données de consommation
5. **Export** : Téléchargez les résultats

### Utilisation en ligne de commande

```python
from src.services.osm_service import OSMService
from src.services.generation_service import EnhancedGenerationService

# Charger les bâtiments
osm_service = OSMService()
result = osm_service.load_buildings_for_zone("Kuala Lumpur")

# Générer les données complètes
generation_service = EnhancedGenerationService()
data = generation_service.generate_complete_dataset(
    buildings=result['buildings'],
    start_date="2024-01-01",
    end_date="2024-01-31",
    frequency="1H",
    include_weather=True,      # 33 paramètres météo
    include_water=True,        # Consommation d'eau
    weather_stations=5         # Nombre de stations météo
)

# Les données générées incluent :
# - data['consumption_data'] : Électricité horaire
# - data['water_data'] : Eau horaire  
# - data['weather_data'] : 33 colonnes météo par station
```

#### Générateur météorologique standalone

```python
from src.core.generator import WeatherGenerator

weather_gen = WeatherGenerator()
result = weather_gen.generate_weather_timeseries(
    start_date="2024-01-01",
    end_date="2024-01-31", 
    frequency="1H",
    station_count=10
)

# 33 colonnes météorologiques :
# temperature_2m, relative_humidity_2m, precipitation, wind_speed_10m, 
# pressure_msl, shortwave_radiation, soil_temperature_0_to_7cm, etc.
weather_df = result['data']
```

## API

### Endpoints principaux

#### GET /api/zones
Liste toutes les zones disponibles organisées par type administratif.

```json
{
  "success": true,
  "zones": ["Kuala Lumpur", "Selangor", ...],
  "total_zones": 157
}
```

#### POST /api/buildings/{zone_name}
Charge les bâtiments OSM pour une zone donnée.

```bash
curl -X POST http://localhost:5000/api/buildings/Kuala%20Lumpur
```

#### POST /api/generate
Génère les données de consommation électrique, eau et météo.

```json
{
  "start_date": "2024-01-01",
  "end_date": "2024-01-31",
  "frequency": "hourly",
  "include_weather": true,
  "include_water": true,
  "weather_stations": 5
}
```

**Réponse** :
```json
{
  "success": true,
  "session_info": {
    "generation_id": "WG_20240119_143022_ABC123",
    "summary": {
      "electricity_points": 74400,
      "water_points": 74400, 
      "weather_observations": 3720,
      "weather_stations": 5,
      "total_data_points": 152520
    }
  }
}
```

#### POST /api/export
Exporte les données dans différents formats.

```json
{
  "format": "csv",
  "filename": "kuala_lumpur_data"
}
```

#### GET /api/status
Statut de l'application et du cache.

## Fonctionnalités

### Données générées

**Consommation électrique**
- Données horaires réalistes par type de bâtiment
- Variation saisonnière et journalière
- Prise en compte des étages et de la géométrie précise
- Facteurs de forme et d'efficacité énergétique

**Consommation d'eau**
- Consommation résidentielle et commerciale
- Facteurs de pression et distribution verticale
- Variation selon l'usage du bâtiment et les étages
- Complexité des systèmes de distribution

**Données météorologiques (33 paramètres)**
- **Température** : température 2m, point de rosée, température apparente
- **Humidité** : humidité relative, déficit de pression vapeur
- **Précipitations** : pluie, neige (0 en Malaisie)
- **Vent** : vitesse, direction, rafales à 10m
- **Pression** : pression niveau mer et surface
- **Rayonnement solaire** : ondes courtes, direct, diffus, ensoleillement
- **Sol** : température et humidité du sol (0-7cm et 7-28cm)
- **Évapotranspiration** : évapotranspiration FAO
- **Nuages** : couverture nuageuse (totale, basse, moyenne, haute)
- **Codes météo** : classification des conditions atmosphériques

#### Spécificités climat tropical Malaisie
- **Température de base** : 27°C avec variation diurne de ±5°C
- **Humidité élevée** : 80% en moyenne (60-95%)
- **Précipitations tropicales** : 30% de chance l'après-midi, 10% la nuit
- **Saisons** : saison sèche (juin-août), saison des pluies (nov-fév)
- **Rayonnement intense** : jusqu'à 800 W/m² avec effet nuages

### Types de bâtiments supportés

- Résidentiel (maisons, appartements)
- Commercial (bureaux, magasins)
- Industriel (usines, entrepôts)
- Public (écoles, hôpitaux, administrations)
- Religieux (mosquées, temples)

### Formats d'export

- **CSV** - Format texte standard (4 fichiers séparés)
  - `buildings_metadata.csv` - Métadonnées bâtiments
  - `electricity_consumption.csv` - Consommation électrique 
  - `water_consumption.csv` - Consommation d'eau
  - `weather_simulation.csv` - 33 colonnes météorologiques

- **Parquet** - Format optimisé pour l'analyse (compression Snappy)
- **Excel** - Feuilles multiples avec métadonnées et graphiques
- **JSON** - Format structuré avec hiérarchie complète

#### Structure fichier météo (33 colonnes)

| Colonne | Description | Unité |
|---------|-------------|--------|
| timestamp | Horodatage | YYYY-MM-DD HH:MM:SS |
| temperature_2m | Température à 2m | °C |
| relative_humidity_2m | Humidité relative | 0-1 |
| precipitation | Précipitations | mm |
| wind_speed_10m | Vitesse vent | m/s |
| pressure_msl | Pression niveau mer | hPa |
| shortwave_radiation | Rayonnement solaire | W/m² |
| soil_temperature_0_to_7cm | Température sol surface | °C |
| et0_fao_evapotranspiration | Évapotranspiration | mm |
| location_id | ID station météo | entier |
| ... | 23 autres paramètres | ... |

## Structure du projet

```
malaysia-electricity-generator/
├── app.py                      # Application Flask principale
├── run.py                      # Script de démarrage
├── config.py                   # Configuration centralisée
├── requirements.txt            # Dépendances Python
├── src/
│   ├── core/                   # Modules principaux
│   │   ├── osm_handler.py      # Gestionnaire OSM
│   │   ├── electricity_generator.py  # Générateur électricité
│   │   ├── water_generator.py  # Générateur eau
│   │   └── generator.py        # Générateur météo (WeatherGenerator)
│   ├── services/               # Services métier
│   │   ├── osm_service.py
│   │   ├── generation_service.py
│   │   └── export_service.py
│   └── utils/                  # Utilitaires
│       ├── helpers.py
│       └── validators.py
├── templates/                  # Templates HTML
├── static/                     # CSS, JS, images
├── exports/                    # Fichiers exportés
└── logs/                       # Journaux
```

## Dépannage

### Dépannage

### Erreurs courantes

**"Mémoire insuffisante"**
- Créez un fichier `.env` avec `MAX_MEMORY_USAGE_GB=64`
- Utilisez le format Parquet au lieu de CSV
- Divisez votre zone en plus petites régions
- Réduisez la fréquence (1H au lieu de 30T)

**"Fichier trop volumineux"**
- Augmentez la limite : `MAX_EXPORT_FILE_SIZE_GB=1000` dans `.env`
- Utilisez l'export streaming par chunks
- Exportez par type de données séparément

**"Trop de bâtiments pour cette zone"**
- Augmentez : `MAX_BUILDINGS_PER_ZONE=2000000` dans `.env`
- Ou divisez la zone en sous-régions administratives

**"Timeout Overpass API"**
- Les gros volumes (>100k bâtiments) peuvent prendre 10+ minutes
- L'API OSM a ses propres limites de timeout
- Solution : découper par états/régions

**Cas de la Malaisie complète (1.3M bâtiments)**
```bash
# Créer .env pour débloquer les limites
MAX_BUILDINGS_PER_ZONE=2000000
MAX_EXPORT_FILE_SIZE_GB=1000
MAX_MEMORY_USAGE_GB=128
ENABLE_STREAMING_EXPORT=true

# Ou traiter par états
states = ["Kuala Lumpur", "Selangor", "Penang", "Johor", "Kedah", ...]
```

### Logs et débogage

Les logs sont sauvegardés dans `logs/app.log` avec différents niveaux :

```bash
# Consulter les logs en temps réel
tail -f logs/app.log

# Filtrer par niveau d'erreur
grep "ERROR" logs/app.log
```

### Limites du système et solutions pour gros volumes

**Limites par défaut (pour protéger les ressources) :**
- **Bâtiments par zone** : 50,000 (configurable)
- **Période de génération** : 365 jours maximum  
- **Taille de fichier export** : 2 GB (configurable via `.env`)
- **Stations météo** : 50 maximum par génération

**Cas d'usage extrême : Malaisie complète (1.3M bâtiments)**
- **Volume** : 45+ milliards de points de données
- **Fichiers** : 600+ GB (Parquet), 2+ TB (CSV)
- **Mémoire** : 4+ TB RAM nécessaire
- **Solutions recommandées** :

#### Solution 1 : Processing par chunks/régions
```python
# Diviser la Malaisie en régions plus petites
regions = ["Kuala Lumpur", "Selangor", "Penang", "Johor", ...]
for region in regions:
    # Traiter chaque région séparément
    generate_data_for_region(region, chunk_size=10000)
```

#### Solution 2 : Configuration pour gros volumes
Créez un fichier `.env` pour augmenter les limites :
```bash
# .env - Configuration gros volumes
MAX_BUILDINGS_PER_ZONE=2000000      # 2M bâtiments
MAX_EXPORT_FILE_SIZE_GB=1000        # 1TB
MAX_MEMORY_USAGE_GB=64              # 64GB RAM
ENABLE_STREAMING_EXPORT=true        # Export par chunks
CHUNK_SIZE=50000                    # Taille des chunks
```

#### Solution 3 : Export streaming (implémentation recommandée)
```python
# Export par chunks pour éviter la saturation mémoire
def export_large_dataset_streaming(buildings, start_date, end_date):
    chunk_size = 10000  # 10k bâtiments par chunk
    
    for i in range(0, len(buildings), chunk_size):
        chunk = buildings[i:i+chunk_size]
        
        # Générer et exporter immédiatement chaque chunk
        data = generate_chunk_data(chunk, start_date, end_date)
        export_chunk_to_file(data, chunk_index=i//chunk_size)
        
        # Libérer la mémoire
        del data
        gc.collect()
```

#### Solution 4 : Formats optimisés
- **Parquet avec compression** : Réduit la taille de 70%
- **Delta Lake** : Pour datasets évolutifs
- **Bases de données** : PostgreSQL/ClickHouse pour requêtes directes

### Performance pour gros volumes

**Scénarios de performance :**

| Bâtiments | Fréquence | Période | Fichier Parquet | RAM nécessaire | Temps estimé |
|-----------|-----------|---------|-----------------|----------------|--------------|
| 10,000 | 1H | 1 mois | 50 MB | 2 GB | 2 min |
| 50,000 | 1H | 1 mois | 250 MB | 8 GB | 8 min |
| 100,000 | 30T | 1 mois | 1 GB | 16 GB | 20 min |
| **1,300,000** | **30T** | **1 an** | **637 GB** | **4,245 GB** | **22h** |

**Solutions d'optimisation :**

1. **Processing par batches** : Diviser en régions de 50k-100k bâtiments
2. **Export streaming** : Écriture directe sans garder en mémoire
3. **Compression Parquet** : 70% de réduction de taille
4. **Serveurs cloud** : AWS/Azure avec 64-128 GB RAM
5. **Bases de données** : ClickHouse pour requêtes sur téraByte

**Configuration recommandée pour 1.3M bâtiments :**
```bash
# Serveur recommandé
RAM: 128 GB minimum
Stockage: 2 TB SSD
CPU: 16+ cores
Réseau: Gigabit (téléchargement OSM)

# Processing par régions
Chunk size: 50,000 bâtiments
Régions: 26 chunks de 50k bâtiments
Temps total: ~4-6 heures
```

### Performance

Pour optimiser les performances :

1. **Zones importantes** : Commencez par des zones plus petites
2. **Périodes courtes** : Testez avec 1 semaine avant 1 an
3. **Formats efficaces** : Utilisez Parquet pour les gros volumes
4. **Cache** : Les bâtiments sont mis en cache automatiquement

### Support

Pour les problèmes techniques :

1. Consultez les logs dans `logs/app.log`
2. Vérifiez le statut avec `/api/status`
3. Redémarrez l'application si nécessaire

### Contribution

Le projet utilise une architecture modulaire facilement extensible :

- **Nouveaux générateurs** dans `src/core/` 
  - `electricity_generator.py` - Consommation électrique avec géométrie
  - `water_generator.py` - Consommation d'eau avec systèmes verticaux  
  - `generator.py` - Météorologie tropicale (33 paramètres)
- **Nouveaux services** dans `src/services/`
- **Validation** dans `src/utils/validators.py`

#### Ajouter un nouveau paramètre météorologique

```python
# Dans src/core/generator.py - WeatherGenerator
def _generate_station_weather_series(self, date_range, location_id):
    # ...
    # Ajouter votre nouveau paramètre :
    custom_parameter = your_calculation_function(timestamp, climate)
    
    weather_observation = {
        # ... autres paramètres
        'custom_parameter': round(custom_parameter, 2)
    }
```

#### Créer un nouveau type de générateur

```python
# Nouveau fichier src/core/gas_generator.py
class GasGenerator:
    def generate_gas_consumption(self, buildings, start_date, end_date):
        # Votre logique de génération
        pass
```

---

**Version** : 3.1.0 Enhanced  
**Dernière mise à jour** : 2025