import json
import time
from datetime import datetime
from collections import defaultdict
from confluent_kafka import Consumer, KafkaException
import clickhouse_connect

class StreamProcessor:
    """Обрабатывает поток данных: фильтрация, windowing, агрегация"""
    
    def __init__(self, kafka_broker: str, clickhouse_host: str, 
                 ch_user: str, ch_password: str, ch_database: str,
                 window_size: int = 10):
        self.window_size = window_size
        self.buffer = defaultdict(lambda: {
            "cpu_sum": 0.0,
            "error_sum": 0,
            "count": 0,
            "window_start": time.time()
        })
        self.running = False
        
        # Подключение к Redpanda
        self.consumer = Consumer({
            'bootstrap.servers': kafka_broker,
            'group.id': 'kpi-processor',
            'auto.offset.reset': 'earliest'
        })
        self.consumer.subscribe(['raw_telemetry'])
        print(f"✅ Подключение к Redpanda ({kafka_broker}) установлено")
        
        # Подключение к ClickHouse
        self.ch_client = clickhouse_connect.get_client(
            host=clickhouse_host,
            port=8123,
            user=ch_user,
            password=ch_password,
            database=ch_database
        )
        print(f"✅ Подключение к ClickHouse ({clickhouse_host}) установлено")
    
    def process(self, callback=None):
        """Основной цикл обработки"""
        print("\n🔄 Запуск обработки потока...")
        self.running = True
        
        try:
            while self.running:
                msg = self.consumer.poll(1.0)
                
                if msg is None:
                    continue
                
                if msg.error():
                    raise KafkaException(msg.error())
                
                # Парсинг сообщения
                event = json.loads(msg.value().decode('utf-8'))
                source = event['source']
                current_time = time.time()
                window = self.buffer[source]
                
                # Фильтрация: игнорируем некорректные данные
                if event['cpu_usage'] < 0:
                    continue
                
                # Проверка окна
                if current_time - window['window_start'] >= self.window_size:
                    if window['count'] > 0:
                        avg_cpu = window['cpu_sum'] / window['count']
                        
                        # Сохранение в ClickHouse
                        self.ch_client.insert(
                            'metrics_aggregated',
                            [(datetime.utcnow(), source, avg_cpu, 
                              window['error_sum'], window['count'])],
                            column_names=['timestamp', 'source', 'avg_cpu', 
                                         'total_errors', 'event_count']
                        )
                        
                        print(f"[{datetime.now().strftime('%H:%M:%S')}] "
                              f"Агрегация для {source}: "
                              f"CPU={avg_cpu:.1f}%, Ошибок={window['error_sum']}")
                        
                        # Вызов callback для алертинга
                        if callback:
                            callback(source, avg_cpu, window['error_sum'])
                    
                    # Сброс окна
                    self.buffer[source] = {
                        "cpu_sum": 0.0,
                        "error_sum": 0,
                        "count": 0,
                        "window_start": current_time
                    }
                
                # Накопление данных в текущем окне
                window['cpu_sum'] += event['cpu_usage']
                window['error_sum'] += event['errors']
                window['count'] += 1
                
        except KeyboardInterrupt:
            print("\n⏹️ Остановка процессора...")
        finally:
            self.consumer.close()
            self.running = False
    
    def stop(self):
        """Останавливает обработку"""
        self.running = False