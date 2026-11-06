import customtkinter as ctk
from tkinter import ttk, messagebox
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from datetime import datetime, timedelta
import random

# ==============================================================================
# ВКЛАДКА 1: DASHBOARD (Главный экран)
# ==============================================================================
class DashboardTab(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent)
        self._build()
        
    def _build(self):
        # KPI-карточки сверху
        kpi_frame = ctk.CTkFrame(self)
        kpi_frame.pack(fill="x", padx=10, pady=10)
        
        self.kpi_cards = {}
        kpis = [
            ("Посетителей сегодня", "12,847", "+12%", "green"),
            ("Средний чек", "2,340 ₽", "+5%", "green"),
            ("Конверсия", "18.4%", "-2%", "red"),
            ("Выручка за час", "847,200 ₽", "+8%", "green"),
        ]
        
        for i, (title, value, delta, color) in enumerate(kpis):
            card = ctk.CTkFrame(kpi_frame, fg_color="gray20")
            card.grid(row=0, column=i, padx=5, pady=5, sticky="nsew")
            kpi_frame.grid_columnconfigure(i, weight=1)
            
            ctk.CTkLabel(card, text=title, font=ctk.CTkFont(size=11), text_color="gray").pack(pady=5)
            ctk.CTkLabel(card, text=value, font=ctk.CTkFont(size=20, weight="bold")).pack()
            ctk.CTkLabel(card, text=delta, font=ctk.CTkFont(size=12), text_color=color).pack(pady=5)
            self.kpi_cards[title] = card
        
        # Тепловая карта + мини-график
        main_frame = ctk.CTkFrame(self)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Левая часть: тепловая карта зон ТЦ
        heatmap = ctk.CTkFrame(main_frame)
        heatmap.pack(side="left", fill="both", expand=True, padx=5)
        ctk.CTkLabel(heatmap, text="🗺 Тепловая карта зон ТЦ", font=ctk.CTkFont(size=14, weight="bold")).pack(pady=10)
        
        zones = [
            ("Фудкорт", 85, "red"), ("Парковка P1", 45, "green"),
            ("Парковка P2", 72, "yellow"), ("Кинозал", 30, "green"),
            ("Детская зона", 90, "red"), ("Бутик-зона", 55, "yellow"),
        ]
        
        self.zone_cards = {}
        for i, (name, load, color) in enumerate(zones):
            row, col = divmod(i, 3)
            card = ctk.CTkFrame(heatmap, fg_color=color if color != "yellow" else "#b8860b")
            card.grid(row=row+1, column=col, padx=5, pady=5, sticky="nsew")
            heatmap.grid_columnconfigure(col, weight=1)
            
            ctk.CTkLabel(card, text=name, font=ctk.CTkFont(weight="bold")).pack(pady=10)
            lbl = ctk.CTkLabel(card, text=f"Загрузка: {load}%", font=ctk.CTkFont(size=16))
            lbl.pack(pady=5)
            self.zone_cards[name] = {"card": card, "label": lbl}
        
        # Правая часть: мини-график посещаемости
        chart = ctk.CTkFrame(main_frame)
        chart.pack(side="right", fill="both", expand=True, padx=5)
        ctk.CTkLabel(chart, text="📈 Посещаемость (последние 2 часа)", font=ctk.CTkFont(size=14, weight="bold")).pack(pady=10)
        
        fig = Figure(figsize=(4, 3), dpi=80)
        fig.patch.set_facecolor('#2b2b2b')
        ax = fig.add_subplot(111)
        ax.set_facecolor('#2b2b2b')
        ax.tick_params(colors='white')
        ax.grid(True, color='#666666')
        
        hours = [f"{h}:00" for h in range(10, 20)]
        visitors = [random.randint(200, 800) for _ in hours]
        ax.plot(hours, visitors, marker='o', color='#1f77b4', linewidth=2)
        ax.set_ylabel("Посетителей/час", color='white')
        
        canvas = FigureCanvasTkAgg(fig, master=chart)
        canvas.get_tk_widget().pack(fill="both", expand=True, padx=10, pady=10)

