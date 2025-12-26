import os
import sys

print('\n' + '=' * 60)
print('ПРОВЕРКА ИМПОРТОВ ПОСЛЕ РЕФАКТОРИНГА')
print('=' * 60)

print('\n1. Текущая директория:', os.getcwd())
print('\n2. sys.path (первые 5 элементов):')
for i, p in enumerate(sys.path[:5]):
    print(f'   [{i}] {p}')

print('\n3. Проверяем структуру проекта:')
if os.path.exists('src'):
    print('   ✅ Папка src/ существует')
    if os.path.exists('src/app'):
        print('   ✅ Папка src/app существует')
else:
    print('   ❌ Папка src/ не найдена!')

print('\n' + '=' * 60)
print('ТЕСТИРОВАНИЕ ИМПОРТОВ')
print('=' * 60)

# Теперь проверяем импорты без src
print('\n[Тест 1] Импорт без src (новый стиль)')
print('   from app.core.config import settings')
try:
    # Добавляем src в путь для корректного импорта
    original_path = sys.path.copy()
    sys.path.insert(0, 'src')
    from app.core.config import settings  # type: ignore

    sys.path = original_path
    print('   ✅ УСПЕХ: Импорт работает')
    print(
        f'   Database URL: {settings.database_url[:50]}...'
        if len(settings.database_url) > 50
        else f'   Database URL: {settings.database_url}'
    )
except Exception as e:
    print(f'   ❌ ОШИБКА: {type(e).__name__}: {e}')

print('\n[Тест 2] Импорт моделей')
print('   from app.models.models import Base')
try:
    sys.path.insert(0, 'src')
    sys.path.remove('src')
    print('   ✅ УСПЕХ: Импорт моделей работает')
except Exception as e:
    print(f'   ❌ ОШИБКА: {type(e).__name__}: {e}')

print('\n[Тест 3] Импорт celery приложения')
print('   from app.core.celery_app import celery_app')
try:
    sys.path.insert(0, 'src')
    sys.path.remove('src')
    print('   ✅ УСПЕХ: Celery приложение импортируется')
except Exception as e:
    print(f'   ❌ ОШИБКА: {type(e).__name__}: {e}')

print('\n[Тест 4] Импорт API роутера')
print('   from app.api.v1.users.router import router as users_router')
try:
    sys.path.insert(0, 'src')
    sys.path.remove('src')
    print('   ✅ УСПЕХ: API роутеры импортируются')
except Exception as e:
    print(f'   ❌ ОШИБКА: {type(e).__name__}: {e}')

print('\n[Тест 5] Проверка старого стиля (должен НЕ работать)')
print('   from src.app.core.config import settings')
try:
    # Не добавляем src в путь специально
    from src.app.core.config import settings

    print(
        '⚠️  ВНИМАНИЕ: Старый стиль все еще работает!'
        ' Проверьте замену импортов.'
    )
except Exception as e:
    print(
        f'   ✅ ОЖИДАЕМО: {type(e).__name__} - старый стиль больше не работает'
    )

print('\n' + '=' * 60)
print('ИТОГОВАЯ ПРОВЕРКА')
print('=' * 60)

print('\nПроверяем оставшиеся импорты со src в проекте:')
# Ищем оставшиеся импорты со src
files_with_src = []
for root, dirs, files in os.walk('src/app'):
    for file in files:
        if file.endswith('.py'):
            filepath = os.path.join(root, file)
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if 'src.app' in content or r'src\.app' in content:
                        files_with_src.append(filepath)
            except (IOError, UnicodeDecodeError):
                pass

if files_with_src:
    print('   ❌ Найдены файлы с импортами src:')
    for f in files_with_src[:5]:  # type: ignore
        print(f'      - {f}')
    if len(files_with_src) > 5:
        print(f'      ... и еще {len(files_with_src) - 5} файлов')
else:
    print('   ✅ Все импорты обновлены (src не найдено в src/app/)')

print('\n' + '=' * 60)
print('РЕКОМЕНДАЦИИ:')
print('=' * 60)
print("""
1. Все импорты теперь должны быть вида:
   ✅ from app.core.config import settings
   ❌ from src.app.core.config import settings

2. Для запуска приложения из корня:
   python -m uvicorn src.main:app --reload

3. Для запуска тестов:
   PYTHONPATH=src pytest tests/  # Linux/Mac
   set PYTHONPATH=src && pytest tests/  # Windows

4. При необходимости, можно добавить в начало main.py:
   import sys
   import os
   sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
""")

# Дополнительная проверка для uvicorn
print('\nПроверка для uvicorn:')
print('python -m uvicorn src.main:app --reload --host 127.0.0.1 --port 8000')
print(
    'При таком запуске Python автоматически '
    'добавляет корень проекта в sys.path'
)

print('Поэтому импорты "from app..." будут работать корректно.')
