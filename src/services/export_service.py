#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SERVICE D'EXPORT AMÉLIORÉ AVEC GÉOMÉTRIE - COUCHE SERVICE
=========================================================

Service métier pour orchestrer l'export des données améliorées avec géométrie précise.
Compatible avec les générateurs electricity_generator.py et water_generator.py
"""

import logging
from typing import Dict, List, Optional
from datetime import datetime
import pandas as pd

from src.core.data_exporter import DataExporter
from src.utils.validators import validate_export_format
from src.utils.helpers import generate_unique_id

logger = logging.getLogger(__name__)


class EnhancedExportService:
    """Service métier pour l'export de données améliorées avec géométrie"""
    
    def __init__(self):
        """Initialise le service d'export amélioré"""
        self.data_exporter = DataExporter()
        self.export_sessions = []
        logger.info("✅ EnhancedExportService initialisé avec support géométrique")
    
    def export_all_datasets(
        self,
        buildings: List[Dict],
        consumption_data: Optional[pd.DataFrame],
        weather_data: Optional[pd.DataFrame],
        water_data: Optional[pd.DataFrame] = None,
        export_format: str = 'csv',
        base_filename: str = None
    ) -> Dict:
        """
        Exporte tous les datasets avec préparation des données géométriques améliorées
        
        Args:
            buildings: Liste des bâtiments avec géométrie précise et étages
            consumption_data: DataFrame de consommation électrique (peut être None)
            weather_data: DataFrame météo (peut être None)
            water_data: DataFrame consommation eau (peut être None)
            export_format: Format d'export
            base_filename: Nom de base optionnel
            
        Returns:
            Dict: Résultat de l'export amélioré
        """
        session_id = generate_unique_id('export_enhanced')
        start_time = datetime.now()
        
        try:
            logger.info(f"📤 Session export améliorée: {session_id}")
            
            # Analyse des données disponibles
            datasets_info = self._analyze_available_datasets(
                buildings, consumption_data, weather_data, water_data
            )
            
            logger.info(f"📊 Export amélioré: {datasets_info['summary']}")
            
            # Validation du format
            if not validate_export_format(export_format):
                return {
                    'success': False,
                    'error': f"Format non supporté: {export_format}",
                    'session_id': session_id
                }
            
            # Préparation des DataFrames améliorés
            dataframes_result = self._prepare_enhanced_export_dataframes(
                buildings, consumption_data, weather_data, water_data
            )
            
            if not dataframes_result['success']:
                return {
                    'success': False,
                    'error': dataframes_result['error'],
                    'session_id': session_id
                }
            
            buildings_df = dataframes_result['buildings_df']
            consumption_df = dataframes_result['consumption_df']
            weather_df = dataframes_result['weather_df']
            water_df = dataframes_result.get('water_df', pd.DataFrame())
            
            # Export via DataExporter
            export_result = self.data_exporter.export_four_datasets(
                buildings_df=buildings_df,
                consumption_df=consumption_df,
                weather_df=weather_df,
                water_df=water_df,
                export_format=export_format,
                base_filename=base_filename
            )
            
            if export_result['success']:
                # Enregistrement de la session améliorée
                export_time = (datetime.now() - start_time).total_seconds()
                
                session_info = {
                    'session_id': session_id,
                    'export_time': start_time.isoformat(),
                    'export_duration_seconds': export_time,
                    'export_format': export_format,
                    'enhanced_features': True,
                    'geometry_included': True,
                    'buildings_count': len(buildings),
                    'consumption_points': len(consumption_df) if not consumption_df.empty else 0,
                    'weather_points': len(weather_df) if not weather_df.empty else 0,
                    'water_points': len(water_df) if not water_df.empty else 0,
                    'files_created': export_result['metadata']['total_files'],
                    'total_size_mb': export_result['metadata']['total_size_mb'],
                    'datasets_analysis': datasets_info,
                    'enhanced_metadata': dataframes_result.get('enhanced_metadata', {})
                }
                
                self.export_sessions.append(session_info)
                
                # Garde seulement les 15 dernières sessions
                if len(self.export_sessions) > 15:
                    self.export_sessions = self.export_sessions[-15:]
                
                # Enrichissement du résultat
                export_result['session_id'] = session_id
                export_result['session_info'] = session_info
                export_result['enhanced_features_exported'] = True
                
                logger.info(f"✅ Export amélioré {session_id} terminé: {export_result['metadata']['total_files']} fichiers")
            
            return export_result
            
        except Exception as e:
            logger.error(f"❌ Erreur service export amélioré: {e}")
            return {
                'success': False,
                'error': str(e),
                'session_id': session_id
            }
    
    def _analyze_available_datasets(
        self,
        buildings: List[Dict],
        consumption_data: Optional[pd.DataFrame],
        weather_data: Optional[pd.DataFrame],
        water_data: Optional[pd.DataFrame]
    ) -> Dict:
        """
        Analyse les datasets disponibles pour l'export
        
        Args:
            buildings: Liste des bâtiments
            consumption_data: DataFrame consommation électrique
            weather_data: DataFrame météo
            water_data: DataFrame consommation eau
            
        Returns:
            Dict: Analyse des datasets
        """
        analysis = {
            'buildings': {
                'count': len(buildings) if buildings else 0,
                'with_geometry': 0,
                'with_floors': 0,
                'geometry_types': {},
                'available': len(buildings) > 0 if buildings else False
            },
            'consumption': {
                'points': len(consumption_data) if consumption_data is not None and not consumption_data.empty else 0,
                'available': consumption_data is not None and not consumption_data.empty
            },
            'water': {
                'points': len(water_data) if water_data is not None and not water_data.empty else 0,
                'available': water_data is not None and not water_data.empty
            },
            'weather': {
                'points': len(weather_data) if weather_data is not None and not weather_data.empty else 0,
                'available': weather_data is not None and not weather_data.empty
            }
        }
        
        # Analyse géométrique des bâtiments
        if buildings:
            for building in buildings:
                # Géométrie précise
                if building.get('has_precise_geometry', False):
                    analysis['buildings']['with_geometry'] += 1
                
                # Données d'étages
                if building.get('floors_count', 1) > 1:
                    analysis['buildings']['with_floors'] += 1
                
                # Types géométriques
                geom_source = building.get('geometry_source', 'unknown')
                analysis['buildings']['geometry_types'][geom_source] = analysis['buildings']['geometry_types'].get(geom_source, 0) + 1
        
        # Résumé textuel
        available_datasets = []
        if analysis['buildings']['available']:
            geom_info = f" ({analysis['buildings']['with_geometry']} avec géométrie)" if analysis['buildings']['with_geometry'] > 0 else ""
            available_datasets.append(f"{analysis['buildings']['count']} bâtiments{geom_info}")
        
        if analysis['consumption']['available']:
            available_datasets.append(f"{analysis['consumption']['points']} points électricité")
        
        if analysis['water']['available']:
            available_datasets.append(f"{analysis['water']['points']} points eau")
        
        if analysis['weather']['available']:
            available_datasets.append(f"{analysis['weather']['points']} points météo")
        
        analysis['summary'] = ', '.join(available_datasets) if available_datasets else 'Aucune donnée'
        
        return analysis
    
    def _prepare_enhanced_export_dataframes(
        self,
        buildings: List[Dict],
        consumption_data: Optional[pd.DataFrame],
        weather_data: Optional[pd.DataFrame],
        water_data: Optional[pd.DataFrame] = None
    ) -> Dict:
        """
        Prépare les DataFrames pour l'export avec enrichissement géométrique
        
        Args:
            buildings: Liste des bâtiments avec géométrie
            consumption_data: DataFrame de consommation électrique (optionnel)
            weather_data: DataFrame météo (optionnel)
            water_data: DataFrame de consommation eau (optionnel)
            
        Returns:
            Dict: DataFrames préparés pour export amélioré
        """
        try:
            # 1. Préparation DataFrame bâtiments amélioré
            if not buildings:
                return {
                    'success': False,
                    'error': 'Aucun bâtiment à exporter'
                }
            
            buildings_df = self._prepare_enhanced_buildings_dataframe(buildings)
            enhanced_metadata = self._extract_enhanced_metadata(buildings)
            
            # 2. Préparation DataFrame consommation électrique
            if consumption_data is not None and not consumption_data.empty:
                consumption_df = self._prepare_consumption_dataframe(consumption_data)
            else:
                consumption_df = pd.DataFrame()
                logger.warning("⚠️ Aucune donnée de consommation électrique à exporter")
            
            # 3. Préparation DataFrame météo
            if weather_data is not None and not weather_data.empty:
                weather_df = self._prepare_weather_dataframe(weather_data)
            else:
                weather_df = pd.DataFrame()
                logger.warning("⚠️ Aucune donnée météo à exporter")
            
            # 4. Préparation DataFrame eau
            if water_data is not None and not water_data.empty:
                water_df = self._prepare_water_dataframe(water_data)
                logger.info(f"💧 DataFrame eau préparé: {len(water_df)} points")
            else:
                water_df = pd.DataFrame()
                logger.info("ℹ️ Aucune donnée eau à exporter (optionnel)")
            
            logger.info(f"📋 DataFrames améliorés préparés: {len(buildings_df)} bâtiments enrichis, "
                       f"{len(consumption_df)} électricité, {len(weather_df)} météo, "
                       f"{len(water_df)} eau")
            
            return {
                'success': True,
                'buildings_df': buildings_df,
                'consumption_df': consumption_df,
                'weather_df': weather_df,
                'water_df': water_df,
                'enhanced_metadata': enhanced_metadata
            }
            
        except Exception as e:
            logger.error(f"❌ Erreur préparation DataFrames améliorés: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _prepare_enhanced_buildings_dataframe(self, buildings: List[Dict]) -> pd.DataFrame:
        """
        Prépare le DataFrame des métadonnées de bâtiments avec géométrie enrichie
        
        Args:
            buildings: Liste des bâtiments avec géométrie
            
        Returns:
            pd.DataFrame: DataFrame des bâtiments enrichi
        """
        # Conversion en DataFrame
        df = pd.DataFrame(buildings)
        
        # Colonnes pour export amélioré avec géométrie
        enhanced_export_columns = [
            # Identifiants
            'unique_id',
            'osm_id',
            
            # Localisation
            'latitude',
            'longitude',
            'zone_name',
            
            # Type et usage
            'building_type',
            'building_subtype',
            'building_use',
            
            # Géométrie et surface
            'surface_area_m2',
            'polygon_area_m2',
            'polygon_perimeter_m',
            'shape_complexity',
            'has_precise_geometry',
            'geometry_source',
            
            # Étages et structure
            'floors_count',
            'building_levels',
            'levels_source',
            'levels_confidence',
            'height_m',
            'roof_levels',
            
            # Construction
            'construction_material',
            'construction_year',
            'roof_material',
            
            # Qualité et source
            'validation_score',
            'source',
            'osm_type',
            'osm_timestamp',
            'osm_version'
        ]
        
        # Garder seulement les colonnes existantes
        available_columns = [col for col in enhanced_export_columns if col in df.columns]
        df_export = df[available_columns].copy()
        
        # Nettoyage et formatage
        if 'latitude' in df_export.columns:
            df_export['latitude'] = df_export['latitude'].round(6)
        
        if 'longitude' in df_export.columns:
            df_export['longitude'] = df_export['longitude'].round(6)
        
        if 'surface_area_m2' in df_export.columns:
            df_export['surface_area_m2'] = df_export['surface_area_m2'].round(1)
        
        if 'polygon_area_m2' in df_export.columns:
            df_export['polygon_area_m2'] = df_export['polygon_area_m2'].round(1)
        
        if 'polygon_perimeter_m' in df_export.columns:
            df_export['polygon_perimeter_m'] = df_export['polygon_perimeter_m'].round(1)
        
        if 'shape_complexity' in df_export.columns:
            df_export['shape_complexity'] = df_export['shape_complexity'].round(3)
        
        if 'validation_score' in df_export.columns:
            df_export['validation_score'] = df_export['validation_score'].round(3)
        
        # Tri par unique_id
        if 'unique_id' in df_export.columns:
            df_export = df_export.sort_values('unique_id').reset_index(drop=True)
        
        return df_export
    
    def _extract_enhanced_metadata(self, buildings: List[Dict]) -> Dict:
        """
        Extrait les métadonnées enrichies des bâtiments
        
        Args:
            buildings: Liste des bâtiments
            
        Returns:
            Dict: Métadonnées enrichies
        """
        if not buildings:
            return {}
        
        total_buildings = len(buildings)
        
        # Analyse géométrique
        with_precise_geometry = sum(1 for b in buildings if b.get('has_precise_geometry', False))
        with_floors_data = sum(1 for b in buildings if b.get('levels_confidence', 'low') != 'low')
        
        # Sources géométriques
        geometry_sources = {}
        for building in buildings:
            source = building.get('geometry_source', 'unknown')
            geometry_sources[source] = geometry_sources.get(source, 0) + 1
        
        # Sources d'étages
        floors_sources = {}
        for building in buildings:
            source = building.get('levels_source', 'unknown')
            floors_sources[source] = floors_sources.get(source, 0) + 1
        
        # Qualité validation
        validation_scores = [b.get('validation_score', 0) for b in buildings if b.get('validation_score') is not None]
        avg_validation = sum(validation_scores) / len(validation_scores) if validation_scores else 0
        
        # Surface et complexité
        surfaces = [b.get('polygon_area_m2', 0) for b in buildings if b.get('polygon_area_m2', 0) > 0]
        complexities = [b.get('shape_complexity', 1.0) for b in buildings if b.get('shape_complexity')]
        
        return {
            'geometry_analysis': {
                'total_buildings': total_buildings,
                'with_precise_geometry': with_precise_geometry,
                'geometry_coverage_rate': round(with_precise_geometry / total_buildings, 3),
                'geometry_sources': geometry_sources
            },
            'floors_analysis': {
                'with_floors_data': with_floors_data,
                'floors_data_rate': round(with_floors_data / total_buildings, 3),
                'floors_sources': floors_sources
            },
            'quality_analysis': {
                'average_validation_score': round(avg_validation, 3),
                'validation_samples': len(validation_scores)
            },
            'surface_analysis': {
                'samples_with_area': len(surfaces),
                'total_area_m2': round(sum(surfaces), 1) if surfaces else 0,
                'average_area_m2': round(sum(surfaces) / len(surfaces), 1) if surfaces else 0,
                'min_area_m2': round(min(surfaces), 1) if surfaces else 0,
                'max_area_m2': round(max(surfaces), 1) if surfaces else 0
            },
            'complexity_analysis': {
                'samples_with_complexity': len(complexities),
                'average_complexity': round(sum(complexities) / len(complexities), 3) if complexities else 1.0,
                'min_complexity': round(min(complexities), 3) if complexities else 1.0,
                'max_complexity': round(max(complexities), 3) if complexities else 1.0
            }
        }
    
    def _prepare_consumption_dataframe(self, consumption_data: pd.DataFrame) -> pd.DataFrame:
        """
        Prépare le DataFrame de consommation électrique pour export
        STRUCTURE: ['unique_id', 'timestamp', 'y', 'frequency']
        
        Args:
            consumption_data: DataFrame de consommation brut
            
        Returns:
            pd.DataFrame: DataFrame de consommation nettoyé
        """
        df = consumption_data.copy()
        
        # Sélection des colonnes pour export
        export_columns = [
            'unique_id',
            'timestamp', 
            'y',
            'frequency'
        ]
        
        # Garder seulement les colonnes existantes
        available_columns = [col for col in export_columns if col in df.columns]
        df_export = df[available_columns].copy()
        
        # Formatage consommation
        if 'y' in df_export.columns:
            df_export['y'] = df_export['y'].round(4)
        
        # Tri par unique_id puis timestamp
        if 'unique_id' in df_export.columns and 'timestamp' in df_export.columns:
            df_export = df_export.sort_values(['unique_id', 'timestamp']).reset_index(drop=True)
        
        return df_export
    
    def _prepare_water_dataframe(self, water_data: pd.DataFrame) -> pd.DataFrame:
        """
        Prépare le DataFrame de consommation d'eau pour export
        STRUCTURE: ['unique_id', 'timestamp', 'y', 'frequency']
        
        Args:
            water_data: DataFrame de consommation d'eau brut
            
        Returns:
            pd.DataFrame: DataFrame de consommation d'eau nettoyé
        """
        df = water_data.copy()
        
        # Sélection des colonnes pour export eau
        water_export_columns = [
            'unique_id',
            'timestamp',
            'y',
            'frequency'
        ]
        
        # Garder seulement les colonnes existantes
        available_columns = [col for col in water_export_columns if col in df.columns]
        df_export = df[available_columns].copy()
        
        # Formatage consommation eau
        if 'y' in df_export.columns:
            df_export['y'] = df_export['y'].round(4)
        
        # Tri par unique_id puis timestamp
        if 'unique_id' in df_export.columns and 'timestamp' in df_export.columns:
            df_export = df_export.sort_values(['unique_id', 'timestamp']).reset_index(drop=True)
        
        return df_export
    
    def _prepare_weather_dataframe(self, weather_data: pd.DataFrame) -> pd.DataFrame:
        """
        Prépare le DataFrame météorologique pour export (INCHANGÉ)
        
        Args:
            weather_data: DataFrame météo brut
            
        Returns:
            pd.DataFrame: DataFrame météo nettoyé
        """
        df = weather_data.copy()
        
        # Colonnes météo dans l'ordre spécifié (33 colonnes)
        weather_columns_order = [
            'timestamp', 'temperature_2m', 'relative_humidity_2m', 'dew_point_2m',
            'apparent_temperature', 'precipitation', 'rain', 'snowfall', 'snow_depth',
            'weather_code', 'pressure_msl', 'surface_pressure', 'cloud_cover',
            'cloud_cover_low', 'cloud_cover_mid', 'cloud_cover_high',
            'et0_fao_evapotranspiration', 'vapour_pressure_deficit', 'wind_speed_10m',
            'wind_direction_10m', 'wind_gusts_10m', 'soil_temperature_0_to_7cm',
            'soil_temperature_7_to_28cm', 'soil_moisture_0_to_7cm',
            'soil_moisture_7_to_28cm', 'is_day', 'sunshine_duration',
            'shortwave_radiation', 'direct_radiation', 'diffuse_radiation',
            'direct_normal_irradiance', 'terrestrial_radiation', 'location_id'
        ]
        
        # Garder seulement les colonnes existantes dans l'ordre
        available_columns = [col for col in weather_columns_order if col in df.columns]
        df_export = df[available_columns].copy()
        
        # Tri par location_id puis timestamp
        if 'location_id' in df_export.columns and 'timestamp' in df_export.columns:
            df_export = df_export.sort_values(['location_id', 'timestamp']).reset_index(drop=True)
        
        return df_export
    
    def export_enhanced_buildings_only(
        self,
        buildings: List[Dict],
        export_format: str = 'csv',
        filename: str = None
    ) -> Dict:
        """
        Exporte uniquement les métadonnées enrichies des bâtiments
        
        Args:
            buildings: Liste des bâtiments avec géométrie
            export_format: Format d'export
            filename: Nom de fichier optionnel
            
        Returns:
            Dict: Résultat de l'export
        """
        try:
            if not buildings:
                return {
                    'success': False,
                    'error': 'Aucun bâtiment à exporter'
                }
            
            # Préparation DataFrame enrichi
            buildings_df = self._prepare_enhanced_buildings_dataframe(buildings)
            
            # Nom de fichier
            if not filename:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f"enhanced_buildings_metadata_{timestamp}"
            
            # Export
            result = self.data_exporter.export_single_dataframe(
                df=buildings_df,
                filename=filename,
                export_format=export_format
            )
            
            # Enrichissement du résultat
            if result['success']:
                enhanced_metadata = self._extract_enhanced_metadata(buildings)
                result['enhanced_metadata'] = enhanced_metadata
                result['enhanced_features_exported'] = True
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Erreur export bâtiments enrichis: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def export_geometry_analysis(
        self,
        buildings: List[Dict],
        export_format: str = 'csv'
    ) -> Dict:
        """
        Exporte une analyse géométrique détaillée des bâtiments
        
        Args:
            buildings: Liste des bâtiments avec géométrie
            export_format: Format d'export
            
        Returns:
            Dict: Résultat de l'export d'analyse
        """
        try:
            if not buildings:
                return {
                    'success': False,
                    'error': 'Aucun bâtiment à analyser'
                }
            
            # Création DataFrame d'analyse géométrique
            analysis_data = []
            
            for building in buildings:
                analysis_record = {
                    'unique_id': building.get('unique_id', 'unknown'),
                    'building_type': building.get('building_type', 'unknown'),
                    'has_precise_geometry': building.get('has_precise_geometry', False),
                    'geometry_source': building.get('geometry_source', 'unknown'),
                    'geometry_points': len(building.get('geometry', [])),
                    'surface_area_m2': building.get('surface_area_m2', 0),
                    'polygon_area_m2': building.get('polygon_area_m2', 0),
                    'polygon_perimeter_m': building.get('polygon_perimeter_m', 0),
                    'shape_complexity': building.get('shape_complexity', 1.0),
                    'floors_count': building.get('floors_count', 1),
                    'levels_source': building.get('levels_source', 'unknown'),
                    'levels_confidence': building.get('levels_confidence', 'low'),
                    'validation_score': building.get('validation_score', 0),
                    'construction_year': building.get('construction_year'),
                    'construction_material': building.get('construction_material'),
                    'zone_name': building.get('zone_name', 'unknown')
                }
                
                # Calculs dérivés
                if analysis_record['polygon_area_m2'] > 0 and analysis_record['polygon_perimeter_m'] > 0:
                    # Indice de compacité (1.0 = cercle parfait)
                    area = analysis_record['polygon_area_m2']
                    perimeter = analysis_record['polygon_perimeter_m']
                    analysis_record['compactness_index'] = (4 * 3.14159 * area) / (perimeter ** 2)
                else:
                    analysis_record['compactness_index'] = None
                
                # Différence surface estimée vs calculée
                if analysis_record['surface_area_m2'] > 0 and analysis_record['polygon_area_m2'] > 0:
                    diff = abs(analysis_record['surface_area_m2'] - analysis_record['polygon_area_m2'])
                    analysis_record['surface_difference_percent'] = (diff / analysis_record['surface_area_m2']) * 100
                else:
                    analysis_record['surface_difference_percent'] = None
                
                # Surface totale des planchers
                analysis_record['total_floor_area_m2'] = analysis_record['polygon_area_m2'] * analysis_record['floors_count']
                
                analysis_data.append(analysis_record)
            
            # Création DataFrame
            analysis_df = pd.DataFrame(analysis_data)
            
            # Nom de fichier
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"geometry_analysis_{timestamp}"
            
            # Export
            result = self.data_exporter.export_single_dataframe(
                df=analysis_df,
                filename=filename,
                export_format=export_format
            )
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Erreur export analyse géométrique: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_export_summary(self) -> Dict:
        """
        Retourne un résumé des exports améliorés
        
        Returns:
            Dict: Résumé des statistiques d'export améliorées
        """
        # Statistiques du service
        service_stats = {
            'total_export_sessions': len(self.export_sessions),
            'enhanced_export_sessions': sum(1 for s in self.export_sessions if s.get('enhanced_features', False)),
            'recent_sessions': self.export_sessions[-5:] if self.export_sessions else []
        }
        
        # Analyse des sessions améliorées
        if self.export_sessions:
            enhanced_sessions = [s for s in self.export_sessions if s.get('enhanced_features', False)]
            
            if enhanced_sessions:
                total_enhanced_buildings = sum(s.get('buildings_count', 0) for s in enhanced_sessions)
                total_enhanced_size = sum(s.get('total_size_mb', 0) for s in enhanced_sessions)
                
                service_stats['enhanced_statistics'] = {
                    'total_enhanced_buildings_exported': total_enhanced_buildings,
                    'total_enhanced_size_mb': round(total_enhanced_size, 2),
                    'average_buildings_per_session': round(total_enhanced_buildings / len(enhanced_sessions), 1),
                    'geometry_features_exported': True,
                    'floors_metadata_exported': True
                }
        
        # Statistiques de l'exporteur
        exporter_stats = self.data_exporter.get_export_statistics()
        
        # Fichiers disponibles
        available_files = self.data_exporter.list_exported_files()
        
        return {
            'service_statistics': service_stats,
            'exporter_statistics': exporter_stats,
            'available_files': available_files[:10],  # Limite aux 10 plus récents
            'supported_formats': ['csv', 'parquet', 'xlsx'],
            'enhanced_features': {
                'geometry_export': True,
                'floors_metadata_export': True,
                'construction_metadata_export': True,
                'quality_scoring_export': True,
                'enhanced_buildings_analysis': True
            }
        }