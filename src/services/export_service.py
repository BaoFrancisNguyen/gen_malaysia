    def export_all_datasets(
        self,
        buildings: List[Dict],
        consumption_data: Optional[pd.DataFrame],
        weather_data: Optional[pd.DataFrame],
        water_data: Optional[pd.DataFrame] = None,  # Nouveau paramètre eau
        export_format: str = 'csv',
        base_filename: str = None
    ) -> Dict:
        """
        Exporte tous les datasets avec préparation des données (4 fichiers possibles)
        
        Args:
            buildings: Liste des bâtiments
            consumption_data: DataFrame de consommation électrique (peut être None)
            weather_data: DataFrame météo (peut être None)
            water_data: DataFrame consommation eau (peut être None)
            export_format: Format d'export
            base_filename: Nom de base optionnel
            
        Returns:
            Dict: Résultat de l'export
        """
        session_id = generate_unique_id('export')
        start_time = datetime.now()
        
        try:
            logger.info(f"📤 Session export: {session_id}")
            datasets_info = f"{len(buildings)} bâtiments"
            if consumption_data is not None and not consumption_data.empty:
                datasets_info += f", {len(consumption_data)} points électricité"
            if weather_data is not None and not weather_data.empty:
                datasets_info += f", {len(weather_data)} points météo"
            if water_data is not None and not water_data.empty:
                datasets_info += f", {len(water_data)} points eau"
            
            logger.info(f"📊 Export: {datasets_info}, format {export_format}")
            
            # Validation du format
            if not validate_export_format(export_format):
                return {
                    'success': False,
                    'error': f"Format non supporté: {export_format}",
                    'session_id': session_id
                }
            
            # Préparation des DataFrames
            dataframes_result = self._prepare_export_dataframes(
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
            
            # Export via DataExporter (mise à jour pour 4 fichiers)
            export_result = self.data_exporter.export_four_datasets(
                buildings_df=buildings_df,
                consumption_df=consumption_df,
                weather_df=weather_df,
                water_df=water_df,
                export_format=export_format,
                base_filename=base_filename
            )
            
            if export_result['success']:
                # Enregistrement de la session
                export_time = (datetime.now() - start_time).total_seconds()
                
                session_info = {
                    'session_id': session_id,
                    'export_time': start_time.isoformat(),
                    'export_duration_seconds': export_time,
                    'export_format': export_format,
                    'buildings_count': len(buildings),
                    'consumption_points': len(consumption_df) if not consumption_df.empty else 0,
                    'weather_points': len(weather_df) if not weather_df.empty else 0,
                    'water_points': len(water_df) if not water_df.empty else 0,
                    'files_created': export_result['metadata']['total_files'],
                    'total_size_mb': export_result['metadata']['total_size_mb']
                }
                
                self.export_sessions.append(session_info)
                
                # Garde seulement les 15 dernières sessions
                if len(self.export_sessions) > 15:
                    self.export_sessions = self.export_sessions[-15:]
                
                # Enrichissement du résultat
                export_result['session_id'] = session_id
                export_result['session_info'] = session_info
                
                logger.info(f"✅ Export {session_id} terminé: {export_result['metadata']['total_files']} fichiers")
            
            return export_result
            
        except Exception as e:
            logger.error(f"❌ Erreur service export: {e}")
            return {
                'success': False,
                'error': str(e),
                'session_id': session_id
            }
    
    def _prepare_export_dataframes(
        self,
        buildings: List[Dict],
        consumption_data: Optional[pd.DataFrame],
        weather_data: Optional[pd.DataFrame],
        water_data: Optional[pd.DataFrame] = None
    ) -> Dict:
        """
        Prépare les DataFrames pour l'export (maintenant avec eau)
        
        Args:
            buildings: Liste des bâtiments
            consumption_data: DataFrame de consommation électrique (optionnel)
            weather_data: DataFrame météo (optionnel)
            water_data: DataFrame de consommation eau (optionnel)
            
        Returns:
            Dict: DataFrames préparés pour export
        """
        try:
            # 1. Préparation DataFrame bâtiments
            if not buildings:
                return {
                    'success': False,
                    'error': 'Aucun bâtiment à exporter'
                }
            
            buildings_df = self._prepare_buildings_dataframe(buildings)
            
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
            
            # 4. Préparation DataFrame eau (NOUVEAU)
            if water_data is not None and not water_data.empty:
                water_df = self._prepare_water_dataframe(water_data)
                logger.info(f"💧 DataFrame eau préparé: {len(water_df)} points")
            else:
                water_df = pd.DataFrame()
                logger.info("ℹ️ Aucune donnée eau à exporter (optionnel)")
            
            logger.info(f"📋 DataFrames préparés: {len(buildings_df)} bâtiments, "
                       f"{len(consumption_df)} électricité, {len(weather_df)} météo, "
                       f"{len(water_df)} eau")
            
            return {
                'success': True,
                'buildings_df': buildings_df,
                'consumption_df': consumption_df,
                'weather_df': weather_df,
                'water_df': water_df
            }
            
        except Exception as e:
            logger.error(f"❌ Erreur préparation DataFrames: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _prepare_water_dataframe(self, water_data: pd.DataFrame) -> pd.DataFrame:
        """
        Prépare le DataFrame de consommation d'eau pour export
        
        Args:
            water_data: DataFrame de consommation d'eau brut
            
        Returns:
            pd.DataFrame: DataFrame de consommation d'eau nettoyé
        """
        df = water_data.copy()
        
        # Sélection des colonnes pour export eau
        water_export_columns = [
            'building_id',
            'timestamp',
            'water_consumption_liters',
            'building_type',
            'surface_area_m2',
            'consumption_intensity_l_m2'
        ]
        
        # Garder seulement les colonnes existantes
        available_columns = [col for col in water_export_columns if col in df.columns]
        df_export = df[available_columns].copy()
        
        # Formatage consommation eau
        if 'water_consumption_liters' in df_export.columns:
            df_export['water_consumption_liters'] = df_export['water_consumption_liters'].round(2)
        
        # Formatage intensité eau
        if 'consumption_intensity_l_m2' in df_export.columns:
            df_export['consumption_intensity_l_m2'] = df_export['consumption_intensity_l_m2'].round(4)
        
        # Formatage surface
        if 'surface_area_m2' in df_export.columns:
            df_export['surface_area_m2'] = df_export['surface_area_m2'].round(1)
        
        # Tri par building_id puis timestamp
        if 'building_id' in df_export.columns and 'timestamp' in df_export.columns:
            df_export = df_export.sort_values(['building_id', 'timestamp']).reset_index(drop=True)
        
        return df_export#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SERVICE D'EXPORT - COUCHE SERVICE
=================================

Service métier pour orchestrer l'export des données.
Prépare les DataFrames et coordonne l'export via DataExporter.
"""

import logging
from typing import Dict, List, Optional
from datetime import datetime
import pandas as pd

from src.core.data_exporter import DataExporter
from src.utils.validators import validate_export_format
from src.utils.helpers import generate_unique_id

logger = logging.getLogger(__name__)


class ExportService:
    """Service métier pour l'export de données"""
    
    def __init__(self):
        """Initialise le service d'export"""
        self.data_exporter = DataExporter()
        self.export_sessions = []
        logger.info("✅ ExportService initialisé")
    
    def export_all_datasets(
        self,
        buildings: List[Dict],
        consumption_data: Optional[pd.DataFrame],
        weather_data: Optional[pd.DataFrame],
        export_format: str = 'csv',
        base_filename: str = None
    ) -> Dict:
        """
        Exporte tous les datasets avec préparation des données
        
        Args:
            buildings: Liste des bâtiments
            consumption_data: DataFrame de consommation (peut être None)
            weather_data: DataFrame météo (peut être None)
            export_format: Format d'export
            base_filename: Nom de base optionnel
            
        Returns:
            Dict: Résultat de l'export
        """
        session_id = generate_unique_id('export')
        start_time = datetime.now()
        
        try:
            logger.info(f"📤 Session export: {session_id}")
            logger.info(f"📊 Export: {len(buildings)} bâtiments, format {export_format}")
            
            # Validation du format
            if not validate_export_format(export_format):
                return {
                    'success': False,
                    'error': f"Format non supporté: {export_format}",
                    'session_id': session_id
                }
            
            # Préparation des DataFrames
            dataframes_result = self._prepare_export_dataframes(
                buildings, consumption_data, weather_data
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
            
            # Export via DataExporter
            export_result = self.data_exporter.export_three_datasets(
                buildings_df=buildings_df,
                consumption_df=consumption_df,
                weather_df=weather_df,
                export_format=export_format,
                base_filename=base_filename
            )
            
            if export_result['success']:
                # Enregistrement de la session
                export_time = (datetime.now() - start_time).total_seconds()
                
                session_info = {
                    'session_id': session_id,
                    'export_time': start_time.isoformat(),
                    'export_duration_seconds': export_time,
                    'export_format': export_format,
                    'buildings_count': len(buildings),
                    'consumption_points': len(consumption_df) if not consumption_df.empty else 0,
                    'weather_points': len(weather_df) if not weather_df.empty else 0,
                    'files_created': export_result['metadata']['total_files'],
                    'total_size_mb': export_result['metadata']['total_size_mb']
                }
                
                self.export_sessions.append(session_info)
                
                # Garde seulement les 15 dernières sessions
                if len(self.export_sessions) > 15:
                    self.export_sessions = self.export_sessions[-15:]
                
                # Enrichissement du résultat
                export_result['session_id'] = session_id
                export_result['session_info'] = session_info
                
                logger.info(f"✅ Export {session_id} terminé: {export_result['metadata']['total_files']} fichiers")
            
            return export_result
            
        except Exception as e:
            logger.error(f"❌ Erreur service export: {e}")
            return {
                'success': False,
                'error': str(e),
                'session_id': session_id
            }
    
    def _prepare_export_dataframes(
        self,
        buildings: List[Dict],
        consumption_data: Optional[pd.DataFrame],
        weather_data: Optional[pd.DataFrame]
    ) -> Dict:
        """
        Prépare les DataFrames pour l'export
        
        Args:
            buildings: Liste des bâtiments
            consumption_data: DataFrame de consommation (optionnel)
            weather_data: DataFrame météo (optionnel)
            
        Returns:
            Dict: DataFrames préparés pour export
        """
        try:
            # 1. Préparation DataFrame bâtiments
            if not buildings:
                return {
                    'success': False,
                    'error': 'Aucun bâtiment à exporter'
                }
            
            buildings_df = self._prepare_buildings_dataframe(buildings)
            
            # 2. Préparation DataFrame consommation
            if consumption_data is not None and not consumption_data.empty:
                consumption_df = self._prepare_consumption_dataframe(consumption_data)
            else:
                consumption_df = pd.DataFrame()  # DataFrame vide
                logger.warning("⚠️ Aucune donnée de consommation à exporter")
            
            # 3. Préparation DataFrame météo
            if weather_data is not None and not weather_data.empty:
                weather_df = self._prepare_weather_dataframe(weather_data)
            else:
                weather_df = pd.DataFrame()  # DataFrame vide
                logger.warning("⚠️ Aucune donnée météo à exporter")
            
            logger.info(f"📋 DataFrames préparés: {len(buildings_df)} bâtiments, "
                       f"{len(consumption_df)} consommation, {len(weather_df)} météo")
            
            return {
                'success': True,
                'buildings_df': buildings_df,
                'consumption_df': consumption_df,
                'weather_df': weather_df
            }
            
        except Exception as e:
            logger.error(f"❌ Erreur préparation DataFrames: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _prepare_buildings_dataframe(self, buildings: List[Dict]) -> pd.DataFrame:
        """
        Prépare le DataFrame des métadonnées de bâtiments pour export
        
        Args:
            buildings: Liste des bâtiments
            
        Returns:
            pd.DataFrame: DataFrame des bâtiments nettoyé
        """
        # Conversion en DataFrame
        df = pd.DataFrame(buildings)
        
        # Sélection et ordre des colonnes pour export
        export_columns = [
            'id',
            'building_type',
            'zone_name',
            'latitude',
            'longitude',
            'surface_area_m2',
            'osm_id',
            'source',
            'extracted_at'
        ]
        
        # Garder seulement les colonnes existantes
        available_columns = [col for col in export_columns if col in df.columns]
        df_export = df[available_columns].copy()
        
        # Nettoyage et formatage
        if 'latitude' in df_export.columns:
            df_export['latitude'] = df_export['latitude'].round(6)
        
        if 'longitude' in df_export.columns:
            df_export['longitude'] = df_export['longitude'].round(6)
        
        if 'surface_area_m2' in df_export.columns:
            df_export['surface_area_m2'] = df_export['surface_area_m2'].round(1)
        
        # Conversion timestamp si nécessaire
        if 'extracted_at' in df_export.columns:
            try:
                if df_export['extracted_at'].dtype == 'object':
                    df_export['extracted_at'] = pd.to_datetime(df_export['extracted_at'], errors='coerce')
            except:
                pass
        
        # Tri par ID
        df_export = df_export.sort_values('id').reset_index(drop=True)
        
        return df_export
    
    def _prepare_consumption_dataframe(self, consumption_data: pd.DataFrame) -> pd.DataFrame:
        """
        Prépare le DataFrame de consommation électrique pour export
        
        Args:
            consumption_data: DataFrame de consommation brut
            
        Returns:
            pd.DataFrame: DataFrame de consommation nettoyé
        """
        df = consumption_data.copy()
        
        # Sélection des colonnes pour export
        export_columns = [
            'building_id',
            'timestamp',
            'consumption_kwh',
            'building_type',
            'surface_area_m2'
        ]
        
        # Garder seulement les colonnes existantes
        available_columns = [col for col in export_columns if col in df.columns]
        df_export = df[available_columns].copy()
        
        # Formatage consommation
        if 'consumption_kwh' in df_export.columns:
            df_export['consumption_kwh'] = df_export['consumption_kwh'].round(4)
        
        # Formatage surface
        if 'surface_area_m2' in df_export.columns:
            df_export['surface_area_m2'] = df_export['surface_area_m2'].round(1)
        
        # Tri par building_id puis timestamp
        if 'building_id' in df_export.columns and 'timestamp' in df_export.columns:
            df_export = df_export.sort_values(['building_id', 'timestamp']).reset_index(drop=True)
        
        return df_export
    
    def _prepare_weather_dataframe(self, weather_data: pd.DataFrame) -> pd.DataFrame:
        """
        Prépare le DataFrame météorologique pour export
        
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
    
    def export_buildings_only(
        self,
        buildings: List[Dict],
        export_format: str = 'csv',
        filename: str = None
    ) -> Dict:
        """
        Exporte uniquement les métadonnées des bâtiments
        
        Args:
            buildings: Liste des bâtiments
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
            
            # Préparation DataFrame
            buildings_df = self._prepare_buildings_dataframe(buildings)
            
            # Nom de fichier
            if not filename:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f"buildings_metadata_{timestamp}"
            
            # Export
            result = self.data_exporter.export_single_dataframe(
                df=buildings_df,
                filename=filename,
                export_format=export_format
            )
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Erreur export bâtiments: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_export_summary(self) -> Dict:
        """
        Retourne un résumé des exports
        
        Returns:
            Dict: Résumé des statistiques d'export
        """
        # Statistiques du service
        service_stats = {
            'total_export_sessions': len(self.export_sessions),
            'recent_sessions': self.export_sessions[-5:] if self.export_sessions else []
        }
        
        # Statistiques de l'exporteur
        exporter_stats = self.data_exporter.get_export_statistics()
        
        # Fichiers disponibles
        available_files = self.data_exporter.list_exported_files()
        
        return {
            'service_statistics': service_stats,
            'exporter_statistics': exporter_stats,
            'available_files': available_files[:10],  # Limite aux 10 plus récents
            'export_directory': str(self.data_exporter.export_directory) if hasattr(self.data_exporter, 'export_directory') else 'exports/',
            'supported_formats': ['csv', 'parquet', 'xlsx']
        }
    
    def validate_export_request(
        self,
        buildings: List[Dict],
        export_format: str,
        consumption_data: Optional[pd.DataFrame] = None,
        weather_data: Optional[pd.DataFrame] = None
    ) -> Dict:
        """
        Valide une demande d'export
        
        Args:
            buildings: Liste des bâtiments
            export_format: Format d'export
            consumption_data: DataFrame de consommation (optionnel)
            weather_data: DataFrame météo (optionnel)
            
        Returns:
            Dict: Résultat de validation
        """
        errors = []
        warnings = []
        
        # Validation format
        if not validate_export_format(export_format):
            errors.append(f"Format non supporté: {export_format}")
        
        # Validation bâtiments
        if not buildings:
            errors.append("Aucun bâtiment à exporter")
        elif len(buildings) > 50000:
            warnings.append("Nombre très élevé de bâtiments (>50k), export peut être lent")
        
        # Validation données optionnelles
        if consumption_data is not None and not consumption_data.empty:
            if len(consumption_data) > 1000000:
                warnings.append("Très grand volume de données de consommation (>1M points)")
        
        if weather_data is not None and not weather_data.empty:
            if len(weather_data) > 500000:
                warnings.append("Très grand volume de données météo (>500k points)")
        
        # Estimation de la taille
        estimated_size_mb = self._estimate_export_size(
            len(buildings),
            len(consumption_data) if consumption_data is not None else 0,
            len(weather_data) if weather_data is not None else 0,
            export_format
        )
        
        if estimated_size_mb > 500:  # 500MB
            warnings.append(f"Taille estimée très importante: {estimated_size_mb:.1f}MB")
        
        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings,
            'estimated_size_mb': estimated_size_mb
        }
    
    def _estimate_export_size(
        self,
        buildings_count: int,
        consumption_count: int,
        weather_count: int,
        export_format: str
    ) -> float:
        """
        Estime la taille d'export en MB
        
        Args:
            buildings_count: Nombre de bâtiments
            consumption_count: Nombre de points de consommation
            weather_count: Nombre de points météo
            export_format: Format d'export
            
        Returns:
            float: Taille estimée en MB
        """
        # Estimation en bytes par enregistrement selon le format
        size_per_record = {
            'csv': {'buildings': 200, 'consumption': 150, 'weather': 400},
            'parquet': {'buildings': 80, 'consumption': 60, 'weather': 160},
            'xlsx': {'buildings': 300, 'consumption': 200, 'weather': 500}
        }
        
        format_sizes = size_per_record.get(export_format, size_per_record['csv'])
        
        total_bytes = (
            buildings_count * format_sizes['buildings'] +
            consumption_count * format_sizes['consumption'] +
            weather_count * format_sizes['weather']
        )
        
        return total_bytes / (1024 * 1024)  # Conversion en MB