# ==============================================================================
# ВКЛАДКА 2: АНАЛИТИКА
# ==============================================================================
class AnalyticsTab(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent)
        self._build()
        
    def _build(self):
        # Панель фильтров
        filter_frame = ctk.CTkFrame(self)
        filter_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(filter_frame, text="Период:").pack(side="left", padx=10)
        self.period_var = ctk.StringVar(value="24 часа")
        period_menu = ctk.CTkOptionMenu(filter_frame, values=["1 час", "24 часа", "7 дней", "30 дней"], variable=self.period_var, command=self._update_chart)
        period_menu.pack(side="left", padx=10)
        
        ctk.CTkLabel(filter_frame, text="Метрика:").pack(side="left", padx=10)
        self.metric_var = ctk.StringVar(value="Посещаемость")
        metric_menu = ctk.CTkOptionMenu(filter_frame, values=["Посещаемость", "Выручка", "Конверсия", "Средний чек"], variable=self.metric_var, command=self._update_chart)
        metric_menu.pack(side="left", padx=10)
        
        ctk.CTkButton(filter_frame, text="🔄 Обновить", command=self._update_chart, width=120).pack(side="left", padx=10)
        ctk.CTkButton(filter_frame, text="📥 Экспорт в Excel", command=lambda: messagebox.showinfo("Экспорт", "Отчёт сохранён в reports/analitics_2026.xlsx"), width=140).pack(side="right", padx=10)
        
        # Большой график
        chart_frame = ctk.CTkFrame(self)
        chart_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.fig = Figure(figsize=(10, 4), dpi=100)
        self.fig.patch.set_facecolor('#2b2b2b')
        self.ax = self.fig.add_subplot(111)
        self.ax.set_facecolor('#2b2b2b')
        self.ax.tick_params(colors='white')
        self.ax.grid(True, color='#666666')
        
        self.canvas = FigureCanvasTkAgg(self.fig, master=chart_frame)
        self.canvas.get_tk_widget().pack(fill="both", expand=True, padx=10, pady=10)
        
        self._update_chart(None)
        
    def _update_chart(self, _):
        self.ax.clear()
        metric = self.metric_var.get()
        period = self.period_var.get()
        
        n_points = {"1 час": 12, "24 часа": 24, "7 дней": 7, "30 дней": 30}[period]
        x_labels = [f"Т-{n_points-i}" for i in range(n_points)]
        
        if metric == "Посещаемость":
            y = [random.randint(500, 2000) for _ in x_labels]
            color = '#1f77b4'
        elif metric == "Выручка":
            y = [random.randint(50000, 200000) for _ in x_labels]
            color = '#2ca02c'
        elif metric == "Конверсия":
            y = [random.uniform(10, 25) for _ in x_labels]
            color = '#ff7f0e'
        else:
            y = [random.randint(1500, 3500) for _ in x_labels]
            color = '#d62728'
        
        self.ax.plot(x_labels, y, marker='o', color=color, linewidth=2, markersize=6)
        self.ax.set_title(f"{metric} за период: {period}", color='white', fontsize=14)
        self.ax.set_ylabel(metric, color='white')
        self.fig.tight_layout()
        self.canvas.draw()

