import sys
import subprocess
import signal
import argparse

# ==============================================================================
# АВТОМАТИЧЕСКАЯ УСТАНОВКА ЗАВИСИМОСТЕЙ (Self-contained deployment)
# ==============================================================================
REQUIRED_PACKAGES = [
    "docker",
    "requests",
    "confluent-kafka",  # Если у вас используется kafka-python, замените на "kafka-python"
    "clickhouse-connect",
    "customtkinter",
    "matplotlib"
]

def ensure_dependencies():
    print("🔍 Проверка зависимостей...")
    missing = []
    for pkg in REQUIRED_PACKAGES:
        try:
            # Пытаемся импортировать пакет (заменяем дефис на подчеркивание для корректной проверки)
            __import__(pkg.replace("-", "_"))
        except ImportError:
            missing.append(pkg)
    
    if missing:
        print(f"⚠️ Обнаружены отсутствующие пакеты: {', '.join(missing)}")
        print("⏳ Устанавливаю автоматически через pip...")
        try:
            # Используем sys.executable, чтобы гарантировать установку в текущий venv/интерпретатор
            subprocess.check_call([sys.executable, "-m", "pip", "install", *missing])
            print("✅ Все зависимости успешно установлены!\n")
        except subprocess.CalledProcessError as e:
            print(f"❌ Критическая ошибка установки пакетов: {e}")
            print("Пожалуйста, установите их вручную: pip install " + " ".join(missing))
            sys.exit(1)
    else:
        print("✅ Все зависимости уже установлены.\n")

# Запускаем проверку ДО импорта остальных модулей проекта
ensure_dependencies()

# ==============================================================================
# ИМПОРТЫ ПРОЕКТА (теперь гарантированно успешны)
# ==============================================================================
from core.docker_manager import DockerManager
from core.config_manager import ConfigManager
from core.stream_processor import StreamProcessor
from services.alert_manager import AlertManager
from services.data_generator import DataGenerator

# ==============================================================================
# КОНСОЛЬНЫЙ РЕЖИМ (Полная, несокращенная версия)
# ==============================================================================
def run_console_mode():
    print("=" * 60)
    print("Запуск системы мониторинга KPI (Консольный режим)")
    print("=" * 60)
    
    config = ConfigManager("config/settings.json")
    docker = DockerManager()
    
    alert_manager = AlertManager(
        telegram_token=config.get('telegram.token', ''),
        chat_id=config.get('telegram.chat_id', ''),
        cpu_threshold=config.get('alerting.cpu_threshold', 85.0),
        errors_threshold=config.get('alerting.errors_threshold', 5)
    )
    
    # Обработчики сигналов для корректного завершения по Ctrl+C
    def signal_handler(sig, frame):
        print("\nПолучен сигнал завершения. Остановка системы...")
        if generator: generator.stop()
        if processor: processor.stop()
        docker.stop_stack()
        print("Система остановлена.")
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        # 1. Подъем инфраструктуры
        docker.start_stack()
        
        if not docker.wait_for_healthy('redpanda', timeout=20):
            raise RuntimeError("Redpanda не запустился")
        
        if not docker.wait_for_clickhouse(timeout=60):
            raise RuntimeError("ClickHouse не ответил")
        
        db_name = config.get('clickhouse.database', 'kpi_db')
        docker.ensure_database_and_tables(db_name=db_name)
        
        # 2. Запуск генератора данных
        generator = DataGenerator(
            kafka_broker=config.get('kafka.broker'),
            topic=config.get('kafka.topic')
        )
        generator.start()
        
        # 3. Запуск процессора потока
        processor = StreamProcessor(
            kafka_broker=config.get('kafka.broker'),
            clickhouse_host=config.get('clickhouse.host'),
            ch_user=config.get('clickhouse.user'),
            ch_password=config.get('clickhouse.password'),
            ch_database=config.get('clickhouse.database'),
            window_size=config.get('processing.window_size', 60)
        )
        
        print("\n" + "=" * 60)
        print("СИСТЕМА ПОЛНОСТЬЮ ГОТОВА")
        print("=" * 60)
        print("Для остановки нажмите Ctrl+C\n")
        
        # 4. Основной цикл обработки
        processor.process(callback=alert_manager.check_and_alert)
        
    except Exception as e:
        print(f"\n❌ Критическая ошибка: {e}")
        if 'generator' in locals(): generator.stop()
        if 'processor' in locals(): processor.stop()
        docker.stop_stack()
        sys.exit(1)

# ==============================================================================
# GUI РЕЖИМ
# ==============================================================================
def run_gui_mode():
    print("🚀 Запуск графического интерфейса...")
    import customtkinter as ctk
    from ui.auth import LoginDialog
    from ui.main_window import KPIMonitorGUI
    
    config = ConfigManager("config/settings.json")
    docker = DockerManager()
    
    alert_manager = AlertManager(
        telegram_token=config.get('telegram.token', ''),
        chat_id=config.get('telegram.chat_id', ''),
        cpu_threshold=config.get('alerting.cpu_threshold', 85.0),
        errors_threshold=config.get('alerting.errors_threshold', 5)
    )
    
    # 1. Создаем ЕДИНСТВЕННЫЙ корневой объект приложения и скрываем его
    root = ctk.CTk()
    root.withdraw() # Скрываем, пока пользователь не войдет в систему
    root.title("Система мониторинга KPI ТЦ")
    root.geometry("1400x900")
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")

    # 2. Функция, которая сработает после успешного входа
    def on_login_success(user_info):
        # 3. Строим главный интерфейс на том же самом root
        gui = KPIMonitorGUI(
            root=root, # Передаем существующий root, а не создаем новый!
            docker_manager=docker, 
            alert_manager=alert_manager, 
            config=config,
            user_info=user_info
        )
        root.deiconify() # Делаем главное окно видимым

    # 4. Показываем диалог входа. Он заблокирует выполнение до ввода данных.
    login_dialog = LoginDialog(root, on_login_success)
    
    # 5. Запускаем главный цикл. Он будет работать, пока не закроют главное окно.
    root.mainloop()

    def on_login_success(user_info, login_window):
        # Сначала создаём главное окно
        gui = KPIMonitorGUI(
            docker_manager=docker, 
            alert_manager=alert_manager, 
            config=config,
            user_info=user_info,
            login_window=login_window  # передаём ссылку
        )
        # Теперь безопасно уничтожаем окно авторизации
        try:
            login_window.destroy()
        except Exception:
            pass  # Игнорируем ошибки уничтожения
    
    login = LoginWindow(on_login_success)
    login.run()

    # Сначала показываем окно авторизации
    def on_login_success(user_info):
        gui = KPIMonitorGUI(
            docker_manager=docker, 
            alert_manager=alert_manager, 
            config=config,
            user_info=user_info
        )
        gui.run()
    
    login = LoginWindow(on_login_success)
    login.run()

# ==============================================================================
# ТОЧКА ВХОДА
# ==============================================================================
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Система мониторинга KPI в реальном времени")
    parser.add_argument("--gui", action="store_true", help="Запустить графический интерфейс (CustomTkinter)")
    args = parser.parse_args()
    
    if args.gui:
        run_gui_mode()
    else:
        run_console_mode()