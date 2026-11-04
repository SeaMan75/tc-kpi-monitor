import time
import signal
import sys
from core.docker_manager import DockerManager
from core.config_manager import ConfigManager
from core.stream_processor import StreamProcessor
from services.alert_manager import AlertManager
from services.data_generator import DataGenerator

class KPIApplication:
    def __init__(self, config_path="config/settings.json"):
        self.config = ConfigManager(config_path)
        self.docker = DockerManager()
        
        # ИСПРАВЛЕННЫЙ БЛОК: параметры теперь точно совпадают с AlertManager
        self.alert_manager = AlertManager(
            telegram_token=self.config.get('telegram.token', ''),
            chat_id=self.config.get('telegram.chat_id', ''),
            cpu_threshold=self.config.get('alerting.cpu_threshold', 85.0),
            errors_threshold=self.config.get('alerting.errors_threshold', 5)
        )
        
        self.processor = None
        self.generator = None
        
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        print("\nПолучен сигнал завершения...")
        self.stop()
        sys.exit(0)
    
    def start(self):
        print("=" * 60)
        print("Запуск системы мониторинга KPI")
        print("=" * 60)
        
        self.docker.start_stack()
        
        if not self.docker.wait_for_healthy('redpanda', timeout=20):
            raise RuntimeError("Redpanda не запустился")
        
        if not self.docker.wait_for_clickhouse(timeout=60):
            print("Перезапускаю ClickHouse...")
            try:
                containers = self.docker.client.containers.list(filters={'name': 'clickhouse'})
                if containers:
                    containers[0].restart()
                else:
                    print("ClickHouse не найден, запускаю заново...")
                    self.docker.start_stack()
            except Exception as e:
                print(f"Ошибка перезапуска ClickHouse: {e}")
                raise RuntimeError("ClickHouse не запустился")
            
            if not self.docker.wait_for_clickhouse(timeout=60):
                raise RuntimeError("ClickHouse не ответил после перезапуска")
        
        # Получаем имя базы из конфига (по умолчанию 'kpi_db')
        db_name = self.config.get('clickhouse.database', 'kpi_db')
        
        # Получаем имя базы из конфига (по умолчанию 'kpi_db')
        db_name = self.config.get('clickhouse.database', 'kpi_db')
        
        # Передаем его в метод инициализации (теперь он создает и таблицы)
        self.docker.ensure_database_and_tables(db_name=db_name)
        
        self.generator = DataGenerator(
            kafka_broker=self.config.get('kafka.broker'),
            topic=self.config.get('kafka.topic')
        )
        self.generator.start()
        
        self.processor = StreamProcessor(
            kafka_broker=self.config.get('kafka.broker'),
            clickhouse_host=self.config.get('clickhouse.host'),
            ch_user=self.config.get('clickhouse.user'),
            ch_password=self.config.get('clickhouse.password'),
            ch_database=self.config.get('clickhouse.database'),
            window_size=self.config.get('processing.window_size', 60)
        )
        
        print("\n" + "=" * 60)
        print("СИСТЕМА ПОЛНОСТЬЮ ГОТОВА")
        print("=" * 60)
        print("Grafana: http://localhost:3000 (admin/admin)")
        print("Redpanda Console: http://localhost:8080")
        print("ClickHouse: http://localhost:8123")
        print("=" * 60)
        print("\nДля остановки нажмите Ctrl+C\n")
    
    def run(self):
        self.processor.process(callback=self.alert_manager.check_and_alert)
    
    def stop(self):
        print("\n" + "=" * 60)
        print("Остановка системы...")
        print("=" * 60)
        
        if self.generator:
            self.generator.stop()
        
        if self.processor:
            self.processor.stop()
        
        self.docker.stop_stack()
        
        print("\nСистема остановлена")
        print("=" * 60)

if __name__ == "__main__":
    app = KPIApplication()
    try:
        app.start()
        app.run()
    except KeyboardInterrupt:
        app.stop()
    except Exception as e:
        print(f"\nКритическая ошибка: {e}")
        app.stop()
        sys.exit(1)