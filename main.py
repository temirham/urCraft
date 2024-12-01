from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from pydantic import BaseModel
from datetime import datetime
from fastapi.middleware.cors import CORSMiddleware

# Инициализация приложения
app = FastAPI()

# Настройка CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Разрешить все источники. Для безопасности укажите конкретные.
    allow_credentials=True,
    allow_methods=["*"],  # Разрешить все методы (POST, GET, OPTIONS и т.д.)
    allow_headers=["*"],  # Разрешить любые заголовки
)

# Настройка базы данных
DATABASE_URL = "sqlite:///./contacts.db"  # SQLite для простоты
Base = declarative_base()
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})  # SQLite требует этой опции
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Модель базы данных
class Contact(Base):
    __tablename__ = "contacts"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    phone = Column(String, nullable=False)
    topic = Column(String, nullable=False)  # Новое поле для темы обращения
    created_at = Column(DateTime, default=datetime.utcnow)

# Создание таблицы
Base.metadata.create_all(bind=engine)

# Pydantic-модель для валидации входящих данных
class ContactCreate(BaseModel):
    name: str
    phone: str
    topic: str  # Новое поле для валидации темы обращения

    class Config:
        schema_extra = {
            "example": {
                "name": "Иван Иванов",
                "phone": "+7 (999) 999-99-99",
                "topic": "Мошенничество"
            }
        }

# Dependency для работы с сессией базы данных
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# API для добавления контактов
@app.post("/api/contact")
def create_contact(contact: ContactCreate, db: Session = Depends(get_db)):
    # Создание записи в базе данных
    new_contact = Contact(name=contact.name, phone=contact.phone, topic=contact.topic)
    db.add(new_contact)
    db.commit()
    db.refresh(new_contact)
    return {"message": "Contact saved successfully", "id": new_contact.id}

# API для получения всех контактов (опционально)
@app.get("/api/contacts")
def get_contacts(db: Session = Depends(get_db)):
    contacts = db.query(Contact).all()
    return contacts

# Запуск приложения
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=7000)
