import docker
from docker.errors import DockerException, NotFound
import time
import requests

class DockerManager:
    def __init__(self):
        try:
            self.client = docker.from_env()
            self.client.ping()
            print("Подключение к Docker установлено")
        except DockerException as e:
            raise RuntimeError(f"Не удалось подключиться к Docker: {e}")
        
        self.containers = {}
        self.network_name = "kpi-monitor-network"
    
    def _create_network(self):
        try:
            self.client.networks.get(self.network_name)
            print(f"Сеть {self.network_name} уже существует")
        except NotFound:
            self.client.networks.create(self.network_name, driver="bridge")
            print(f"Сеть {self.network_name} создана")
    
    def start_stack(self):
        print("\nЗапуск инфраструктуры...")
        self._create_network()
        
        # Redpanda
        self._start_container(
            name='redpanda',
            image='docker.redpanda.com/redpandadata/redpanda:v23.3.3',
            ports={'9092/tcp': 9092},
            command=[
                'redpanda', 'start', '--smp', '1', '--memory', '1G',
                '--reserve-memory', '0M', '--overprovisioned', '--node-id', '0',
                '--kafka-addr', 'PLAINTEXT://0.0.0.0:29092,OUTSIDE://0.0.0.0:9092',
                '--advertise-kafka-addr', 'PLAINTEXT://redpanda:29092,OUTSIDE://localhost:9092'
            ]
        )
        
        # ClickHouse
        self._start_container(
            name='clickhouse',
            image='clickhouse/clickhouse-server:23.8',
            ports={'8123/tcp': 8123, '9000/tcp': 9000},
            environment={
                'CLICKHOUSE_USER': 'admin',
                'CLICKHOUSE_PASSWORD': 'secret',
                'CLICKHOUSE_DEFAULT_ACCESS_MANAGEMENT': '1'
            }
        )
        
        # Redpanda Console
        self._start_container(
            name='console',
            image='docker.redpanda.com/redpandadata/console:v2.3.8',
            ports={'8080/tcp': 8080},
            environment={'KAFKA_BROKERS': 'redpanda:29092'}
        )
        
        # Grafana
        self._start_container(
            name='grafana',
            image='grafana/grafana:10.2.0',
            ports={'3000/tcp': 3000},
            environment={
                'GF_SECURITY_ADMIN_USER': 'admin',
                'GF_SECURITY_ADMIN_PASSWORD': 'admin'
            }
        )
        
        print("Инфраструктура запущена\n")
    
    def _start_container(self, name, image, ports=None, command=None, environment=None):
        try:
            existing = self.client.containers.get(name)
            print(f"  {name} уже запущен")
            return
        except NotFound:
            pass
        
        run_params = {
            'image': image,
            'name': name,
            'detach': True,
        }
        
        if ports:
            run_params['ports'] = ports
        
        if command:
            run_params['command'] = command
        
        if environment:
            run_params['environment'] = environment
        
        try:
            container = self.client.containers.run(**run_params)
            self.containers[name] = container
            print(f"  {name} запущен")
        except Exception as e:
            print(f"  Ошибка запуска {name}: {e}")
    
    def stop_stack(self):
        print("Остановка инфраструктуры...")
        for name, container in list(self.containers.items()):
            try:
                container.stop(timeout=5)
                container.remove()
                print(f"  {name} остановлен")
            except Exception as e:
                print(f"  Ошибка остановки {name}: {e}")
        
        self.containers.clear()
    
    def wait_for_healthy(self, service_name, timeout=30):
        print(f"Ожидание готовности {service_name}...")
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                container = self.client.containers.get(service_name)
                container.reload()
                if container.status == 'running':
                    print(f"  {service_name} готов")
                    return True
            except NotFound:
                pass
            time.sleep(1)
        
        return False
    
    def wait_for_clickhouse(self, timeout=60):
        print("Ожидание ClickHouse...")
        start = time.time()
        while time.time() - start < timeout:
            try:
                r = requests.get("http://localhost:8123/ping", timeout=5)
                if r.status_code == 200 and "Ok" in r.text:
                    print("ClickHouse готов")
                    return True
            except Exception:
                pass
            time.sleep(2)
        print("ClickHouse не ответил за 60 секунд")
        return False
    
    def ensure_database_and_tables(self, db_name="kpi_db"):
        print(f"Проверка и инициализация БД '{db_name}'...")
        
        # 1. Создаем базу и пользователя (если нет)
        check_user = "SELECT count() FROM system.users WHERE name = 'app_user'"
        create_db = f"CREATE DATABASE IF NOT EXISTS {db_name}"
        create_user = "CREATE USER IF NOT EXISTS 'app_user' IDENTIFIED WITH plaintext_password BY 'app_secret'"
        grant_perms = f"GRANT INSERT, SELECT, CREATE TABLE ON {db_name}.* TO 'app_user'"
        
        try:
            r = requests.post("http://localhost:8123/", data=check_user.encode(), auth=('admin', 'secret'))
            if r.status_code == 200 and r.text.strip() == '0':
                print("  Создаю пользователя и выдаю права...")
                requests.post("http://localhost:8123/", data=create_db.encode(), auth=('admin', 'secret'))
                requests.post("http://localhost:8123/", data=create_user.encode(), auth=('admin', 'secret'))
                requests.post("http://localhost:8123/", data=grant_perms.encode(), auth=('admin', 'secret'))
            else:
                print("  Пользователь app_user уже существует")
        except Exception as e:
            print(f"  Ошибка настройки пользователя: {e}")
            raise

        # 2. Создаем таблицы (если их нет)
        # ВНИМАНИЕ: Если в твоем stream_processor.py другие названия колонок, поправь их здесь!
        create_table_metrics = f"""
        CREATE TABLE IF NOT EXISTS {db_name}.metrics_aggregated (
            timestamp DateTime,
            source String,
            avg_cpu Float32,
            total_errors UInt32,
            record_count UInt32
        ) ENGINE = MergeTree()
        ORDER BY (timestamp, source)
        """
        
        try:
            print(f"  Создаю таблицу {db_name}.metrics_aggregated...")
            r = requests.post("http://localhost:8123/", data=create_table_metrics.encode(), auth=('app_user', 'app_secret'))
            if r.status_code == 200:
                print("  ✅ Таблица успешно создана или уже существует")
            else:
                print(f"  ⚠️ Ответ ClickHouse при создании таблицы: {r.text}")
        except Exception as e:
            print(f"  ❌ Ошибка создания таблицы: {e}")
            raise