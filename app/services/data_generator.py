import json
import time
import random
import threading
from datetime import datetime
from confluent_kafka import Producer

class DataGenerator:
    """Генерирует поток событий и отправляет в Redpanda"""
    
    def __init__(self, kafka_broker: str, topic: str):
        self.topic = topic
        self.running = False
        self.thread = None
        
        # Настройки Redpanda
        self.producer = Producer({'bootstrap.servers': kafka_broker})
        print(f"✅ Генератор данных подключен к {kafka_broker}")
    
    def _delivery_report(self, err, msg):
        """Callback для отслеживания доставки сообщений"""
        if err is not None:
            print(f'❌ Ошибка доставки: {err}')
    
    def _generate_loop(self):
        """Основной цикл генерации данных"""
        sources = ['server_1', 'server_2', 'server_3']
        
        while self.running:
            for source in sources:
                # Генерируем аномалию с вероятностью 5%
                is_anomaly = random.random() < 0.05
                cpu = random.uniform(80, 99) if is_anomaly else random.uniform(20, 60)
                errors = random.randint(1, 5) if is_anomaly else 0
                
                event = {
                    "timestamp": datetime.utcnow().isoformat() + "Z",
                    "source": source,
                    "cpu_usage": round(cpu, 2),
                    "errors": errors
                }
                
                self.producer.produce(
                    self.topic,
                    key=source,
                    value=json.dumps(event),
                    callback=self._delivery_report
                )
            
            self.producer.flush()
            time.sleep(1)  # 1 событие в секунду с каждого источника
    
    def start(self):
        """Запускает генерацию данных в отдельном потоке"""
        if self.running:
            print("⚠️ Генератор уже запущен")
            return
        
        self.running = True
        self.thread = threading.Thread(target=self._generate_loop, daemon=True)
        self.thread.start()
        print("✅ Генератор данных запущен")
    
    def stop(self):
        """Останавливает генерацию данных"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=2)
        print("⏹️ Генератор данных остановлен")