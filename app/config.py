"""Configuration management for fishing forecast app."""
import yaml
from pathlib import Path
from typing import Dict, Any

class Config:
    """Application configuration loaded from config.yaml"""

    def __init__(self, config_path: str = None):
        if config_path is None:
            # Default to config.yaml in project root
            config_path = Path(__file__).parent.parent / "config.yaml"

        with open(config_path, 'r') as f:
            self._config: Dict[str, Any] = yaml.safe_load(f)

    @property
    def location(self) -> Dict[str, Any]:
        return self._config['location']

    @property
    def latitude(self) -> float:
        return self._config['location']['latitude']

    @property
    def longitude(self) -> float:
        return self._config['location']['longitude']

    @property
    def timezone(self) -> str:
        return self._config['location']['timezone']

    @property
    def tide_station_id(self) -> str:
        """Tide prediction station ID (for backwards compatibility)"""
        return self._config['tide']['prediction_station_id']

    @property
    def tide_prediction_station_id(self) -> str:
        """Station ID for tide predictions (8735180 - Bayou La Batre)"""
        return self._config['tide']['prediction_station_id']

    @property
    def realtime_conditions_station_id(self) -> str:
        """Station ID for real-time conditions (8736897 - Middle Bay Light)"""
        return self._config['tide']['realtime_station_id']

    @property
    def tide_api_url(self) -> str:
        return self._config['tide']['api_url']

    @property
    def weather_api_url(self) -> str:
        return self._config['weather']['api_url']

    @property
    def weather_user_agent(self) -> str:
        return self._config['weather']['user_agent']

    @property
    def fetch_interval_minutes(self) -> int:
        return self._config['scheduler']['fetch_interval_minutes']

    @property
    def forecast_compute_interval_minutes(self) -> int:
        return self._config['scheduler']['forecast_compute_interval_minutes']

    @property
    def alert_thresholds(self) -> Dict[str, int]:
        return self._config['alerts']

    @property
    def email_config(self) -> Dict[str, Any]:
        return self._config['email']

    @property
    def telegram_config(self) -> Dict[str, Any]:
        return self._config['telegram']

    @property
    def server_host(self) -> str:
        return self._config['server']['host']

    @property
    def server_port(self) -> int:
        return self._config['server']['port']

    @property
    def debug(self) -> bool:
        return self._config['server']['debug']

    @property
    def marine_zone(self) -> str:
        return self._config['marine']['zone']

    @property
    def marine_fetch_interval(self) -> int:
        return self._config['marine']['fetch_interval_minutes']

    @property
    def marine_safety_thresholds(self) -> Dict[str, Any]:
        return self._config['marine']['safety_thresholds']

    @property
    def marine_bite_score_penalties(self) -> Dict[str, int]:
        return self._config['marine']['bite_score_penalties']

# Global config instance
config = Config()
