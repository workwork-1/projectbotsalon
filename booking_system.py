"""
Модуль системы бронирования для салона красоты с SQLite.
"""

from datetime import datetime, time, timedelta
from typing import List, Dict, Optional, Tuple
import logging
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from db_config import get_db, engine
from models import Base, Client, Service, Master, Schedule, Booking

class BookingSystem:
    def __init__(self):
        Base.metadata.create_all(bind=engine)
        self._init_services_and_masters()
        logging.info("Booking system initialized")

    def _init_services_and_masters(self) -> None:
        db = next(get_db())
        try:
            # Проверяем, есть ли уже данные в базе
            if db.query(Service).count() == 0:
                # Стандартные услуги
                services = [
                    Service(name="Женская стрижка", duration=60, price=1500),
                    Service(name="Мужская стрижка", duration=30, price=800),
                    Service(name="Окрашивание", duration=120, price=3000),
                    Service(name="Маникюр", duration=90, price=2000),
                    Service(name="Педикюр", duration=90, price=2500)
                ]
                
                for service in services:
                    db.add(service)
                
                # Мастера
                masters = [
                    Master(name="Анна", specialization="Парикмахер"),
                    Master(name="Елена", specialization="Колорист"),
                    Master(name="Мария", specialization="Мастер маникюра"),
                    Master(name="Ирина", specialization="Мастер педикюра")
                ]
                
                for master in masters:
                    db.add(master)
                
                db.commit()
                
                # Стандартное расписание на 2 недели
                masters = db.query(Master).all()
                for master in masters:
                    for day in range(14):
                        current_date = (datetime.now() + timedelta(days=day)).date()
                        if current_date.weekday() < 5:  # Только будни
                            schedule = Schedule(
                            master_id=master.id,
                            date=current_date,  # Передаем date object
                            start_time="10:00",
                            end_time="19:00"
                        )
                        db.add(schedule)

                
                db.commit()
            
        except Exception as e:
            db.rollback()
            logging.error(f"Error initializing database: {e}")
            raise
        finally:
            db.close()

    def add_client(self, name: str, phone: str, telegram_id: Optional[int] = None) -> Optional[int]:
        db = next(get_db())
        try:
            existing_client = db.query(Client).filter(
                (Client.phone == phone) | (Client.telegram_id == telegram_id)
            ).first()
            
            if existing_client:
                return existing_client.id
            
            client = Client(name=name, phone=phone, telegram_id=telegram_id)
            db.add(client)
            db.commit()
            return client.id
            
        except IntegrityError:
            db.rollback()
            client = db.query(Client).filter(Client.phone == phone).first()
            return client.id if client else None
        except Exception as e:
            db.rollback()
            logging.error(f"Error adding client: {e}")
            return None
        finally:
            db.close()

    def get_client_id(self, phone: Optional[str] = None, telegram_id: Optional[int] = None) -> Optional[int]:
        db = next(get_db())
        try:
            query = db.query(Client)
            if phone:
                client = query.filter(Client.phone == phone).first()
            elif telegram_id:
                client = query.filter(Client.telegram_id == telegram_id).first()
            else:
                return None
            return client.id if client else None
        finally:
            db.close()

    def get_all_services(self) -> List[Dict]:
        db = next(get_db())
        try:
            services = db.query(Service).all()
            return [
                {
                    'id': s.id,
                    'name': s.name,
                    'duration': s.duration,
                    'price': s.price
                }
                for s in services
            ]
        finally:
            db.close()

    def get_service_by_id(self, service_id: int) -> Optional[Dict]:
        db = next(get_db())
        try:
            service = db.query(Service).filter(Service.id == service_id).first()
            if service:
                return {
                    'id': service.id,
                    'name': service.name,
                    'duration': service.duration,
                    'price': service.price
                }
            return None
        finally:
            db.close()

    def get_all_masters(self) -> List[Dict]:
        db = next(get_db())
        try:
            masters = db.query(Master).all()
            return [
                {
                    'id': m.id,
                    'name': m.name,
                    'specialization': m.specialization
                }
                for m in masters
            ]
        finally:
            db.close()

    def get_masters_for_service(self, service_id: int) -> List[Dict]:
        return self.get_all_masters()

    def get_available_slots(self, master_id: int, date: str, service_duration: int) -> List[Dict]:
        db = next(get_db())
        try:
            schedule = db.query(Schedule).filter(
                Schedule.master_id == master_id,
                Schedule.date == date
            ).first()
            
            if not schedule:
                return []
            
            work_start = datetime.strptime(schedule.start_time, "%H:%M").time()
            work_end = datetime.strptime(schedule.end_time, "%H:%M").time()
            
            booked_slots = db.query(Booking).filter(
                Booking.master_id == master_id,
                Booking.date == date,
                Booking.status == 'confirmed'
            ).all()
            
            booked_times = [
                (
                    datetime.strptime(b.start_time, "%H:%M").time(),
                    datetime.strptime(b.end_time, "%H:%M").time()
                )
                for b in booked_slots
            ]
            
            available_slots = []
            current_time = work_start
            
            while True:
                end_time = (datetime.combine(datetime.today(), current_time) + 
                           timedelta(minutes=service_duration)).time()
                
                if end_time > work_end:
                    break
                
                slot_available = True
                for booked_start, booked_end in booked_times:
                    if not (end_time <= booked_start or current_time >= booked_end):
                        slot_available = False
                        break
                
                if slot_available:
                    available_slots.append({
                        'start_time': current_time.strftime("%H:%M"),
                        'end_time': end_time.strftime("%H:%M")
                    })
                
                current_time = (datetime.combine(datetime.today(), current_time) + 
                              timedelta(minutes=15)).time()
            
            return available_slots
        finally:
            db.close()

    def create_booking(self, client_id: int, service_id: int, master_id: int, 
                      date_str: str, start_time: str) -> bool:
        db = next(get_db())
        try:
            service = db.query(Service).filter(Service.id == service_id).first()
            if not service:
                return False
            
            booking_date = datetime.strptime(date_str, "%Y-%m-%d").date()
            
            end_time = (datetime.strptime(start_time, "%H:%M") + 
                       timedelta(minutes=service.duration)).strftime("%H:%M")
            
            available_slots = self.get_available_slots(master_id, date_str, service.duration)
            if not any(slot['start_time'] == start_time for slot in available_slots):
                return False
            
            booking = Booking(
                client_id=client_id,
                service_id=service_id,
                master_id=master_id,
                date=booking_date,
                start_time=start_time,
                end_time=end_time,
                status='confirmed'
            )
            
            db.add(booking)
            db.commit()
            return True
            
        except Exception as e:
            db.rollback()
            logging.error(f"Error creating booking: {e}")
            return False
        finally:
            db.close()

    def get_client_bookings(self, client_id: int) -> List[Dict]:
        db = next(get_db())
        try:
            bookings = db.query(Booking).filter(
                Booking.client_id == client_id,
                Booking.status == 'confirmed'
            ).all()
            
            return [
                {
                    'id': b.id,
                    'date': b.date,
                    'start_time': b.start_time,
                    'service': b.service.name,
                    'master': b.master.name
                }
                for b in bookings
            ]
        finally:
            db.close()

    def cancel_booking(self, booking_id: int) -> bool:
        db = next(get_db())
        try:
            booking = db.query(Booking).filter(Booking.id == booking_id).first()
            if not booking:
                return False
            
            booking.status = 'cancelled'
            db.commit()
            return True
            
        except Exception as e:
            db.rollback()
            logging.error(f"Error cancelling booking: {e}")
            return False
        finally:
            db.close()