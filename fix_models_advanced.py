#!/usr/bin/env python3
"""
Улучшенный скрипт для автоматического добавления extend_existing=True во все модели SQLAlchemy.
"""

import os
import re
from pathlib import Path


def fix_model_file(file_path):
    """Добавляет extend_existing=True в модель, если его нет."""
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Проверяем, есть ли уже extend_existing=True
    if "extend_existing" in content:
        print(f"ℹ️  Файл уже содержит extend_existing: {file_path}")
        return False

    # Ищем класс, который наследуется от Base
    class_match = re.search(r"class\s+(\w+)\(Base\):", content)
    if not class_match:
        print(f"⚠️  Не найден класс Base в файле: {file_path}")
        return False

    class_name = class_match.group(1)

    # Случай 1: Есть __table_args__ с tuple
    table_args_tuple_match = re.search(
        r"(\s+)__table_args__\s*=\s*\(\s*\n(.*?\n\s*)\)", content, re.DOTALL
    )
    if table_args_tuple_match:
        indent = table_args_tuple_match.group(1)
        # Добавляем extend_existing в конец tuple
        new_content = content.replace(
            table_args_tuple_match.group(0),
            f'{table_args_tuple_match.group(0)[:-1]}        {{"extend_existing": True}},\n{indent})',
        )
        print(f"✅ Добавил extend_existing в tuple __table_args__: {file_path}")

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(new_content)
        return True

    # Случай 2: Есть __table_args__ с dict
    table_args_dict_match = re.search(r"(\s+)__table_args__\s*=\s*\{([^}]*)\}", content)
    if table_args_dict_match:
        indent = table_args_dict_match.group(1)
        dict_content = table_args_dict_match.group(2)

        # Если dict пустой
        if not dict_content.strip():
            new_dict_content = '"extend_existing": True'
        else:
            new_dict_content = f'{dict_content}, "extend_existing": True'

        new_content = content.replace(
            table_args_dict_match.group(0),
            f"{indent}__table_args__ = {{{new_dict_content}}}",
        )
        print(f"✅ Добавил extend_existing в dict __table_args__: {file_path}")

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(new_content)
        return True

    # Случай 3: Нет __table_args__ - добавляем после __tablename__
    tablename_match = re.search(r'(\s+)__tablename__\s*=\s*["\'][^"\']*["\']', content)
    if tablename_match:
        indent = tablename_match.group(1)
        new_content = content.replace(
            tablename_match.group(0),
            f'{tablename_match.group(0)}\n{indent}__table_args__ = {{"extend_existing": True}}',
        )
        print(f"✅ Добавил __table_args__ с extend_existing: {file_path}")

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(new_content)
        return True

    print(f"⚠️  Не удалось обработать файл: {file_path}")
    return False


def main():
    """Основная функция."""
    models_dir = Path("src/models")

    if not models_dir.exists():
        print(f"❌ Директория {models_dir} не найдена")
        return

    fixed_files = 0
    total_files = 0

    for file_path in models_dir.glob("*.py"):
        if file_path.name in ["__init__.py", "__pycache__"]:
            continue

        total_files += 1
        print(f"🔄 Обрабатываю файл: {file_path}")

        if fix_model_file(file_path):
            fixed_files += 1

    print(f"\n📊 Результат:")
    print(f"   Обработано файлов: {total_files}")
    print(f"   Исправлено файлов: {fixed_files}")
    print(f"   Пропущено файлов: {total_files - fixed_files}")


if __name__ == "__main__":
    main()
