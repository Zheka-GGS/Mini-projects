import tkinter as tk
from tkinter import ttk, messagebox, Toplevel
import requests
from bs4 import BeautifulSoup
import threading
import time
from datetime import datetime
import json
import os
import ttkbootstrap as tb
from ttkbootstrap.constants import *
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.dates as mdates
from collections import deque
import webbrowser

class CurrencyTracker:
    def __init__(self, root):
        self.root = root
        self.root.title("💰 Currency Tracker Pro")
        self.root.geometry("1000x700")
        self.root.resizable(True, True)
        
        # Темы
        self.themes = ["darkly", "flatly", "cosmo", "journal", "litera", "lumen", "minty", "pulse", "sandstone", "united", "yeti", "morph", "simplex", "cerculean", "solar", "superhero", "vapor"]
        self.current_theme = "darkly"
        
        # Данные о валютах
        self.currencies = []
        self.currency_widgets = {}
        self.price_history = {}  # История цен для графиков
        self.load_currencies()
        
        # Настройка стилей
        self.setup_styles()
        
        # Интерфейс
        self.setup_ui()
        
        # Запуск обновления
        self.update_currencies()
        self.start_auto_update()
        
    def apply_theme(self):
        self.style.theme_use(self.current_theme)
        self.root.update_idletasks()
    
    def setup_styles(self):
        self.style = tb.Style()
        self.style.configure("Card.TFrame", relief="raised", borderwidth=2)
        self.style.configure("Positive.TLabel", foreground="green")
        self.style.configure("Negative.TLabel", foreground="red")
        self.style.configure("Neutral.TLabel", foreground="blue")
        self.style.configure("Title.TLabel", font=("Helvetica", 28, "bold"))
        self.style.configure("Currency.TLabel", font=("Helvetica", 12, "bold"))
        self.style.configure("Price.TLabel", font=("Helvetica", 14, "bold"))
        self.style.configure("Change.TLabel", font=("Helvetica", 10))
    
    def load_currencies(self):
        """Завантаження збережених валют"""
        try:
            if os.path.exists('currencies.json'):
                with open('currencies.json', 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.currencies = data.get('currencies', [])
                    # Валидация данных
                    for currency in self.currencies:
                        if not all(key in currency for key in ['code', 'name']):
                            self.currencies = []
                            break
        except (json.JSONDecodeError, KeyError, TypeError) as e:
            print(f"Помилка завантаження JSON: {e}. Використовуються стандартні налаштування.")
            self.currencies = []
        
        # Если нет валют, добавляем дефолтные
        if not self.currencies:
            self.currencies = [
                {'code': 'usd', 'name': 'Долар США', 'last_price': None, 'current_price': None}
            ]
    
    def save_currencies(self):
        """Збереження списку валют"""
        data = {'currencies': []}
        for currency in self.currencies:
            # Копіюємо тільки дані, без віджетів
            currency_data = {
                'code': currency['code'],
                'name': currency['name'],
                'last_price': currency.get('last_price'),
                'current_price': currency.get('current_price')
            }
            data['currencies'].append(currency_data)
        
        try:
            with open('currencies.json', 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Помилка збереження: {e}")
    
    def setup_ui(self):
        # Главный контейнер
        self.main_container = tb.Frame(self.root, padding=20)
        self.main_container.pack(fill=BOTH, expand=YES)
        
        # Верхняя панель
        self.setup_top_bar()
        
        # Панель добавления валюты
        self.setup_add_currency()
        
        # Панель валют
        self.setup_currency_panel()
        
        # Статус бар
        self.setup_status_bar()
    
    def setup_add_currency(self):
        add_frame = ttk.LabelFrame(
            self.main_container,
            text="➕ Добавить валюту",
            padding=15
        )
        add_frame.pack(fill=X, pady=(0, 20))
        
        # Левая часть - ввод
        input_frame = tb.Frame(add_frame)
        input_frame.pack(side=LEFT, fill=Y)
        
        tb.Label(input_frame, text="Код валюты:").pack(side=LEFT, padx=(0, 10))
        
        self.currency_entry = ttk.Entry(input_frame, width=8)
        self.currency_entry.pack(side=LEFT, padx=(0, 10))
        self.currency_entry.insert(0, "usd")
        
        add_btn = tb.Button(
            input_frame,
            text="Добавить",
            command=self.add_currency,
            bootstyle="success"
        )
        add_btn.pack(side=LEFT)
        
        # Правая часть - популярные валюты
        popular_frame = tb.Frame(add_frame)
        popular_frame.pack(side=RIGHT, fill=Y)
        
        tb.Label(popular_frame, text="Популярные:").pack(side=LEFT, padx=(0, 5))
        
        popular_currencies = ["USD", "EUR", "GBP", "PLN", "CHF"]
        for code in popular_currencies:
            btn = tb.Button(
                popular_frame,
                text=code,
                command=lambda c=code: self.quick_add_currency(c),
                bootstyle="outline-secondary",
                width=4
            )
            btn.pack(side=LEFT, padx=2)
    
    def setup_currency_panel(self):
        # Контейнер для валют
        self.currency_container = tb.Frame(self.main_container)
        self.currency_container.pack(fill=BOTH, expand=YES)
        
        # Скроллбар
        scrollbar = ttk.Scrollbar(self.currency_container)
        scrollbar.pack(side=RIGHT, fill=Y)
        
        # Canvas для скроллинга
        self.canvas = tk.Canvas(self.currency_container, yscrollcommand=scrollbar.set, bg=self.style.lookup("TFrame", "background"))
        self.canvas.pack(side=LEFT, fill=BOTH, expand=YES)
        scrollbar.config(command=self.canvas.yview)
        
        # Фрейм внутри canvas
        self.currency_frame = tb.Frame(self.canvas)
        self.canvas.create_window((0, 0), window=self.currency_frame, anchor="nw")
        
        # Обновление скроллинга
        self.currency_frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        
        # Обновляем список валют
        self.update_currency_list()
    
    def setup_top_bar(self):
        top_frame = tb.Frame(self.main_container)
        top_frame.pack(fill=X, pady=(0, 20))
        
        # Заголовок
        title_label = tb.Label(
            top_frame,
            text="💰 Currency Tracker Pro",
            style="Title.TLabel",
            bootstyle="primary"
        )
        title_label.pack(side=LEFT)
        
        # Панель управления
        control_frame = tb.Frame(top_frame)
        control_frame.pack(side=RIGHT)
        
        # Переключатель темы
        theme_label = tb.Label(control_frame, text="Тема:")
        theme_label.pack(side=LEFT, padx=(0, 5))
        
        self.theme_var = tk.StringVar(value=self.current_theme)
        theme_combo = ttk.Combobox(
            control_frame,
            textvariable=self.theme_var,
            values=self.themes,
            width=12
        )
        theme_combo.pack(side=LEFT, padx=(0, 10))
        theme_combo.bind("<<ComboboxSelected>>", self.change_theme)
        
        # Кнопка обновления
        refresh_btn = tb.Button(
            control_frame,
            text="🔄 Обновить",
            command=self.update_currencies,
            bootstyle="success-outline"
        )
        refresh_btn.pack(side=LEFT)
    
    def setup_status_bar(self):
        self.status_frame = tb.Frame(self.main_container)
        self.status_frame.pack(fill=X, pady=(10, 0))
        
        self.status_var = tk.StringVar()
        self.status_var.set("Готов к работе")
        
        status_label = tb.Label(
            self.status_frame,
            textvariable=self.status_var,
            bootstyle="secondary",
            anchor="w"
        )
        status_label.pack(side=LEFT, fill=X, expand=YES)
        
        # Прогресс бар для обновления
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(
            self.status_frame,
            variable=self.progress_var,
            maximum=100
        )
        self.progress_bar.pack(side=RIGHT, fill=X, expand=NO, padx=(10, 0))
    
    def change_theme(self, event=None):
        self.current_theme = self.theme_var.get()
        self.apply_theme()
    
    def quick_add_currency(self, code):
        self.currency_entry.delete(0, tk.END)
        self.currency_entry.insert(0, code.lower())
        self.add_currency()
    
    def update_currency_list(self):
        """Обновление списка валют на экране"""
        for widget in self.currency_frame.winfo_children():
            widget.destroy()
        
        if not self.currencies:
            empty_label = tb.Label(
                self.currency_frame,
                text="📊 Нет добавленных валют\nДобавьте валюту выше для отслеживания",
                bootstyle="secondary",
                font=("Helvetica", 14),
                justify="center"
            )
            empty_label.pack(pady=50)
            return
        
        # Отображение каждой валюты
        for i, currency in enumerate(self.currencies):
            self.create_currency_card(currency, i)
    
    def create_currency_card(self, currency, index):
        """Создание карточки валюты"""
        # Карточка
        card = tb.Frame(self.currency_frame, padding=15, bootstyle="card")
        card.pack(fill=X, pady=5, padx=5)
        
        # Верхняя часть - название и флаги
        header_frame = tb.Frame(card)
        header_frame.pack(fill=X, pady=(0, 10))
        
        # Название валюты
        name_label = tb.Label(
            header_frame,
            text=f"{currency['name']} ({currency['code'].upper()})",
            font=("Helvetica", 14, "bold"),
            bootstyle="primary"
        )
        name_label.pack(side=LEFT)
        
        # Кнопки действий
        actions_frame = tb.Frame(header_frame)
        actions_frame.pack(side=RIGHT)
        
        # График
        chart_btn = tb.Button(
            actions_frame,
            text="📈",
            command=lambda: self.show_chart(currency['code']),
            bootstyle="outline-info",
            width=3
        )
        chart_btn.pack(side=LEFT, padx=2)
        
        # Удалить
        remove_btn = tb.Button(
            actions_frame,
            text="🗑️",
            command=lambda idx=index: self.remove_currency(idx),
            bootstyle="outline-danger",
            width=3
        )
        remove_btn.pack(side=LEFT, padx=2)
        
        # Основная информация
        info_frame = tb.Frame(card)
        info_frame.pack(fill=X)
        
        # Текущий курс
        price_frame = tb.Frame(info_frame)
        price_frame.pack(side=LEFT, padx=(0, 20))
        
        tb.Label(price_frame, text="Курс:", bootstyle="secondary").pack(anchor="w")
        price_text = f"{currency['current_price']:.2f} ₴" if currency['current_price'] else "Загрузка..."
        price_label = tb.Label(
            price_frame,
            text=price_text,
            font=("Helvetica", 16, "bold"),
            bootstyle="success" if currency['current_price'] else "secondary"
        )
        price_label.pack(anchor="w")
        
        # Изменение
        change_frame = tb.Frame(info_frame)
        change_frame.pack(side=LEFT, padx=(0, 20))
        
        tb.Label(change_frame, text="Изменение:", bootstyle="secondary").pack(anchor="w")
        
        if currency.get('last_price') and currency.get('current_price'):
            change = currency['current_price'] - currency['last_price']
            change_percent = (change / currency['last_price']) * 100
            
            if change > 0:
                change_text = f"▲ +{change:.2f} (+{change_percent:.2f}%)"
                change_color = "success"
            elif change < 0:
                change_text = f"▼ {change:.2f} ({change_percent:.2f}%)"
                change_color = "danger"
            else:
                change_text = "→ 0.00 (0.00%)"
                change_color = "secondary"
        else:
            change_text = "Нет данных"
            change_color = "secondary"
        
        change_label = tb.Label(
            change_frame,
            text=change_text,
            font=("Helvetica", 12),
            bootstyle=change_color
        )
        change_label.pack(anchor="w")
        
        # Время последнего обновления
        time_frame = tb.Frame(info_frame)
        time_frame.pack(side=RIGHT)
        
        tb.Label(time_frame, text="Обновлено:", bootstyle="secondary").pack(anchor="w")
        time_text = datetime.now().strftime("%H:%M:%S")
        time_label = tb.Label(
            time_frame,
            text=time_text,
            font=("Helvetica", 10),
            bootstyle="info"
        )
        time_label.pack(anchor="w")
        
        # Сохраняем виджеты
        self.currency_widgets[index] = {
            'price_label': price_label,
            'change_label': change_label,
            'time_label': time_label
        }
    
    def get_currency_price(self, currency_code):
        """Отримання курсу валюти з Minfin"""
        try:
            url = f"https://minfin.com.ua/currency/{currency_code.lower()}/"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Спроба знайти курс через різні селектори
            selectors = [
                'div[data-currency]',
                'span.mfm-black-btn',
                'div.mfm-posr',
                'div.sc-1x32wa2-9',
                'table tr td'
            ]
            
            for selector in selectors:
                elements = soup.select(selector)
                for element in elements:
                    text = element.get_text().strip()
                    # Шукаємо число з плаваючою точкою
                    import re
                    matches = re.findall(r'\d+\.\d+', text.replace(',', '.'))
                    if matches:
                        try:
                            price = float(matches[0])
                            if 1 < price < 1000:  # Реалістичний діапазон для валют
                                return price
                        except:
                            continue
            
            # Альтернативний метод - пошук за класами, які часто використовуються
            price_divs = soup.find_all('div', class_=lambda x: x and 'rate' in str(x).lower())
            for div in price_divs:
                text = div.get_text().strip()
                try:
                    price = float(text.replace(',', '.'))
                    if 1 < price < 1000:
                        return price
                except:
                    continue
            
            return None
        except Exception as e:
            print(f"Помилка отримання курсу {currency_code}: {e}")
            return None
    
    def show_chart(self, currency_code):
        """Показать график изменения курса"""
        if currency_code not in self.price_history:
            messagebox.showinfo("Информация", "Недостаточно данных для построения графика")
            return
        
        history = self.price_history[currency_code]
        if len(history) < 2:
            messagebox.showinfo("Информация", "Недостаточно данных для построения графика")
            return
        
        # Создаем новое окно
        chart_window = Toplevel(self.root)
        chart_window.title(f"График {currency_code.upper()}")
        chart_window.geometry("800x600")
        
        # Фрейм для графика
        chart_frame = tb.Frame(chart_window, padding=20)
        chart_frame.pack(fill=BOTH, expand=YES)
        
        # Создаем график
        fig, ax = plt.subplots(figsize=(8, 6))
        
        times = [entry['time'] for entry in history]
        prices = [entry['price'] for entry in history]
        
        ax.plot(times, prices, marker='o', linestyle='-', color='#2196F3', linewidth=2, markersize=4)
        ax.set_title(f'Изменение курса {currency_code.upper()}', fontsize=16, fontweight='bold')
        ax.set_xlabel('Время', fontsize=12)
        ax.set_ylabel('Курс (₴)', fontsize=12)
        ax.grid(True, alpha=0.3)
        
        # Форматирование оси X
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
        plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)
        
        # Добавляем график в окно
        canvas = FigureCanvasTkAgg(fig, master=chart_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=BOTH, expand=YES)
    
    def update_currencies(self):
        """Обновление курсов всех валют"""
        self.status_var.set("Обновление курсов...")
        self.progress_var.set(0)
        
        def update_thread():
            total = len(self.currencies)
            for i, currency in enumerate(self.currencies):
                new_price = self.get_currency_price(currency['code'])
                
                if new_price:
                    # Инициализируем историю если нужно
                    if currency['code'] not in self.price_history:
                        self.price_history[currency['code']] = deque(maxlen=50)
                    
                    # Добавляем в историю
                    self.price_history[currency['code']].append({
                        'time': datetime.now(),
                        'price': new_price
                    })
                    
                    # Обновляем цены
                    currency['last_price'] = currency.get('current_price')
                    currency['current_price'] = new_price
                    
                    # Обновляем интерфейс
                    self.root.after(0, self.update_currency_display, i)
                
                # Обновляем прогресс
                progress = (i + 1) / total * 100
                self.root.after(0, lambda p=progress: self.progress_var.set(p))
            
            # Обновляем статус
            current_time = datetime.now().strftime("%H:%M:%S")
            self.root.after(0, lambda: self.status_var.set(f"Последнее обновление: {current_time}"))
            self.root.after(0, lambda: self.progress_var.set(0))
        
        # Запускаем в отдельном потоке
        thread = threading.Thread(target=update_thread, daemon=True)
        thread.start()
    
    def update_currency_display(self, index):
        """Обновление отображения валюты"""
        if index >= len(self.currencies) or index not in self.currency_widgets:
            return
            
        currency = self.currencies[index]
        widgets = self.currency_widgets[index]
        
        if widgets.get('price_label'):
            price_text = f"{currency['current_price']:.2f} ₴" if currency['current_price'] else "Ошибка"
            widgets['price_label'].config(text=price_text)
        
        if widgets.get('change_label') and currency.get('last_price') and currency.get('current_price'):
            change = currency['current_price'] - currency['last_price']
            change_percent = (change / currency['last_price']) * 100 if currency['last_price'] else 0
            
            if change > 0:
                change_text = f"▲ +{change:.2f} (+{change_percent:.2f}%)"
                change_color = "success"
            elif change < 0:
                change_text = f"▼ {change:.2f} ({change_percent:.2f}%)"
                change_color = "danger"
            else:
                change_text = "→ 0.00 (0.00%)"
                change_color = "secondary"
            
            widgets['change_label'].config(text=change_text, bootstyle=change_color)
        elif widgets.get('change_label'):
            widgets['change_label'].config(text="Нет данных", bootstyle="secondary")
        
        # Обновляем время
        if widgets.get('time_label'):
            time_text = datetime.now().strftime("%H:%M:%S")
            widgets['time_label'].config(text=time_text)
    
    def add_currency(self):
        """Добавление новой валюты"""
        code = self.currency_entry.get().strip().lower()
        
        if not code:
            messagebox.showwarning("Внимание", "Пожалуйста, введите код валюты")
            return
        
        # Проверка, добавлена ли валюта уже
        for curr in self.currencies:
            if curr['code'] == code:
                messagebox.showwarning("Внимание", "Эта валюта уже добавлена")
                return
        
        # Добавление новой валюты
        currency_names = {
            'usd': 'Доллар США',
            'eur': 'Евро',
            'gbp': 'Фунт стерлингов',
            'pln': 'Злотый',
            'chf': 'Швейцарский франк',
            'cad': 'Канадский доллар',
            'jpy': 'Иена',
            'cny': 'Юань',
            'uah': 'Гривна'
        }
        
        name = currency_names.get(code, code.upper())
        
        new_currency = {
            'code': code,
            'name': name,
            'last_price': None,
            'current_price': None
        }
        
        self.currencies.append(new_currency)
        self.save_currencies()
        self.update_currency_list()
        
        # Обновляем курс новой валюты
        self.update_currencies()
        
        self.currency_entry.delete(0, tk.END)
        self.currency_entry.insert(0, "usd")  # Сбрасываем к умолчанию
        messagebox.showinfo("Успех", f"Валюта {name} добавлена успешно")
    
    def remove_currency(self, index):
        """Удаление валюты"""
        if 0 <= index < len(self.currencies):
            currency_name = self.currencies[index]['name']
            if messagebox.askyesno("Подтверждение", f"Удалить {currency_name}?"):
                # Удаляем валюту
                del self.currencies[index]
                # Очищаем индексированные виджеты
                self.currency_widgets = {}
                
                self.save_currencies()
                self.update_currency_list()
    
    def start_auto_update(self):
        """Запуск автоматичного оновлення"""
        def auto_update():
            while True:
                time.sleep(300)  # Оновлення кожні 5 хвилин
                self.update_currencies()
        
        thread = threading.Thread(target=auto_update, daemon=True)
        thread.start()

def main():
    root = tb.Window(themename="darkly")
    
    app = CurrencyTracker(root)
    root.mainloop()

if __name__ == "__main__":
    main()