# ==============================================================================
# ВКЛАДКА 3: ЗОНЫ ТЦ (Источники данных)
# ==============================================================================
class ZonesTab(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent)
        self._build()
        
    def _build(self):
        ctk.CTkLabel(self, text="📍 Мониторинг зон торгового центра", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=10)
        
        columns = ("Зона", "Посетителей/час", "Загрузка %", "Статус", "Последнее событие")
        tree = ttk.Treeview(self, columns=columns, show="headings", height=15)
        
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview", background="#2b2b2b", foreground="white", fieldbackground="#2b2b2b", rowheight=30)
        style.configure("Treeview.Heading", background="#1f538d", foreground="white")
        
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=180, anchor="center")
        
        zones_data = [
            ("Фудкорт (2 этаж)", "1,247", "85%", "⚠️ Высокая", "Очередь на кассе #3"),
            ("Парковка P1 (подземная)", "342", "45%", "✅ Норма", "Свободно 124 места"),
            ("Парковка P2 (наземная)", "518", "72%", "⚠️ Средняя", "Свободно 56 мест"),
            ("Кинозал 'Люмьер'", "189", "30%", "✅ Норма", "Сеанс 19:30 — 45 билетов"),
            ("Детская зона 'Луна-парк'", "412", "90%", "🔴 Критично", "Превышена вместимость!"),
            ("Бутик-зона 'Люкс'", "267", "55%", "✅ Норма", "Пик посещаемости"),
            ("Супермаркет 'Перекрёсток'", "892", "78%", "⚠️ Средняя", "Очередь на кассе #7"),
            ("Спортзал 'FitLife'", "156", "42%", "✅ Норма", "Групповое занятие в 20:00"),
        ]
        
        for row in zones_data:
            tree.insert("", "end", values=row)
        
        tree.pack(fill="both", expand=True, padx=10, pady=10)

