import customtkinter as ctk
from tkinter import messagebox
from .tabs import DashboardTab, AnalyticsTab, ZonesTab, AlertsTab, InfrastructureTab, UsersTab, SettingsTab

class KPIMonitorGUI:
    def __init__(self, docker_manager, alert_manager, config, user_info, login_window=None):
        self.docker_manager = docker_manager
        self.alert_manager = alert_manager
        self.config = config
        self.user_info = user_info
        self.login_window = login_window  # сохраняем ссылку
        self.running = False
        
        # ВАЖНО: сначала создаём главное окно, потом уничтожаем логин
        self.root = ctk.CTk()
        self.root.title(f"Система мониторинга KPI ТЦ — {user_info['name']} ({user_info['role']})")
        self.root.geometry("1400x900")
        
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        
        self._build_header()
        self._build_tabs()
        
    def _build_header(self):
        header = ctk.CTkFrame(self.root, height=60)
        header.pack(fill="x")
        header.pack_propagate(False)
        
        ctk.CTkLabel(header, text="🏬 Система мониторинга KPI торгового центра", font=ctk.CTkFont(size=18, weight="bold")).pack(side="left", padx=20, pady=15)
        
        # Инфо о пользователе
        user_frame = ctk.CTkFrame(header, fg_color="transparent")
        user_frame.pack(side="right", padx=20)
        
        ctk.CTkLabel(user_frame, text=f"👤 {self.user_info['name']}", font=ctk.CTkFont(size=12)).pack(side="top")
        role_text = "🔑 Администратор" if self.user_info['role'] == 'admin' else "👁 Оператор"
        ctk.CTkLabel(user_frame, text=role_text, font=ctk.CTkFont(size=11), text_color="gray").pack(side="top")
        
        # Переключатель темы
        self.theme_var = ctk.StringVar(value="dark")
        theme_switch = ctk.CTkSwitch(header, text="🌙/☀️ Тема", variable=self.theme_var, command=self._toggle_theme)
        theme_switch.pack(side="right", padx=20)
        
        # Кнопка выхода
        ctk.CTkButton(header, text="🚪 Выйти", fg_color="red", hover_color="darkred", width=100, command=self._logout).pack(side="right", padx=10)
    
    def _build_tabs(self):
        self.tabview = ctk.CTkTabview(self.root)
        self.tabview.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Добавляем вкладки (с проверкой прав)
        self.tabview.add("📊 Dashboard")
        self.tabview.add("📈 Аналитика")
        self.tabview.add("📍 Зоны ТЦ")
        self.tabview.add("🔔 Алерты")
        self.tabview.add("🖥 Инфраструктура")
        
        if self.user_info['role'] == 'admin':
            self.tabview.add("👥 Пользователи")
            self.tabview.add("⚙️ Настройки")
        
        # Вставляем контент вкладок
        DashboardTab(self.tabview.tab("📊 Dashboard")).pack(fill="both", expand=True)
        AnalyticsTab(self.tabview.tab("📈 Аналитика")).pack(fill="both", expand=True)
        ZonesTab(self.tabview.tab("📍 Зоны ТЦ")).pack(fill="both", expand=True)
        AlertsTab(self.tabview.tab("🔔 Алерты")).pack(fill="both", expand=True)
        InfrastructureTab(self.tabview.tab("🖥 Инфраструктура")).pack(fill="both", expand=True)
        
        if self.user_info['role'] == 'admin':
            UsersTab(self.tabview.tab("👥 Пользователи")).pack(fill="both", expand=True)
            SettingsTab(self.tabview.tab("⚙️ Настройки")).pack(fill="both", expand=True)
    
    def _toggle_theme(self):
        new_theme = "light" if self.theme_var.get() == "dark" else "dark"
        ctk.set_appearance_mode(new_theme)
        self.theme_var.set(new_theme)
        
    def _logout(self):
        if messagebox.askyesno("Выход", "Завершить сеанс?"):
            self.root.destroy()
    
    def run(self):
        self.root.mainloop()