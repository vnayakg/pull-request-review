import os
import yaml
from dotenv import load_dotenv

class Config:
    def __init__(self, config_path=None):
        load_dotenv()
        self.config = self._load_config(config_path)

    def _load_config(self, config_path):
        # Load default config
        default_path = os.path.join(os.path.dirname(__file__), '../config/default_config.yaml')
        with open(default_path, 'r') as f:
            config = yaml.safe_load(f)
        # Override with user config if provided
        if config_path:
            with open(config_path, 'r') as f:
                user_config = yaml.safe_load(f)
            config = self._deep_update(config, user_config)
        # Substitute env vars
        config = self._substitute_env_vars(config)
        return config

    def _deep_update(self, d, u):
        for k, v in u.items():
            if isinstance(v, dict):
                d[k] = self._deep_update(d.get(k, {}), v)
            else:
                d[k] = v
        return d

    def _substitute_env_vars(self, obj):
        if isinstance(obj, dict):
            return {k: self._substitute_env_vars(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._substitute_env_vars(i) for i in obj]
        elif isinstance(obj, str) and obj.startswith('${') and obj.endswith('}'): 
            env_var = obj[2:-1]
            return os.getenv(env_var, obj)
        else:
            return obj

    def get(self, key_path, default=None):
        keys = key_path.split('.')
        val = self.config
        for k in keys:
            val = val.get(k, None)
            if val is None:
                return default
        return val 