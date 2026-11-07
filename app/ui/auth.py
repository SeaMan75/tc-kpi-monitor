import customtkinter as ctk
from tkinter import messagebox

# База пользователей (в реальном проекте — в БД)
USERS_DB = {
    'admin': {'password': 'admin', 'role': 'admin', 'name': 'Администратор системы'},
    'user':  {'password': 'user',  'role': 'user',  'name': 'Оператор мониторинга'},
}

class LoginWindow:
    def __init__(self, on_success):
        self.on_success = on_success
        self.window = ctk.CTk()
        self.window.title("Вход в систему мониторинга KPI")
        self.window.geometry("400x380")
        self.window.resizable(False, False)
        self.window.protocol("WM_DELETE_WINDOW", self._on_close)
        ctk.set_appearance_mode("dark")
        
        self._build_ui()
        
    def _build_ui(self):
        ctk.CTkLabel(self.window, text="🔐 Авторизация", font=ctk.CTkFont(size=24, weight="bold")).pack(pady=30)
        
        frame = ctk.CTkFrame(self.window)
        frame.pack(padx=30, pady=10, fill="x")
        
        ctk.CTkLabel(frame, text="Логин:").pack(padx=10, pady=(10, 5), anchor="w")
        self.entry_login = ctk.CTkEntry(frame, placeholder_text="Введите логин")
        self.entry_login.pack(padx=10, pady=5, fill="x")
        
        ctk.CTkLabel(frame, text="Пароль:").pack(padx=10, pady=(10, 5), anchor="w")
        self.entry_pass = ctk.CTkEntry(frame, placeholder_text="Введите пароль", show="*")
        self.entry_pass.pack(padx=10, pady=(5, 10), fill="x")
        self.entry_pass.bind("<Return>", lambda e: self._login())
        
        self.btn_login = ctk.CTkButton(self.window, text="Войти", command=self._login, fg_color="#1f538d", hover_color="#143d6b")
        self.btn_login.pack(pady=20, padx=30, fill="x")
        
        self.lbl_hint = ctk.CTkLabel(self.window, text="admin/admin — администратор\nuser/user — оператор", text_color="gray", font=ctk.CTkFont(size=11))
        self.lbl_hint.pack(pady=10)
        
        # Фокус на поле логина
        self.entry_login.focus_set()
        
    def _login(self):
        login = self.entry_login.get().strip()
        password = self.entry_pass.get().strip()
        
        if login in USERS_DB and USERS_DB[login]['password'] == password:
            user_info = USERS_DB[login].copy()
            user_info['login'] = login
            # НЕ уничтожаем окно сразу — передаём управление дальше
            self.on_success(user_info, self.window)
        else:
            messagebox.showerror("Ошибка", "Неверный логин или пароль")
            self.entry_pass.delete(0, 'end')
            self.entry_pass.focus_set()
            
    def _on_close(self):
        """Обработка крестика — закрываем всё приложение"""
        import sys
        sys.exit(0)
            
    def run(self):
        self.window.mainloop()