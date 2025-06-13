# init_db.py - запустите этот файл один раз для создания таблиц
from src.core.database import engine
from src.core.models import Base

print("Создание таблиц...")
Base.metadata.create_all(bind=engine)
print("Таблицы созданы успешно!")