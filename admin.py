"""
Административная панель для салона красоты
Отображает все текущие записи клиентов
"""

import tkinter as tk
from tkinter import ttk
from datetime import datetime, timedelta
from typing import List, Dict
from sqlalchemy.orm import Session
from db_config import get_db
from models import Booking, Client, Service, Master
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AdminPanel:
    def __init__(self):
        self.window = tk.Tk()
        self.window.title("Beauty Salon Admin")
        self.window.geometry("1200x700")
        
        self._setup_ui()
        self._load_bookings()
        
    def _setup_ui(self):
        # Основные фреймы
        control_frame = ttk.Frame(self.window, padding="10")
        control_frame.pack(fill=tk.X)
        
        display_frame = ttk.Frame(self.window)
        display_frame.pack(fill=tk.BOTH, expand=True)

        # Элементы управления
        ttk.Button(control_frame, text="🔄 Обновить", command=self._load_bookings).pack(side=tk.LEFT)
        ttk.Button(control_frame, text="📅 Сегодня", command=lambda: self._load_bookings("today")).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="📆 Неделя", command=lambda: self._load_bookings("week")).pack(side=tk.LEFT)
        
        # Таблица записей
        columns = ("id", "client", "phone", "service", "master", "date", "time", "duration")
        self.bookings_tree = ttk.Treeview(
            display_frame, 
            columns=columns, 
            show="headings",
            selectmode="browse"
        )
        
        # Настройка колонок
        self.bookings_tree.heading("id", text="ID")
        self.bookings_tree.column("id", width=50, anchor=tk.CENTER)
        
        self.bookings_tree.heading("client", text="Клиент")
        self.bookings_tree.column("client", width=150)
        
        self.bookings_tree.heading("phone", text="Телефон")
        self.bookings_tree.column("phone", width=120)
        
        self.bookings_tree.heading("service", text="Услуга")
        self.bookings_tree.column("service", width=150)
        
        self.bookings_tree.heading("master", text="Мастер") 
        self.bookings_tree.column("master", width=150)
        
        self.bookings_tree.heading("date", text="Дата")
        self.bookings_tree.column("date", width=100, anchor=tk.CENTER)
        
        self.bookings_tree.heading("time", text="Время")
        self.bookings_tree.column("time", width=80, anchor=tk.CENTER)
        
        self.bookings_tree.heading("duration", text="Длительность")
        self.bookings_tree.column("duration", width=100, anchor=tk.CENTER)
        
        # Скроллбар
        scrollbar = ttk.Scrollbar(display_frame, orient=tk.VERTICAL, command=self.bookings_tree.yview)
        self.bookings_tree.configure(yscroll=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.bookings_tree.pack(fill=tk.BOTH, expand=True)
        
        # Контекстное меню
        self.menu = tk.Menu(self.window, tearoff=0)
        self.menu.add_command(label="Отменить запись", command=self._cancel_booking)
        self.bookings_tree.bind("<Button-3>", self._show_context_menu)

    def _load_bookings(self, period: str = "all"):
        self.bookings_tree.delete(*self.bookings_tree.get_children())
        
        db: Session = next(get_db())
        try:
            query = db.query(Booking).filter(Booking.status == 'confirmed')
            
            if period == "today":
                today = datetime.now().date()
                query = query.filter(Booking.date == today)
            elif period == "week":
                start_date = datetime.now().date()
                end_date = start_date + timedelta(days=7)
                query = query.filter(Booking.date >= start_date, Booking.date <= end_date)
            
            bookings = query.order_by(Booking.date, Booking.start_time).all()
            
            for booking in bookings:
                self.bookings_tree.insert("", tk.END, values=(
                    booking.id,
                    booking.client.name,
                    booking.client.phone,
                    booking.service.name,
                    booking.master.name,
                    booking.date.strftime("%Y-%m-%d"),
                    booking.start_time,
                    f"{booking.service.duration} мин"
                ))
                
        except Exception as e:
            logger.error(f"Error loading bookings: {e}")
            tk.messagebox.showerror("Ошибка", "Не удалось загрузить записи")
        finally:
            db.close()

    def _show_context_menu(self, event):
        item = self.bookings_tree.identify_row(event.y)
        if item:
            self.bookings_tree.selection_set(item)
            self.menu.post(event.x_root, event.y_root)

    def _cancel_booking(self):
        selected_item = self.bookings_tree.selection()
        if not selected_item:
            return
            
        booking_id = self.bookings_tree.item(selected_item)['values'][0]
        
        db: Session = next(get_db())
        try:
            booking = db.query(Booking).get(booking_id)
            if booking:
                booking.status = 'cancelled'
                db.commit()
                self._load_bookings()
                tk.messagebox.showinfo("Успех", "Запись отменена")
        except Exception as e:
            db.rollback()
            logger.error(f"Error cancelling booking: {e}")
            tk.messagebox.showerror("Ошибка", "Не удалось отменить запись")
        finally:
            db.close()

    def run(self):
        self.window.mainloop()


if __name__ == "__main__":
    app = AdminPanel()
    app.run()