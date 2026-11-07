import customtkinter as ctk
from tkinter import messagebox

USERS_DB = {
    'admin': {'password': 'admin', 'role': 'admin', 'name': 'Администратор системы'},
    'user':  {'password': 'user',  'role': 'user',  'name': 'Оператор мониторинга'},
}

class LoginDialog(ctk.CTkToplevel):
    def __init__(self, parent, on_success):
        super().__init__(parent)
        self.on_success = on_success
        
        self.title("Вход в систему мониторинга KPI")
        self.geometry("400x380")
        self.resizable(False, False)
        
        # Делаем окно модальным (блокирует основное окно до входа)
        self.transient(parent)
        self.grab_set()
        
        # === ИСПРАВЛЕННОЕ ЦЕНТРИРОВАНИЕ ПО ЦЕНТРУ ЭКРАНА ===
        self.update_idletasks()
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        
        # Вычисляем координаты для центра экрана
        x = (screen_width // 2) - (400 // 2)
        y = (screen_height // 2) - (380 // 2)
        
        self.geometry(f"400x380+{x}+{y}")
        # ====================================================
        
        self._build_ui()
        
    def _build_ui(self):
        ctk.CTkLabel(self, text="🔐 Авторизация", font=ctk.CTkFont(size=24, weight="bold")).pack(pady=30)
        
        frame = ctk.CTkFrame(self)
        frame.pack(padx=30, pady=10, fill="x")
        
        ctk.CTkLabel(frame, text="Логин:").pack(padx=10, pady=(10, 5), anchor="w")
        self.entry_login = ctk.CTkEntry(frame, placeholder_text="Введите логин")
        self.entry_login.pack(padx=10, pady=5, fill="x")
        
        ctk.CTkLabel(frame, text="Пароль:").pack(padx=10, pady=(10, 5), anchor="w")
        self.entry_pass = ctk.CTkEntry(frame, placeholder_text="Введите пароль", show="*")
        self.entry_pass.pack(padx=10, pady=(5, 10), fill="x")
        self.entry_pass.bind("<Return>", lambda e: self._login())
        
        self.btn_login = ctk.CTkButton(self, text="Войти", command=self._login, fg_color="#1f538d", hover_color="#143d6b")
        self.btn_login.pack(pady=20, padx=30, fill="x")
        
        self.lbl_hint = ctk.CTkLabel(self, text="admin/admin — администратор\nuser/user — оператор", text_color="gray", font=ctk.CTkFont(size=11))
        self.lbl_hint.pack(pady=10)
        
        self.entry_login.focus_set()
        
    def _login(self):
        login = self.entry_login.get().strip()
        password = self.entry_pass.get().strip()
        
        if login in USERS_DB and USERS_DB[login]['password'] == password:
            user_info = USERS_DB[login].copy()
            user_info['login'] = login
            self.destroy() # Просто закрываем диалог, root остается жив!
            self.on_success(user_info)
        else:
            messagebox.showerror("Ошибка", "Неверный логин или пароль", parent=self)
            self.entry_pass.delete(0, 'end')
            self.entry_pass.focus_set()