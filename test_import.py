import sys
import os

print("=" * 60)
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
    from app.models.models import User
    print("   ✅ УСПЕХ")
except Exception as e:
    print(f"   ❌ ОШИБКА: {type(e).__name__}: {e}")

# Тест 2
print("\n[Тест 2] from src.app.models.models import User")
try:
    # Сначала убираем sys.path изменения
    sys.path.pop(0)
    from src.app.models.models import User as User2
    print("   ✅ УСПЕХ")
except Exception as e:
    print(f"   ❌ ОШИБКА: {type(e).__name__}: {e}")

print("\n" + "=" * 60)
print("ВЫВОД")
print("=" * 60)
print("""
Когда программа запускается как:
  python -m uvicorn src.main:app
  
Интерпретатор Python добавляет текущую директорию в sys.path,
а затем загружает модуль src/main.py

В этом случае:
  - ✅ from app... работает (потому что src/ добавлен в PYTHONPATH)
  - ❌ from src.app... НЕ работает (нет модуля src в sys.path)
""")
