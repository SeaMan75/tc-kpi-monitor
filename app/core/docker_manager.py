import docker
from docker.errors import DockerException, NotFound
import yaml
import time

class DockerManager:
    """Управляет Docker-контейнерами через Docker API"""
    
    def __init__(self, compose_file: str = "config/docker-compose.yml"):
        try:
            self.client = docker.from_env()
            self.client.ping()
            print("✅ Подключение к Docker установлено")
        except DockerException as e:
            raise RuntimeError(f"Не удалось подключиться к Docker: {e}")
        
        self.compose_file = compose_file
        self.containers = {}
        self.network_name = "kpi-monitor-network"
    
    def _create_network(self):
        """Создает Docker-сеть"""
        try:
            self.client.networks.get(self.network_name)
            print(f"✅ Сеть {self.network_name} уже существует")
        except NotFound:
            self.client.networks.create(self.network_name, driver="bridge")
            print(f"✅ Сеть {self.network_name} создана")
    
    def start_stack(self):
        """Запускает весь стек (Redpanda, ClickHouse, Grafana)"""
        print("\n🚀 Запуск инфраструктуры...")
        
        # Создаем сеть
        self._create_network()
        
        # Читаем docker-compose.yml
        with open(self.compose_file, 'r', encoding='utf-8') as f:
            compose = yaml.safe_load(f)
        
        # Запускаем сервисы в правильном порядке
        services_order = ['redpanda', 'clickhouse', 'console', 'grafana']
        
        for service_name in services_order:
            if service_name not in compose['services']:
                continue
            
            service_config = compose['services'][service_name]
            
            # Проверяем, не запущен ли уже контейнер
            try:
                existing = self.client.containers.get(service_name)
                print(f"⚠️ {service_name} уже запущен")
                self.containers[service_name] = existing
                continue
            except NotFound:
                pass
            
            # Подготавливаем параметры
            run_params = {
                'image': service_config['image'],
                'name': service_name,
                'detach': True,
                'network': self.network_name,
            }
            
            # Порты
            if 'ports' in service_config:
                ports = {}
                for port_mapping in service_config['ports']:
                    host_port, container_port = port_mapping.split(':')
                    ports[f"{container_port}/tcp"] = int(host_port)
                run_params['ports'] = ports
            
            # Переменные окружения
            if 'environment' in service_config:
                env = {}
                for env_var in service_config['environment']:
                    if '=' in env_var:
                        key, value = env_var.split('=', 1)
                        env[key] = value
                run_params['environment'] = env
            
            # Команда
            if 'command' in service_config:
                run_params['command'] = service_config['command']
            
            # Запускаем контейнер
            try:
                container = self.client.containers.run(**run_params)
                self.containers[service_name] = container
                print(f"  ✅ {service_name} запущен")
            except Exception as e:
                print(f"  ❌ Ошибка запуска {service_name}: {e}")
        
        print("✅ Инфраструктура запущена\n")
    
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
    
        try:
            network = self.client.networks.get(self.network_name)
            network.remove()
            print(f"Сеть {self.network_name} удалена")
        except NotFound:
            pass
    
    def get_status(self) -> dict:
        """Возвращает статус всех контейнеров"""
        status = {}
        for name, container in self.containers.items():
            try:
                container.reload()
                status[name] = container.status
            except Exception:
                status[name] = 'unknown'
        return status
    
    def wait_for_healthy(self, service_name: str, timeout: int = 30):
        """Ожидает, пока контейнер станет здоровым"""
        print(f"⏳ Ожидание готовности {service_name}...")
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                container = self.client.containers.get(service_name)
                container.reload()
                if container.status == 'running':
                    print(f"  ✅ {service_name} готов")
                    return True
            except NotFound:
                pass
            time.sleep(1)
        
        print(f"  ⚠️ {service_name} не готов после {timeout} секунд")
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

    def ensure_app_user(self):
        print("Проверка пользователя ClickHouse...")
        check_query = "SELECT count() FROM system.users WHERE name = 'app_user'"
        create_db = "CREATE DATABASE IF NOT EXISTS tc_kpi_db"
        create_user = "CREATE USER IF NOT EXISTS 'app_user' IDENTIFIED WITH plaintext_password BY 'app_secret'"
        grant_perms = "GRANT INSERT, SELECT ON tc_kpi_db.* TO 'app_user'"
        
        try:
            r = requests.post("http://localhost:8123/", data=check_query.encode(), auth=('admin', 'secret'))
            if r.status_code == 200 and r.text.strip() == '0':
                print("Создаю пользователя app_user...")
                requests.post("http://localhost:8123/", data=create_db.encode(), auth=('admin', 'secret'))
                requests.post("http://localhost:8123/", data=create_user.encode(), auth=('admin', 'secret'))
                requests.post("http://localhost:8123/", data=grant_perms.encode(), auth=('admin', 'secret'))
                print("Пользователь app_user создан")
            else:
                print("Пользователь app_user уже существует")
        except Exception as e:
            print(f"Ошибка настройки ClickHouse: {e}")
            raise