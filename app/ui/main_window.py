import customtkinter as ctk
from tkinter import ttk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import threading
import time
from datetime import datetime
import clickhouse_connect

# ==============================================================================
# БЛОК ВИЗУАЛИЗАЦИИ (UI) - Главный класс окна
# ==============================================================================
class KPIMonitorGUI:
    def __init__(self, docker_manager, alert_manager, config):
        self.docker_manager = docker_manager
        self.alert_manager = alert_manager
        self.config = config
        self.running = False
        
        # Настройка главного окна
        self.root = ctk.CTk()
        self.root.title("Система мониторинга KPI торгового центра (Real-time)")
        self.root.geometry("1400x900")
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        
        # Основная сетка: Сайдбар (слева) и Основная область (справа)
        self.root.grid_columnconfigure(1, weight=1)
        self.root.grid_rowconfigure(0, weight=1)
        
        self._create_sidebar()
        self._create_main_area()
        
        # Поток обновления данных
        self.update_thread = None

    # ==============================================================================
    # БЛОК УПРАВЛЕНИЯ и МОНИТОРИНГА ИНФРАСТРУКТУРЫ (Сайдбар)
    # ==============================================================================
    def _create_sidebar(self):
        sidebar = ctk.CTkFrame(self.root, width=300, corner_radius=0)
        sidebar.grid(row=0, column=0, sticky="nsew")
        sidebar.grid_rowconfigure(4, weight=1)

        # 1. Блок управления
        ctk.CTkLabel(sidebar, text="Управление системой", font=ctk.CTkFont(size=16, weight="bold")).grid(row=0, column=0, padx=20, pady=20, sticky="w")
        
        self.btn_start = ctk.CTkButton(sidebar, text="▶ Запустить", command=self._start_system, fg_color="green", hover_color="darkgreen")
        self.btn_start.grid(row=1, column=0, padx=20, pady=10, sticky="ew")
        
        self.btn_stop = ctk.CTkButton(sidebar, text="⏹ Остановить", command=self._stop_system, fg_color="red", hover_color="darkred", state="disabled")
        self.btn_stop.grid(row=2, column=0, padx=20, pady=10, sticky="ew")

        # 2. Блок мониторинга инфраструктуры
        ctk.CTkLabel(sidebar, text="Инфраструктура", font=ctk.CTkFont(size=14, weight="bold")).grid(row=3, column=0, padx=20, pady=(20, 10), sticky="w")
        
        self.infra_status = {}
        for service in ["Redpanda", "ClickHouse", "Grafana"]:
            frame = ctk.CTkFrame(sidebar)
            frame.grid(row=4 + list(["Redpanda", "ClickHouse", "Grafana"]).index(service), column=0, padx=20, pady=5, sticky="ew")
            
            dot = ctk.CTkLabel(frame, text="●", text_color="gray", font=ctk.CTkFont(size=18))
            dot.pack(side="left", padx=10)
            lbl = ctk.CTkLabel(frame, text=service, anchor="w")
            lbl.pack(side="left", fill="x", expand=True)
            
            self.infra_status[service] = dot

        # 3. Блок управления и настройки (пороги алертинга)
        settings_frame = ctk.CTkFrame(sidebar)
        settings_frame.grid(row=7, column=0, padx=20, pady=20, sticky="ew")
        
        ctk.CTkLabel(settings_frame, text="Настройки алертинга", font=ctk.CTkFont(weight="bold")).grid(row=0, column=0, columnspan=2, padx=10, pady=10)
        
        ctk.CTkLabel(settings_frame, text="CPU порог (%):").grid(row=1, column=0, padx=10, pady=5, sticky="w")
        self.entry_cpu = ctk.CTkEntry(settings_frame, width=80)
        self.entry_cpu.insert(0, str(self.alert_manager.thresholds['cpu']))
        self.entry_cpu.grid(row=1, column=1, padx=10, pady=5)
        
        ctk.CTkLabel(settings_frame, text="Порог ошибок:").grid(row=2, column=0, padx=10, pady=5, sticky="w")
        self.entry_err = ctk.CTkEntry(settings_frame, width=80)
        self.entry_err.insert(0, str(self.alert_manager.thresholds['errors']))
        self.entry_err.grid(row=2, column=1, padx=10, pady=5)
        
        btn_apply = ctk.CTkButton(settings_frame, text="Применить", command=self._apply_settings, height=30)
        btn_apply.grid(row=3, column=0, columnspan=2, padx=10, pady=15, sticky="ew")

        # 4. Блок уведомлений (Лог алертов)
        ctk.CTkLabel(sidebar, text="Лог алертов", font=ctk.CTkFont(weight="bold")).grid(row=8, column=0, padx=20, pady=(20, 5), sticky="w")
        self.alert_log = ctk.CTkTextbox(sidebar, height=150, font=ctk.CTkFont(size=11))
        self.alert_log.grid(row=9, column=0, padx=20, pady=10, sticky="ew")

    # ==============================================================================
    # БЛОК ВИЗУАЛИЗАЦИИ (Основная область)
    # ==============================================================================
    def _create_main_area(self):
        main = ctk.CTkFrame(self.root)
        main.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        main.grid_rowconfigure(1, weight=1)
        main.grid_columnconfigure(0, weight=1)

        # 1. Тепловая карта / Матрица и Бинарные индикаторы
        ctk.CTkLabel(main, text="Матрица состояния источников (Тепловая карта)", font=ctk.CTkFont(size=16, weight="bold")).grid(row=0, column=0, pady=10, sticky="w")
        
        self.heatmap_frame = ctk.CTkFrame(main)
        self.heatmap_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=5)
        self.heatmap_frame.grid_columnconfigure((0, 1, 2), weight=1)
        
        self.server_indicators = {}
        for i, server in enumerate(["server_1", "server_2", "server_3"]):
            card = ctk.CTkFrame(self.heatmap_frame, fg_color="gray20")
            card.grid(row=0, column=i, padx=10, pady=10, sticky="nsew")
            
            ctk.CTkLabel(card, text=server.upper(), font=ctk.CTkFont(weight="bold")).pack(pady=5)
            lbl_cpu = ctk.CTkLabel(card, text="CPU: --%", font=ctk.CTkFont(size=14))
            lbl_cpu.pack(pady=2)
            lbl_err = ctk.CTkLabel(card, text="Ошибки: --", font=ctk.CTkFont(size=12))
            lbl_err.pack(pady=2)
            
            self.server_indicators[server] = {"card": card, "cpu": lbl_cpu, "err": lbl_err}

        # 2. График / Таймлайн
        chart_frame = ctk.CTkFrame(main)
        chart_frame.grid(row=2, column=0, sticky="nsew", padx=10, pady=10)
        
        ctk.CTkLabel(chart_frame, text="Динамика KPI (Средний CPU по времени)", font=ctk.CTkFont(size=14, weight="bold")).pack(pady=5)
        
        self.fig = Figure(figsize=(8, 3), dpi=100)
        self.fig.patch.set_facecolor('#2b2b2b') # Темный фон для графика
        self.ax = self.fig.add_subplot(111)
        self.ax.set_facecolor('#2b2b2b')
        self.ax.tick_params(colors='white')
        self.ax.xaxis.label.set_color('white')
        self.ax.yaxis.label.set_color('white')
        self.ax.grid(True, color='#666666')
        
        self.canvas = FigureCanvasTkAgg(self.fig, master=chart_frame)
        self.canvas.get_tk_widget().pack(fill="both", expand=True, padx=10, pady=10)

        # 3. Таблица с детализацией
        table_frame = ctk.CTkFrame(main)
        table_frame.grid(row=3, column=0, sticky="nsew", padx=10, pady=10)
        
        ctk.CTkLabel(table_frame, text="Детализация данных (Блок хранения и аналитики)", font=ctk.CTkFont(size=14, weight="bold")).pack(pady=5)
        
        columns = ("Время", "Источник", "CPU %", "Ошибки", "Событий")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=8)
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=150, anchor="center")
        
        # Стилизация таблицы (темная тема)
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview", background="#2b2b2b", foreground="white", fieldbackground="#2b2b2b", rowheight=25)
        style.configure("Treeview.Heading", background="#1f538d", foreground="white")
        
        self.tree.pack(fill="both", expand=True, padx=10, pady=10)

    # ==============================================================================
    # ЛОГИКА ОБНОВЛЕНИЯ ДАННЫХ
    # ==============================================================================
    def _update_loop(self):
        """Фоновый поток для опроса ClickHouse и обновления UI"""
        while self.running:
            try:
                client = clickhouse_connect.get_client(
                    host='localhost', port=8123, username='app_user', 
                    password='app_secret', database='kpi_db'
                )
                
                # Запрос последних 30 записей
                result = client.query(
                    "SELECT timestamp, source, avg_cpu, total_errors, event_count "
                    "FROM metrics_aggregated ORDER BY timestamp DESC LIMIT 30"
                )
                
                self.root.after(0, self._update_ui, result.result_rows)
                
            except Exception as e:
                # Тихая ошибка, если БД перезагружается
                pass
            
            time.sleep(3) # Обновление каждые 3 секунды

    def _update_ui(self, data):
        """Обновление элементов UI из главного потока (безопасно для Tkinter)"""
        if not data:
            return

        # 1. Обновление таблицы (Детализация)
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        for row in reversed(data):
            ts, src, cpu, err, ev = row
            self.tree.insert("", 0, values=(
                ts.strftime("%H:%M:%S"), src, f"{cpu:.1f}", err, ev
            ))

        # 2. Обновление тепловой карты и бинарных индикаторов
        latest_by_source = {}
        for row in data:
            if row[1] not in latest_by_source:
                latest_by_source[row[1]] = row
        
        for src, info in self.server_indicators.items():
            if src in latest_by_source:
                _, _, cpu, err, _ = latest_by_source[src]
                info["cpu"].configure(text=f"CPU: {cpu:.1f}%")
                info["err"].configure(text=f"Ошибки: {err}")
                
                # Бинарный индикатор: меняем цвет карточки
                if cpu > self.alert_manager.thresholds['cpu'] or err > self.alert_manager.thresholds['errors']:
                    info["card"].configure(fg_color="#800000") # Красный (Алерт)
                else:
                    info["card"].configure(fg_color="#006400") # Зеленый (Норма)

        # 3. Обновление графика (Таймлайн)
        self.ax.clear()
        times, cpus = [], []
        for row in reversed(data):
            times.append(row[0].strftime("%H:%M:%S"))
            cpus.append(row[2])
            
        self.ax.plot(times, cpus, marker='o', color='#1f77b4', linewidth=2)
        self.ax.set_ylim(0, 100)
        self.ax.tick_params(axis='x', rotation=45)
        self.fig.tight_layout()
        self.canvas.draw()

    def _update_infra_status(self):
        """Проверка статуса Docker-контейнеров"""
        while self.running:
            for service, dot in self.infra_status.items():
                try:
                    container = self.docker_manager.client.containers.get(service.lower())
                    color = "green" if container.status == "running" else "red"
                except:
                    color = "red"
                self.root.after(0, lambda d=dot, c=color: d.configure(text_color=c))
            time.sleep(5)

    # ==============================================================================
    # УПРАВЛЕНИЕ
    # ==============================================================================
    def _start_system(self):
        self.btn_start.configure(state="disabled")
        self.btn_stop.configure(state="normal")
        self.running = True
        
        self.alert_log.insert("end", "[INFO] Запуск инфраструктуры...\n")
        
        # Запуск в отдельном потоке, чтобы не морозить GUI
        threading.Thread(target=self._run_backend, daemon=True).start()
        threading.Thread(target=self._update_loop, daemon=True).start()
        threading.Thread(target=self._update_infra_status, daemon=True).start()

    def _run_backend(self):
        try:
            self.docker_manager.start_stack()
            self.docker_manager.wait_for_healthy('redpanda', timeout=20)
            self.docker_manager.wait_for_clickhouse(timeout=60)
            self.docker_manager.ensure_database_and_tables()
            self.root.after(0, lambda: self.alert_log.insert("end", "[SUCCESS] Система готова\n"))
        except Exception as e:
            self.root.after(0, lambda: self.alert_log.insert("end", f"[ERROR] {e}\n"))

    def _stop_system(self):
        self.running = False
        self.alert_log.insert("end", "[INFO] Остановка системы...\n")
        self.docker_manager.stop_stack()
        self.btn_start.configure(state="normal")
        self.btn_stop.configure(state="disabled")

    def _apply_settings(self):
        """Блок управления и настройки: обновление порогов на лету"""
        try:
            new_cpu = float(self.entry_cpu.get())
            new_err = int(self.entry_err.get())
            self.alert_manager.update_thresholds(cpu=new_cpu, errors=new_err)
            self.alert_log.insert("end", f"[SETTINGS] Пороги обновлены: CPU>{new_cpu}%, Ошибки>{new_err}\n")
        except ValueError:
            self.alert_log.insert("end", "[ERROR] Неверный формат чисел в настройках\n")

    def run(self):
        self.root.mainloop()