# Malaysia Electricity Generator - Guide des Calculs

## Table des Matières
- [Vue d'ensemble](#vue-densemble)
- [Consommation Électrique](#consommation-électrique)
- [Consommation d'Eau](#consommation-deau)
- [Données Météorologiques](#données-météorologiques)
- [Métadonnées des Bâtiments](#métadonnées-des-bâtiments)
- [Facteurs de Variation](#facteurs-de-variation)
- [Exemples Concrets](#exemples-concrets)

---

## Vue d'ensemble

Le **Malaysia Electricity Generator** utilise une approche géométrique avancée pour calculer les consommations énergétiques réalistes. Les calculs se basent sur :

- **Géométrie précise** des polygones OSM
- **Nombre d'étages** extrait des métadonnées
- **Climat tropical** de Malaysia
- **Variations temporelles** réalistes
- **Types de bâtiments** spécifiques

### Architecture des Calculs

```
Bâtiments OSM → Géométrie précise → Surface × Étages → Consommation de base
     ↓
Facteurs temporels → Facteurs géométriques → Facteurs d'étages → Consommation finale
```

---

## Consommation Électrique

### Unité finale
**kWh/h** (kilowatt-heures par heure) pour chaque bâtiment à chaque timestamp

### Calcul de Base

```python
# 1. Surface totale = Surface sol × Nombre d'étages
total_floor_area = surface_sol_m2 * floors_count

# 2. Consommation journalière de base
daily_consumption = base_kwh_m2_day * total_floor_area

# 3. Conversion horaire
hourly_base = daily_consumption / 24
```

### Consommations de Référence (kWh/m²/jour)

| Type de Bâtiment | Base (kWh/m²/jour) | Occupation (h) | Équipements Principaux |
|------------------|-------------------|----------------|------------------------|
| **Résidentiel** | 0.8 | 16-24h | Climatisation, électroménager |
| **Commercial** | 1.5 | 10-14h | Éclairage, réfrigération |
| **Bureau** | 2.0 | 8-10h | IT, climatisation, ascenseurs |
| **Industriel** | 3.5 | 16-24h | Machines, process industriels |
| **École** | 1.2 | 8-12h | Éclairage, ventilation |
| **Hôpital** | 4.0 | 24h | Équipements médicaux |

### Facteurs d'Ajustement

#### 1. Facteur d'Étages
```python
if building_type == 'residential':
    floors_efficiency = 1.0 + (floors_count - 1) * 0.05  # +5% par étage
elif building_type in ['office', 'commercial']:
    floors_efficiency = 1.0 + (floors_count - 1) * 0.08  # +8% par étage (ascenseurs)
elif building_type == 'industrial':
    floors_efficiency = 1.0 + (floors_count - 1) * 0.02  # +2% par étage
```

#### 2. Facteur de Forme Géométrique
```python
# Basé sur le rapport périmètre/aire du polygone OSM
shape_factor = perimeter / (2 * sqrt(π * area))
shape_penalty = 1.0 + (shape_factor - 1.0) * 0.05

# Bâtiments allongés = moins efficaces énergétiquement
```

#### 3. Facteur de Taille
```python
if total_floor_area < 100:
    size_factor = 1.1      # Petits bâtiments moins efficaces
elif total_floor_area > 10000:
    size_factor = 0.9      # Gros bâtiments plus efficaces (économies d'échelle)
else:
    size_factor = 1.0      # Taille standard
```

### Variations Temporelles

#### Variation Horaire
```python
# Résidentiel : pics matin et soir
if 6 <= hour <= 8 or 18 <= hour <= 22:
    hour_factor = 1.5
elif 0 <= hour <= 5:
    hour_factor = 0.3
else:
    hour_factor = 1.0

# Bureau : heures de travail
if 8 <= hour <= 18:
    hour_factor = 1.8      # Climatisation, éclairage, IT
else:
    hour_factor = 0.2      # Mode veille
```

#### Variation Journalière
```python
# Weekdays vs Weekend
if building_type == 'residential':
    day_factor = 1.2 if day_of_week >= 5 else 1.0  # Plus de consommation le weekend
elif building_type in ['office', 'commercial']:
    day_factor = 0.3 if day_of_week >= 5 else 1.0  # Fermé le weekend
```

#### Variation Saisonnière (Climat Malaysia)
```python
if 6 <= month <= 8:        # Saison sèche
    seasonal_factor = 1.3   # Plus de climatisation
elif 11 <= month <= 2:     # Saison des pluies
    seasonal_factor = 0.9   # Moins de climatisation
else:
    seasonal_factor = 1.0   # Saison normale
```

#### Facteur Spécifique aux Étages
```python
# Impact des ascenseurs selon l'heure
if building_type == 'office':
    if 8 <= hour <= 9 or 17 <= hour <= 18:  # Pics de circulation
        floors_factor = base_floors_impact * 1.3
    elif 9 <= hour <= 17:
        floors_factor = base_floors_impact * 1.1
    else:
        floors_factor = base_floors_impact * 0.7
```

### Formule Finale
```python
consumption_kwh = (
    base_consumption * 
    hour_factor * 
    day_factor * 
    seasonal_factor * 
    floors_factor * 
    shape_efficiency_factor * 
    random_factor  # Variation aléatoire ±10%
)
```

---

## Consommation d'Eau

### Unité finale
**L/h** (litres par heure) pour chaque bâtiment à chaque timestamp

### Calcul de Base

```python
# 1. Surface totale = Surface sol × Nombre d'étages
total_floor_area = surface_sol_m2 * floors_count

# 2. Consommation journalière de base
daily_water = base_L_m2_day * total_floor_area

# 3. Conversion horaire
hourly_base = daily_water / 24
```

### Consommations de Référence (L/m²/jour)

| Type de Bâtiment | Base (L/m²/jour) | Usage Principal |
|------------------|------------------|-----------------|
| **Résidentiel** | 150 | Douches, cuisine, sanitaires |
| **Commercial** | 80 | Sanitaires clients, nettoyage |
| **Bureau** | 60 | Sanitaires employés |
| **Industriel** | 200 | Process industriels, nettoyage |
| **École** | 100 | Sanitaires, fontaines, cantine |
| **Hôpital** | 300 | Sanitaires, stérilisation, cuisine |

### Facteurs Spécifiques à l'Eau

#### 1. Facteur de Pression (Étages)
```python
# Besoins en surpression pour les étages élevés
pressure_factor = 1.0 + (floors_count - 1) * 0.05

if floors_count > 5:
    pressure_factor *= 1.1   # Système de pompage plus complexe
if floors_count > 10:
    pressure_factor *= 1.15  # Système haute pression
```

#### 2. Facteur de Distribution (Géométrie)
```python
# Bâtiments de forme complexe = plus de tuyauterie
shape_factor = perimeter / (2 * sqrt(π * area))
distribution_complexity = 1.0 + (shape_factor - 1.0) * 0.08
```

#### 3. Facteur d'Efficacité par Étages
```python
if building_type == 'residential':
    floors_efficiency = 1.0 + (floors_count - 1) * 0.1   # +10% par étage
elif building_type in ['office', 'commercial']:
    floors_efficiency = 1.0 + (floors_count - 1) * 0.12  # +12% par étage
elif building_type == 'hospital':
    floors_efficiency = 1.0 + (floors_count - 1) * 0.15  # +15% par étage
```

### Variations Temporelles Eau

#### Variation Horaire Spécifique
```python
# Résidentiel : pics spécifiques à l'usage de l'eau
if 6 <= hour <= 8:      # Douches matin
    hour_factor = 2.0
elif 11 <= hour <= 13:  # Cuisine midi
    hour_factor = 1.5
elif 18 <= hour <= 21:  # Douches soir + cuisine
    hour_factor = 1.8
elif 22 <= hour <= 6:   # Nuit
    hour_factor = 0.2
else:
    hour_factor = 1.0

# Bureau : usage pendant les heures de travail
if 8 <= hour <= 18:
    hour_factor = 1.5      # Sanitaires + fontaines
else:
    hour_factor = 0.1      # Fermé
```

#### Facteur Multi-Étages par Heure
```python
# Usage des ascenseurs et systèmes verticaux pour l'eau
if building_type == 'office':
    if 8 <= hour <= 9 or 12 <= hour <= 13 or 17 <= hour <= 18:
        floors_water_factor = base_floors_impact * 1.4  # Pics d'usage
    else:
        floors_water_factor = base_floors_impact
```

### Formule Finale Eau
```python
water_consumption_L = (
    base_water_consumption * 
    hour_factor * 
    day_factor * 
    seasonal_factor * 
    floors_water_factor * 
    pressure_efficiency_factor * 
    distribution_loss_factor * 
    random_factor  # Variation aléatoire ±15%
)
```

---

## Données Météorologiques

### Structure
**33 colonnes** de données météorologiques simulées pour le climat tropical de Malaysia

### Paramètres de Base (Climate Malaysia)
```python
CLIMATE_PARAMS = {
    'base_temperature': 27.0,      # °C (température moyenne)
    'base_humidity': 0.8,          # 80% (humidité relative)
    'base_pressure': 1013.25,      # hPa (pression atmosphérique)
    'temperature_variation': 5.0,   # Variation diurne
    'seasonal_variation': 2.0,     # Variation saisonnière
}
```

### Colonnes Générées

#### Température et Humidité
- `temperature_2m` : Température à 2m (°C)
- `relative_humidity_2m` : Humidité relative (0-1)
- `dew_point_2m` : Point de rosée (°C)
- `apparent_temperature` : Température ressentie (°C)

#### Précipitations
- `precipitation` : Précipitations totales (mm)
- `rain` : Pluie (mm)
- `snowfall` : Neige (mm) - toujours 0 en Malaysia
- `snow_depth` : Épaisseur neige (mm) - toujours 0

#### Pression et Vent
- `pressure_msl` : Pression niveau mer (hPa)
- `surface_pressure` : Pression surface (hPa)
- `wind_speed_10m` : Vitesse vent à 10m (m/s)
- `wind_direction_10m` : Direction vent (°)
- `wind_gusts_10m` : Rafales (m/s)

#### Rayonnement Solaire
- `shortwave_radiation` : Rayonnement ondes courtes (W/m²)
- `direct_radiation` : Rayonnement direct (W/m²)
- `diffuse_radiation` : Rayonnement diffus (W/m²)
- `sunshine_duration` : Durée ensoleillement (s)

#### Sol et Évaporation
- `soil_temperature_0_to_7cm` : Température sol 0-7cm (°C)
- `soil_moisture_0_to_7cm` : Humidité sol 0-7cm (m³/m³)
- `et0_fao_evapotranspiration` : Évapotranspiration (mm)

### Calculs Spécifiques

#### Variation Diurne
```python
# Température varie selon l'heure
temp_diurnal = temperature_variation * sin((hour - 6) * π / 12)
temperature_2m = base_temperature + temp_diurnal + seasonal + noise
```

#### Précipitations (Climat Tropical)
```python
# Probabilité de pluie l'après-midi (climat tropical)
if 14 <= hour <= 18:
    precip_prob = 0.3    # 30% de chance l'après-midi
else:
    precip_prob = 0.1    # 10% autres heures

if random() < precip_prob:
    precipitation = exponential(5)  # Distribution exponentielle
```

#### Rayonnement Solaire
```python
if is_day:
    base_radiation = 800 * sin((hour - 6) * π / 12)
    cloud_factor = (100 - cloud_cover) / 100
    shortwave_radiation = base_radiation * cloud_factor
else:
    shortwave_radiation = 0  # Nuit
```

---

## Métadonnées des Bâtiments

### Extraction Géométrique OSM

#### Calcul Surface Précise
```python
# Algorithme Shoelace pour calculer l'aire d'un polygone
area_deg = 0.0
for i in range(n):
    j = (i + 1) % n
    area_deg += coordinates[i][0] * coordinates[j][1]
    area_deg -= coordinates[j][0] * coordinates[i][1]
area_deg = abs(area_deg) / 2.0

# Conversion degrés → mètres carrés (Malaysia ~3-7°N)
lat_center = sum(coord[0] for coord in coordinates) / len(coordinates)
meters_per_degree_lat = 111000
meters_per_degree_lon = 111000 * cos(radians(lat_center))
area_m2 = area_deg * meters_per_degree_lat * meters_per_degree_lon
```

#### Extraction Nombre d'Étages
```python
# Sources prioritaires (par ordre de fiabilité)
floors_sources = [
    'building:levels',     # Tag OSM principal
    'levels',             # Tag OSM alternatif
    'building:floors',    # Tag OSM floors
    'height'              # Converti : height/3.5m par étage
]

# Estimation par type si pas de données
if building_type == 'residential':
    floors = choice([1, 2, 3], p=[0.6, 0.3, 0.1])
elif building_type == 'office':
    floors = choice([1,2,3,4,5,6,7,8,9,10], 
                   p=[0.3,0.2,0.15,0.1,0.08,0.06,0.04,0.03,0.02,0.02])
```

#### Facteur de Forme
```python
# Indice de compacité du bâtiment
perimeter = sum(distance between consecutive points)
area = shoelace_area(coordinates)
shape_factor = perimeter / (2 * sqrt(π * area))

# 1.0 = cercle parfait, >1.0 = forme allongée
```

### Structure de Sortie Bâtiments

| Colonne | Description | Unité |
|---------|-------------|-------|
| `unique_id` | Identifiant unique | - |
| `building_type` | Type normalisé | - |
| `latitude` | Latitude précise | degrés |
| `longitude` | Longitude précise | degrés |
| `surface_area_m2` | Surface sol | m² |
| `polygon_area_m2` | Surface calculée polygone | m² |
| `floors_count` | Nombre d'étages | - |
| `has_precise_geometry` | Géométrie OSM disponible | boolean |
| `validation_score` | Score qualité (0-1) | - |

---

## Facteurs de Variation

### Synthèse des Facteurs Appliqués

#### Électricité
1. **Base** : type × surface_totale
2. **Étages** : +5% à +8% par étage selon type
3. **Forme** : +5% pour formes allongées
4. **Taille** : ±10% selon économies d'échelle
5. **Heure** : 0.2 à 1.8× selon type et heure
6. **Jour** : 0.3 à 1.2× weekend vs semaine
7. **Saison** : 0.9 à 1.3× selon saison Malaysia
8. **Aléatoire** : ±10%

#### Eau
1. **Base** : type × surface_totale
2. **Étages** : +10% à +15% par étage selon type
3. **Pression** : +5% par étage (surpression)
4. **Distribution** : +8% pour formes complexes
5. **Heure** : 0.1 à 2.0× selon usage spécifique eau
6. **Jour** : 0.2 à 1.3× weekend vs semaine
7. **Saison** : 0.8 à 1.4× selon saisons pluies
8. **Aléatoire** : ±15%

### Réalisme des Variations

Les facteurs sont calibrés pour reproduire :
- **Patterns de vie malaysiens** (climat, horaires)
- **Efficacité énergétique** selon architecture
- **Contraintes physiques** (pression eau, ascenseurs)
- **Variations météorologiques** tropicales

---

## Exemples Concrets

### Exemple 1 : Bâtiment Résidentiel

**Caractéristiques :**
- Surface sol : 120 m²
- Étages : 2
- Géométrie : rectangulaire (shape_factor = 1.1)

**Calculs Électricité :**
```
Surface totale = 120 × 2 = 240 m²
Base journalière = 0.8 kWh/m²/jour × 240 m² = 192 kWh/jour
Facteur étages = 1.0 + (2-1) × 0.05 = 1.05
Facteur forme = 1.0 + (1.1-1.0) × 0.05 = 1.005
Consommation ajustée = 192 × 1.05 × 1.005 = 202.6 kWh/jour
Base horaire = 202.6 ÷ 24 = 8.44 kWh/h

Variations horaires :
- Nuit (3h) : 8.44 × 0.3 = 2.5 kWh/h
- Matin (7h) : 8.44 × 1.5 = 12.7 kWh/h
- Soir (20h) : 8.44 × 1.5 = 12.7 kWh/h
```

**Calculs Eau :**
```
Base journalière = 150 L/m²/jour × 240 m² = 36,000 L/jour
Facteur étages = 1.0 + (2-1) × 0.1 = 1.1
Facteur pression = 1.0 + (2-1) × 0.05 = 1.05
Consommation ajustée = 36,000 × 1.1 × 1.05 = 41,580 L/jour
Base horaire = 41,580 ÷ 24 = 1,732 L/h

Variations horaires :
- Nuit (3h) : 1,732 × 0.2 = 346 L/h
- Douches matin (7h) : 1,732 × 2.0 = 3,464 L/h
- Douches soir (19h) : 1,732 × 1.8 = 3,118 L/h
```

### Exemple 2 : Tour de Bureaux

**Caractéristiques :**
- Surface sol : 400 m²
- Étages : 8
- Géométrie : carrée (shape_factor = 1.0)

**Calculs Électricité :**
```
Surface totale = 400 × 8 = 3,200 m²
Base journalière = 2.0 kWh/m²/jour × 3,200 m² = 6,400 kWh/jour
Facteur étages = 1.0 + (8-1) × 0.08 = 1.56 (ascenseurs)
Facteur taille = 0.95 (économies d'échelle)
Consommation ajustée = 6,400 × 1.56 × 0.95 = 9,497 kWh/jour
Base horaire = 9,497 ÷ 24 = 396 kWh/h

Variations :
- Nuit : 396 × 0.2 = 79 kWh/h
- Heures bureau : 396 × 1.8 = 713 kWh/h
- Pic ascenseurs (8h-9h) : 713 × 1.3 = 927 kWh/h
```

**Calculs Eau :**
```
Base journalière = 60 L/m²/jour × 3,200 m² = 192,000 L/jour
Facteur étages = 1.0 + (8-1) × 0.12 = 1.84
Facteur pression = 1.0 + (8-1) × 0.05 = 1.35 (système haute pression)
Consommation ajustée = 192,000 × 1.84 × 1.35 = 477,408 L/jour
Base horaire = 477,408 ÷ 24 = 19,892 L/h

Variations :
- Nuit : 19,892 × 0.1 = 1,989 L/h
- Heures bureau : 19,892 × 1.5 = 29,838 L/h
```

### Exemple 3 : Impact Saisonnier

**Même bâtiment résidentiel en saisons différentes :**

**Saison sèche (juillet) :**
```
Facteur saisonnier = 1.3 (plus de climatisation)
Électricité : 8.44 × 1.3 = 10.97 kWh/h (base)
Eau : 1,732 × 1.4 = 2,425 L/h (base)
```

**Saison des pluies (décembre) :**
```
Facteur saisonnier électricité = 0.9 (moins de climatisation)
Facteur saisonnier eau = 0.8 (eau de pluie disponible)
Électricité : 8.44 × 0.9 = 7.60 kWh/h (base)
Eau : 1,732 × 0.8 = 1,386 L/h (base)
```

---

## Validation et Cohérence

### Vérifications Automatiques

1. **Limites physiques** : Consommations dans des plages réalistes
2. **Cohérence temporelle** : Variations logiques selon l'heure
3. **Cohérence géométrique** : Surface polygone vs estimation
4. **Score de qualité** : Évaluation 0-1 de la fiabilité des données

### Comparaison Standards Malaysia

Les valeurs générées sont calibrées selon :
- Standards énergétiques Malaysia (MS 1525)
- Données climatiques officielles MetMalaysia
- Consommations types secteur résidentiel/commercial
- Études d'efficacité énergétique tropicale

---

## Formats de Sortie

### Structure des Fichiers CSV

#### 1. Métadonnées Bâtiments
```csv
unique_id,building_type,latitude,longitude,surface_area_m2,floors_count,has_precise_geometry
RKL_A1B2C3,residential,3.1390,101.6869,120.5,2,true
```

#### 2. Consommation Électrique
```csv
unique_id,timestamp,y,frequency
RKL_A1B2C3,2024-01-01 00:00:00,2.532,1H
RKL_A1B2C3,2024-01-01 01:00:00,2.187,1H
```

#### 3. Consommation Eau
```csv
unique_id,timestamp,y,frequency
RKL_A1B2C3,2024-01-01 00:00:00,346.2,1H
RKL_A1B2C3,2024-01-01 07:00:00,3464.1,1H
```

#### 4. Données Météorologiques (33 colonnes)
```csv
timestamp,temperature_2m,relative_humidity_2m,precipitation,location_id
2024-01-01 00:00:00,25.2,0.83,0.0,1
```

---

## Notes Techniques

### Performance
- **91,000 bâtiments** traités en ~12 secondes
- **630,000+ points** de consommation générés
- Optimisations pour gros volumes de données

### Précision
- Géométrie OSM précise quand disponible
- Fallback intelligent pour données manquantes
- Variations aléatoires réalistes (±10-15%)

### Extensibilité
- Architecture modulaire pour nouveaux types
- Paramètres climatiques configurables
- Facteurs d'ajustement personnalisables

---

*Ce guide détaille l'ensemble des calculs utilisés par le Malaysia Electricity Generator v3.1.0 Enhanced*