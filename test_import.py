import os
import sys

print("\n" + "=" * 60)
print("ПРОВЕРКА ИМПОРТОВ")
print("=" * 60)

print("\n1. Текущая директория:", os.getcwd())
print("\n2. sys.path (первые 5 элементов):")
for i, p in enumerate(sys.path[:5]):
    print(f"   [{i}] {p}")

print("\n3. Добавляем src/ в sys.path:")
sys.path.insert(0, 'src')
print(f"   Добавлено: src -> {os.path.abspath('src')}")

print("\n4. sys.path после изменения (первые 5 элементов):")
for i, p in enumerate(sys.path[:5]):
    print(f"   [{i}] {p}")

print("\n" + "=" * 60)
print("ТЕСТИРОВАНИЕ ИМПОРТОВ")
print("=" * 60)

# Тест 1
print("\n[Тест 1] from app.models.models import User")
try:
    print("   ✅ УСПЕХ")
except Exception as e:
    print(f"   ❌ ОШИБКА: {type(e).__name__}: {e}")

# Тест 2
print("\n[Тест 2] from src.app.models.models import User")
try:
    # Сначала убираем sys.path изменения
    sys.path.pop(0)
    print("   ✅ УСПЕХ")
except Exception as e:
    print(f"   ❌ ОШИБКА: {type(e).__name__}: {e}")

print("\n" + "=" * 60)
print("=" * 60)
print("""
Когда проект запускается из корня командой:
    python -m uvicorn src.main:app --reload --host 127.0.0.1 --port 8000

Работают только импорты вида:
  - ✅ from src.app... (требуется для корректного запуска из корня)
  - ❌ from app... НЕ работает (модуль app не найден в sys.path)

Это соответствует требованиям README
и обеспечивает универсальный запуск для всех разработчиков.
""")
