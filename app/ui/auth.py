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
        self.window.geometry("400x350")
        self.window.resizable(False, False)
        ctk.set_appearance_mode("dark")
        
        self._build_ui()
        
    def _build_ui(self):
        ctk.CTkLabel(self.window, text="🔐 Авторизация", font=ctk.CTkFont(size=24, weight="bold")).pack(pady=30)
        
        frame = ctk.CTkFrame(self.window)
        frame.pack(padx=30, pady=10, fill="x")
        
        ctk.CTkLabel(frame, text="Логин:").pack(padx=10, pady=5, anchor="w")
        self.entry_login = ctk.CTkEntry(frame, placeholder_text="Введите логин")
        self.entry_login.pack(padx=10, pady=5, fill="x")
        
        ctk.CTkLabel(frame, text="Пароль:").pack(padx=10, pady=5, anchor="w")
        self.entry_pass = ctk.CTkEntry(frame, placeholder_text="Введите пароль", show="*")
        self.entry_pass.pack(padx=10, pady=5, fill="x")
        self.entry_pass.bind("<Return>", lambda e: self._login())
        
        self.btn_login = ctk.CTkButton(self.window, text="Войти", command=self._login, fg_color="#1f538d", hover_color="#143d6b")
        self.btn_login.pack(pady=20, padx=30, fill="x")
        
        self.lbl_hint = ctk.CTkLabel(self.window, text="admin/admin — администратор\nuser/user — оператор", text_color="gray", font=ctk.CTkFont(size=11))
        self.lbl_hint.pack(pady=10)
        
    def _login(self):
        login = self.entry_login.get().strip()
        password = self.entry_pass.get().strip()
        
        if login in USERS_DB and USERS_DB[login]['password'] == password:
            user_info = USERS_DB[login].copy()
            user_info['login'] = login
            self.window.destroy()
            self.on_success(user_info)
        else:
            messagebox.showerror("Ошибка", "Неверный логин или пароль")
            
    def run(self):
        self.window.mainloop()