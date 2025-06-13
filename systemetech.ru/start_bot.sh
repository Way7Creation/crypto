#!/bin/bash
# Скрипт запуска торгового бота

# Переход в директорию проекта
cd /var/www/www-root/data/www/systemetech.ru

# Активация виртуального окружения
source venv/bin/activate

# Создание директории для логов если не существует
mkdir -p logs

# Экспорт переменных окружения
export PYTHONPATH=/var/www/www-root/data/www/systemetech.ru:$PYTHONPATH

# Запуск веб-интерфейса в фоне
echo "🌐 Запуск веб-интерфейса..."
nohup python app.py > logs/web.log 2>&1 &
echo "✅ Веб-интерфейс запущен на порту 8000"

# Пауза для запуска веб-сервера
sleep 3

# Запуск основного бота
echo "🤖 Запуск торгового бота..."
python main.py