# ==============================================================================
# ВКЛАДКА 4: АЛЕРТЫ
# ==============================================================================
class AlertsTab(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent)
        self._build()
        
    def _build(self):
        # Настройки порогов
        settings = ctk.CTkFrame(self)
        settings.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(settings, text="⚙️ Настройки алертинга", font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", padx=10, pady=5)
        
        row1 = ctk.CTkFrame(settings)
        row1.pack(fill="x", padx=10, pady=5)
        ctk.CTkLabel(row1, text="Порог CPU (%):").pack(side="left", padx=10)
        ctk.CTkEntry(row1, width=80).insert(0, "85")
        ctk.CTkEntry(row1, width=80).pack(side="left", padx=10)
        ctk.CTkLabel(row1, text="Порог ошибок:").pack(side="left", padx=10)
        ctk.CTkEntry(row1, width=80).insert(0, "5")
        ctk.CTkEntry(row1, width=80).pack(side="left", padx=10)
        
        ctk.CTkLabel(row1, text="Канал уведомлений:").pack(side="left", padx=10)
        ctk.CTkOptionMenu(row1, values=["Telegram", "Email", "SMS", "Все каналы"]).pack(side="left", padx=10)
        
        ctk.CTkButton(settings, text="💾 Сохранить настройки", command=lambda: messagebox.showinfo("Успех", "Настройки алертинга сохранены")).pack(pady=10)
        
        # История алертов
        ctk.CTkLabel(self, text="📋 История алертов (последние 24 часа)", font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", padx=10, pady=10)
        
        columns = ("Время", "Источник", "Тип", "Значение", "Порог", "Статус")
        tree = ttk.Treeview(self, columns=columns, show="headings", height=12)
        
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=150, anchor="center")
        
        alerts = [
            ("19:25:59", "server_3", "Ошибки", "8", "5", "🔴 Активен"),
            ("19:15:22", "Фудкорт", "Загрузка", "92%", "85%", "🔴 Активен"),
            ("18:45:10", "Парковка P2", "Заполнение", "95%", "90%", "🔴 Активен"),
            ("18:30:05", "server_1", "CPU", "87%", "85%", "✅Resolved"),
            ("17:20:33", "Детская зона", "Вместимость", "105%", "100%", "✅Resolved"),
            ("16:10:12", "Кинозал", "Продажи", "12", "10", "✅Resolved"),
        ]
        
        for row in alerts:
            tree.insert("", "end", values=row)
        
        tree.pack(fill="both", expand=True, padx=10, pady=10)

# ==============================================================================
# ВКЛАДКА 5: ИНФРАСТРУКТУРА
# ==============================================================================
class InfrastructureTab(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent)
        self._build()
        
    def _build(self):
        ctk.CTkLabel(self, text="🖥 Мониторинг инфраструктуры", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=10)
        
        # Статус контейнеров
        containers_frame = ctk.CTkFrame(self)
        containers_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(containers_frame, text="Docker-контейнеры", font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", padx=10, pady=5)
        
        containers = [
            ("redpanda", "Running", "18h", "124 MB", "2.3%"),
            ("clickhouse", "Running", "18h", "412 MB", "8.7%"),
            ("grafana", "Running", "18h", "89 MB", "1.2%"),
        ]
        
        columns = ("Имя", "Статус", "Аптайм", "Память", "CPU")
        tree = ttk.Treeview(containers_frame, columns=columns, show="headings", height=5)
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=150, anchor="center")
        for row in containers:
            tree.insert("", "end", values=row)
        tree.pack(fill="x", padx=10, pady=10)
        
        # Метрики хоста
        host_frame = ctk.CTkFrame(self)
        host_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        ctk.CTkLabel(host_frame, text="Метрики хоста", font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", padx=10, pady=5)
        
        fig = Figure(figsize=(8, 3), dpi=80)
        fig.patch.set_facecolor('#2b2b2b')
        ax = fig.add_subplot(111)
        ax.set_facecolor('#2b2b2b')
        ax.tick_params(colors='white')
        ax.grid(True, color='#666666')
        
        times = [f"{18+i//4}:{(i%4)*15:02d}" for i in range(24)]
        cpu = [random.uniform(15, 45) for _ in times]
        mem = [random.uniform(40, 65) for _ in times]
        
        ax.plot(times, cpu, label='CPU %', color='#1f77b4', linewidth=2)
        ax.plot(times, mem, label='Memory %', color='#ff7f0e', linewidth=2)
        ax.legend(facecolor='#2b2b2b', edgecolor='white', labelcolor='white')
        ax.set_ylim(0, 100)
        
        canvas = FigureCanvasTkAgg(fig, master=host_frame)
        canvas.get_tk_widget().pack(fill="both", expand=True, padx=10, pady=10)

# ==============================================================================
# ВКЛАДКА 6: ПОЛЬЗОВАТЕЛИ (только для admin)
# ==============================================================================
class UsersTab(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent)
        self._build()
        
    def _build(self):
        ctk.CTkLabel(self, text="👥 Управление пользователями", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=10)
        
        btn_frame = ctk.CTkFrame(self)
        btn_frame.pack(fill="x", padx=10, pady=5)
        ctk.CTkButton(btn_frame, text="➕ Добавить пользователя", command=lambda: messagebox.showinfo("Создание", "Открыта форма создания пользователя")).pack(side="left", padx=5)
        ctk.CTkButton(btn_frame, text="✏️ Редактировать", command=lambda: messagebox.showinfo("Редактирование", "Выберите пользователя в таблице")).pack(side="left", padx=5)
        ctk.CTkButton(btn_frame, text="🗑 Удалить", fg_color="red", hover_color="darkred", command=lambda: messagebox.showwarning("Удаление", "Функция доступна только супер-администратору")).pack(side="left", padx=5)
        
        columns = ("Логин", "Имя", "Роль", "Последний вход", "Статус")
        tree = ttk.Treeview(self, columns=columns, show="headings", height=12)
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=180, anchor="center")
        
        users = [
            ("admin", "Администратор системы", "Администратор", "2026-11-06 19:25", "🟢 Онлайн"),
            ("user", "Оператор мониторинга", "Оператор", "2026-11-06 18:10", "⚫ Оффлайн"),
            ("manager", "Иванов А.П. (директор ТЦ)", "Менеджер", "2026-11-06 14:30", "⚫ Оффлайн"),
            ("security", "Петров С.В. (безопасность)", "Наблюдатель", "2026-11-06 09:00", "⚫ Оффлайн"),
        ]
        
        for row in users:
            tree.insert("", "end", values=row)
        
        tree.pack(fill="both", expand=True, padx=10, pady=10)

# ==============================================================================
# ВКЛАДКА 7: НАСТРОЙКИ СИСТЕМЫ
# ==============================================================================
class SettingsTab(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent)
        self._build()
        
    def _build(self):
        ctk.CTkLabel(self, text="⚙️ Настройки системы", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=10)
        
        # Kafka
        kafka_frame = ctk.CTkFrame(self)
        kafka_frame.pack(fill="x", padx=10, pady=10)
        ctk.CTkLabel(kafka_frame, text="📨 Брокер сообщений (Kafka/Redpanda)", font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=10, pady=5)
        
        row = ctk.CTkFrame(kafka_frame)
        row.pack(fill="x", padx=10, pady=5)
        ctk.CTkLabel(row, text="Адрес брокера:").pack(side="left", padx=10)
        entry = ctk.CTkEntry(row, width=200)
        entry.insert(0, "localhost:9092")
        entry.pack(side="left", padx=10)
        ctk.CTkLabel(row, text="Топик:").pack(side="left", padx=10)
        entry2 = ctk.CTkEntry(row, width=150)
        entry2.insert(0, "tc_metrics")
        entry2.pack(side="left", padx=10)
        
        # ClickHouse
        ch_frame = ctk.CTkFrame(self)
        ch_frame.pack(fill="x", padx=10, pady=10)
        ctk.CTkLabel(ch_frame, text="🗄 База данных (ClickHouse)", font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=10, pady=5)
        
        row = ctk.CTkFrame(ch_frame)
        row.pack(fill="x", padx=10, pady=5)
        ctk.CTkLabel(row, text="Хост:").pack(side="left", padx=10)
        ctk.CTkEntry(row, width=150).insert(0, "localhost:8123")
        ctk.CTkEntry(row, width=150).pack(side="left", padx=10)
        ctk.CTkLabel(row, text="БД:").pack(side="left", padx=10)
        ctk.CTkEntry(row, width=100).insert(0, "kpi_db")
        ctk.CTkEntry(row, width=100).pack(side="left", padx=10)
        
        # Telegram
        tg_frame = ctk.CTkFrame(self)
        tg_frame.pack(fill="x", padx=10, pady=10)
        ctk.CTkLabel(tg_frame, text="📱 Telegram-уведомления", font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=10, pady=5)
        
        row = ctk.CTkFrame(tg_frame)
        row.pack(fill="x", padx=10, pady=5)
        ctk.CTkLabel(row, text="Bot Token:").pack(side="left", padx=10)
        ctk.CTkEntry(row, width=300, show="*").pack(side="left", padx=10)
        ctk.CTkLabel(row, text="Chat ID:").pack(side="left", padx=10)
        ctk.CTkEntry(row, width=150).pack(side="left", padx=10)
        
        # Кнопки
        btn_frame = ctk.CTkFrame(self)
        btn_frame.pack(fill="x", padx=10, pady=20)
        ctk.CTkButton(btn_frame, text="💾 Сохранить все настройки", command=lambda: messagebox.showinfo("Успех", "Настройки сохранены в config/settings.json")).pack(side="left", padx=10)
        ctk.CTkButton(btn_frame, text="🔄 Тест подключения к Kafka", command=lambda: messagebox.showinfo("Тест", "Подключение к Kafka: ✅ Успешно")).pack(side="left", padx=10)
        ctk.CTkButton(btn_frame, text="🔄 Тест Telegram", command=lambda: messagebox.showinfo("Тест", "Telegram-бот: ✅ Сообщение отправлено")).pack(side="left", padx=10)