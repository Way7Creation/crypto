#!/bin/bash
echo "������️ Удаление дублирующих файлов..."

# Бэкап перед удалением
mkdir -p backups/cleanup_$(date +%Y%m%d_%H%M%S)
cp -r src/core/*.py backups/cleanup_$(date +%Y%m%d_%H%M%S)/ 2>/dev/null

# Удаляем старые менеджеры
rm -f src/core/bot_manager.py
rm -f src/core/process_bot_manager.py
rm -f src/core/unified_bot_manager.py
rm -f src/core/state_manager.py

# Удаляем старые точки входа
rm -f main_simple.py
rm -f main_advanced.py
rm -f main_bot.py

# Удаляем дублирующие файлы проверки
rm -f test_*.py
rm -f check_*.py
rm -f init_db.py

# Удаляем старые скрипты
rm -f start_bot.sh
rm -f stop_bot.sh
rm -f restart_bot.sh
rm -f stop_all.sh

# Удаляем старый app.py из корня
rm -f app.py

echo "✅ Очистка завершена"
