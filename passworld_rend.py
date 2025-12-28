import tkinter as tk
from tkinter import ttk, messagebox
import random
import string
import pyperclip
import time

class PasswordGenerator:
    def __init__(self, root):
        self.root = root
        self.root.title("✨ Генератор Паролів")
        self.root.geometry("500x650")
        self.root.configure(bg="#2c3e50")
        self.root.resizable(False, False)
        
        # Стилізація
        self.setup_styles()
        
        # Змінні
        self.password_var = tk.StringVar()
        self.length_var = tk.IntVar(value=12)
        self.uppercase_var = tk.BooleanVar(value=True)
        self.lowercase_var = tk.BooleanVar(value=True)
        self.numbers_var = tk.BooleanVar(value=True)
        self.symbols_var = tk.BooleanVar(value=True)
        self.complexity_var = tk.StringVar(value="medium")
        
        # Анімаційні змінні
        self.animation_running = False
        self.progress_value = 0
        
        # Створення UI
        self.create_widgets()
        
    def setup_styles(self):
        style = ttk.Style()
        style.theme_use('clam')
        
        # Кольори
        self.colors = {
            'bg': '#2c3e50',
            'fg': '#ecf0f1',
            'accent': '#3498db',
            'success': '#2ecc71',
            'warning': '#e74c3c',
            'card_bg': '#34495e',
            'entry_bg': '#ecf0f1',
            'entry_fg': '#2c3e50'
        }
        
    def create_widgets(self):
        # Заголовок
        title_frame = tk.Frame(self.root, bg=self.colors['bg'])
        title_frame.pack(pady=30)
        
        title_label = tk.Label(
            title_frame,
            text="🔐 Генератор Паролів",
            font=("Segoe UI", 24, "bold"),
            fg=self.colors['fg'],
            bg=self.colors['bg']
        )
        title_label.pack()
        
        subtitle_label = tk.Label(
            title_frame,
            text="Створюйте надійні паролі миттєво",
            font=("Segoe UI", 10),
            fg=self.colors['accent'],
            bg=self.colors['bg']
        )
        subtitle_label.pack(pady=(5, 0))
        
        # Картка налаштувань
        settings_card = tk.Frame(
            self.root,
            bg=self.colors['card_bg'],
            relief=tk.FLAT,
            bd=0
        )
        settings_card.pack(pady=20, padx=30, fill=tk.X)
        
        # Довжина пароля
        length_frame = tk.Frame(settings_card, bg=self.colors['card_bg'])
        length_frame.pack(fill=tk.X, padx=20, pady=15)
        
        length_label = tk.Label(
            length_frame,
            text="Довжина пароля:",
            font=("Segoe UI", 11),
            fg=self.colors['fg'],
            bg=self.colors['card_bg']
        )
        length_label.pack(anchor=tk.W)
        
        length_scale = ttk.Scale(
            length_frame,
            from_=6,
            to=32,
            variable=self.length_var,
            orient=tk.HORIZONTAL,
            command=lambda x: self.update_length_label()
        )
        length_scale.pack(fill=tk.X, pady=(5, 0))
        
        self.length_value_label = tk.Label(
            length_frame,
            text="12",
            font=("Segoe UI", 10, "bold"),
            fg=self.colors['accent'],
            bg=self.colors['card_bg']
        )
        self.length_value_label.pack(anchor=tk.E)
        
        # Складність
        complexity_frame = tk.Frame(settings_card, bg=self.colors['card_bg'])
        complexity_frame.pack(fill=tk.X, padx=20, pady=10)
        
        complexity_label = tk.Label(
            complexity_frame,
            text="Складність:",
            font=("Segoe UI", 11),
            fg=self.colors['fg'],
            bg=self.colors['card_bg']
        )
        complexity_label.pack(anchor=tk.W)
        
        complexity_options = [
            ("Низька", "low"),
            ("Середня", "medium"),
            ("Висока", "high"),
            ("Максимальна", "max")
        ]
        
        for text, value in complexity_options:
            rb = ttk.Radiobutton(
                complexity_frame,
                text=text,
                value=value,
                variable=self.complexity_var,
                command=self.update_complexity_settings
            )
            rb.pack(side=tk.LEFT, padx=(0, 15))
        
        # Налаштування символів
        chars_frame = tk.Frame(settings_card, bg=self.colors['card_bg'])
        chars_frame.pack(fill=tk.X, padx=20, pady=15)
        
        options = [
            ("Великі літери (A-Z)", self.uppercase_var),
            ("Малі літери (a-z)", self.lowercase_var),
            ("Цифри (0-9)", self.numbers_var),
            ("Символи (!@#$%)", self.symbols_var)
        ]
        
        for text, var in options:
            cb = tk.Checkbutton(
                chars_frame,
                text=text,
                variable=var,
                font=("Segoe UI", 10),
                fg=self.colors['fg'],
                bg=self.colors['card_bg'],
                selectcolor=self.colors['card_bg'],
                activebackground=self.colors['card_bg'],
                activeforeground=self.colors['fg']
            )
            cb.pack(anchor=tk.W, pady=2)
        
        # Кнопка генерації
        self.generate_btn = tk.Button(
            self.root,
            text="🎲 Згенерувати Пароль",
            font=("Segoe UI", 12, "bold"),
            bg=self.colors['accent'],
            fg="white",
            activebackground="#2980b9",
            activeforeground="white",
            relief=tk.FLAT,
            cursor="hand2",
            height=2,
            command=self.generate_password_with_animation
        )
        self.generate_btn.pack(fill=tk.X, padx=30, pady=(20, 10))
        
        # Прогрес бар для анімації
        self.progress_bar = ttk.Progressbar(
            self.root,
            mode='determinate',
            length=440,
            style="green.Horizontal.TProgressbar"
        )
        self.progress_bar.pack(pady=(0, 20))
        self.progress_bar.pack_forget()  # Приховати поки не потрібно
        
        # Поле результату
        result_frame = tk.Frame(self.root, bg=self.colors['bg'])
        result_frame.pack(fill=tk.X, padx=30, pady=(10, 20))
        
        password_entry = tk.Entry(
            result_frame,
            textvariable=self.password_var,
            font=("Consolas", 14, "bold"),
            bg=self.colors['entry_bg'],
            fg=self.colors['entry_fg'],
            relief=tk.FLAT,
            justify=tk.CENTER,
            bd=0,
            readonlybackground=self.colors['entry_bg']
        )
        password_entry.pack(fill=tk.X, pady=(0, 10))
        password_entry.config(state='readonly')
        
        # Кнопки дій
        buttons_frame = tk.Frame(result_frame, bg=self.colors['bg'])
        buttons_frame.pack(fill=tk.X)
        
        self.copy_btn = tk.Button(
            buttons_frame,
            text="📋 Копіювати",
            font=("Segoe UI", 10),
            bg=self.colors['success'],
            fg="white",
            relief=tk.FLAT,
            cursor="hand2",
            command=self.copy_to_clipboard
        )
        self.copy_btn.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0, 5))
        
        self.regenerate_btn = tk.Button(
            buttons_frame,
            text="🔄 Згенерувати знову",
            font=("Segoe UI", 10),
            bg="#9b59b6",
            fg="white",
            relief=tk.FLAT,
            cursor="hand2",
            command=self.generate_password
        )
        self.regenerate_btn.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(5, 0))
        
        # Статус бар
        self.status_label = tk.Label(
            self.root,
            text="Готовий до генерації пароля",
            font=("Segoe UI", 9),
            fg=self.colors['fg'],
            bg=self.colors['bg']
        )
        self.status_label.pack(pady=(0, 20))
        
    def update_length_label(self):
        self.length_value_label.config(text=str(self.length_var.get()))
        
    def update_complexity_settings(self):
        complexity = self.complexity_var.get()
        
        if complexity == "low":
            self.length_var.set(8)
            self.uppercase_var.set(True)
            self.lowercase_var.set(True)
            self.numbers_var.set(False)
            self.symbols_var.set(False)
        elif complexity == "medium":
            self.length_var.set(12)
            self.uppercase_var.set(True)
            self.lowercase_var.set(True)
            self.numbers_var.set(True)
            self.symbols_var.set(False)
        elif complexity == "high":
            self.length_var.set(16)
            self.uppercase_var.set(True)
            self.lowercase_var.set(True)
            self.numbers_var.set(True)
            self.symbols_var.set(True)
        else:  # max
            self.length_var.set(20)
            self.uppercase_var.set(True)
            self.lowercase_var.set(True)
            self.numbers_var.set(True)
            self.symbols_var.set(True)
            
        self.update_length_label()
        
    def generate_password_with_animation(self):
        if self.animation_running:
            return
            
        self.animation_running = True
        self.progress_bar.pack(pady=(0, 20))
        self.progress_value = 0
        self.progress_bar['value'] = 0
        
        # Анімація прогресу
        def animate():
            if self.progress_value < 100:
                self.progress_value += 5
                self.progress_bar['value'] = self.progress_value
                self.root.after(30, animate)
            else:
                self.progress_bar.pack_forget()
                self.generate_password()
                self.animation_running = False
                
        animate()
        
    def generate_password(self):
        length = self.length_var.get()
        
        # Перевірка, чи вибрані символи
        if not any([self.uppercase_var.get(), self.lowercase_var.get(), 
                   self.numbers_var.get(), self.symbols_var.get()]):
            messagebox.showwarning("Увага", "Будь ласка, оберіть хоча б один тип символів")
            return
            
        # Формування набору символів
        characters = ""
        if self.uppercase_var.get():
            characters += string.ascii_uppercase
        if self.lowercase_var.get():
            characters += string.ascii_lowercase
        if self.numbers_var.get():
            characters += string.digits
        if self.symbols_var.get():
            characters += "!@#$%^&*()_+-=[]{}|;:,.<>?"
            
        # Генерація пароля
        try:
            password = ''.join(random.choice(characters) for _ in range(length))
            self.password_var.set(password)
            
            # Оцінка складності
            strength = self.estimate_password_strength(password)
            strength_colors = {
                "weak": "#e74c3c",
                "medium": "#f39c12",
                "strong": "#2ecc71"
            }
            
            self.status_label.config(
                text=f"Пароль згенеровано! Складність: {strength.upper()}",
                fg=strength_colors.get(strength, self.colors['fg'])
            )
            
            # Анімація копіювання кнопки
            self.animate_button(self.copy_btn, self.colors['success'])
            
        except Exception as e:
            messagebox.showerror("Помилка", f"Не вдалося згенерувати пароль: {str(e)}")
            
    def estimate_password_strength(self, password):
        score = 0
        
        # Перевірка довжини
        if len(password) >= 12:
            score += 2
        elif len(password) >= 8:
            score += 1
            
        # Перевірка на різні типи символів
        if any(c.isupper() for c in password):
            score += 1
        if any(c.islower() for c in password):
            score += 1
        if any(c.isdigit() for c in password):
            score += 1
        if any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password):
            score += 1
            
        # Визначення рівня складності
        if score >= 5:
            return "strong"
        elif score >= 3:
            return "medium"
        else:
            return "weak"
            
    def copy_to_clipboard(self):
        password = self.password_var.get()
        if password:
            pyperclip.copy(password)
            self.status_label.config(
                text="Пароль скопійовано в буфер обміну!",
                fg=self.colors['success']
            )
            self.animate_button(self.copy_btn, "#27ae60")
            
            # Повернення початкового тексту через 2 секунди
            self.root.after(2000, lambda: self.status_label.config(
                text="Готовий до генерації пароля",
                fg=self.colors['fg']
            ))
            
    def animate_button(self, button, color):
        original_color = button.cget("bg")
        button.config(bg=color)
        self.root.after(300, lambda: button.config(bg=original_color))

def main():
    root = tk.Tk()
    app = PasswordGenerator(root)
    root.mainloop()

if __name__ == "__main__":
    main()