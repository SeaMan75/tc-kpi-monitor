import requests
from datetime import datetime

class AlertManager:
    """Управляет уведомлениями (Telegram)"""
    
    def __init__(self, telegram_token: str, chat_id: str, 
                 cpu_threshold: float = 85.0, errors_threshold: int = 5):
        self.telegram_token = telegram_token
        self.chat_id = chat_id
        self.thresholds = {
            'cpu': cpu_threshold,
            'errors': errors_threshold
        }
        print(f"✅ AlertManager инициализирован (CPU > {cpu_threshold}%, Ошибки > {errors_threshold})")
    
    def check_and_alert(self, source: str, avg_cpu: float, total_errors: int):
        """Проверяет пороги и отправляет алерт"""
        alerts = []
        
        if avg_cpu > self.thresholds['cpu']:
            alerts.append(f"CPU: {avg_cpu:.1f}% (порог: {self.thresholds['cpu']}%)")
        
        if total_errors > self.thresholds['errors']:
            alerts.append(f"Ошибки: {total_errors} (порог: {self.thresholds['errors']})")
        
        if alerts:
            self._send_telegram_alert(source, alerts)
    
    def _send_telegram_alert(self, source: str, alerts: list):
        """Отправляет алерт в Telegram"""
        alerts_text = "\n".join(f"  • {alert}" for alert in alerts)
        
        message = f"""
🚨 *АЛЕРТ: Превышены пороги*

*Источник:* {source}
*Проблемы:*
{alerts_text}
*Время:* {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        """.strip()
        
        url = f'https://api.telegram.org/bot{self.telegram_token}/sendMessage'
        payload = {
            'chat_id': self.chat_id,
            'text': message,
            'parse_mode': 'Markdown'
        }
        
        try:
            response = requests.post(url, json=payload, timeout=5)
            if response.status_code == 200:
                print(f"  ✅ Алерт отправлен в Telegram для {source}")
            else:
                print(f"  ❌ Ошибка отправки алерта: {response.text}")
        except Exception as e:
            print(f"  ❌ Исключение при отправке алерта: {e}")
    
    def update_thresholds(self, cpu: float = None, errors: int = None):
        """Обновляет пороги срабатывания"""
        if cpu is not None:
            self.thresholds['cpu'] = cpu
        if errors is not None:
            self.thresholds['errors'] = errors
        print(f"⚙️ Пороги обновлены: CPU > {self.thresholds['cpu']}%, Ошибки > {self.thresholds['errors']}")