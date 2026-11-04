import json
import os

class ConfigManager:
    """Управляет конфигурацией приложения"""
    
    def __init__(self, config_path: str = "config/settings.json"):
        self.config_path = config_path
        self.settings = {}
        self.load()
    
    def load(self):
        """Загружает конфигурацию из файла"""
        if not os.path.exists(self.config_path):
            raise FileNotFoundError(f"Конфигурационный файл не найден: {self.config_path}")
        
        with open(self.config_path, 'r', encoding='utf-8') as f:
            self.settings = json.load(f)
        print(f"✅ Конфигурация загружена из {self.config_path}")
    
    def save(self):
        """Сохраняет конфигурацию в файл"""
        with open(self.config_path, 'w', encoding='utf-8') as f:
            json.dump(self.settings, f, indent=2, ensure_ascii=False)
        print(f"✅ Конфигурация сохранена в {self.config_path}")
    
    def get(self, key_path: str, default=None):
        """
        Получает значение по пути (например, 'telegram.token')
        """
        keys = key_path.split('.')
        value = self.settings
        
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        
        return value
    
    def set(self, key_path: str, value):
        """
        Устанавливает значение по пути
        """
        keys = key_path.split('.')
        settings = self.settings
        
        for key in keys[:-1]:
            if key not in settings:
                settings[key] = {}
            settings = settings[key]
        
        settings[keys[-1]] = value
        self.save()
    
    def update(self, updates: dict):
        """Обновляет несколько значений"""
        for key_path, value in updates.items():
            self.set(key_path, value)