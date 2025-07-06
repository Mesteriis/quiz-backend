#!/usr/bin/env python
"""
Скрипт для запуска всех e2e тестов API Quiz App.

Пример использования:
    python run_all_tests.py
    python run_all_tests.py --url http://localhost:8000
"""

import os
import sys
import argparse
import subprocess
import time
from datetime import datetime


def parse_args():
    """Парсинг аргументов командной строки."""
    parser = argparse.ArgumentParser(description="Запуск e2e тестов API")
    parser.add_argument(
        "--url", default="http://localhost:8000", 
        help="URL API сервера (по умолчанию: http://localhost:8000)"
    )
    parser.add_argument(
        "--token", default=None,
        help="Токен API для авторизованных запросов"
    )
    parser.add_argument(
        "--admin-token", default=None,
        help="Админский токен API для авторизованных запросов"
    )
    parser.add_argument(
        "--telegram-token", default=None,
        help="Токен Telegram бота для тестов Telegram API"
    )
    parser.add_argument(
        "--only", default=None, choices=["api", "admin", "telegram"],
        help="Запуск только указанного набора тестов"
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true",
        help="Подробный вывод"
    )
    parser.add_argument(
        "--report", action="store_true",
        help="Создать HTML-отчет о тестировании"
    )
    return parser.parse_args()


def setup_environment(args):
    """Настройка переменных окружения для тестов."""
    os.environ["API_URL"] = args.url

    if args.token:
        os.environ["API_TOKEN"] = args.token

    if args.admin_token:
        os.environ["ADMIN_API_TOKEN"] = args.admin_token

    if args.telegram_token:
        os.environ["TEST_TELEGRAM_TOKEN"] = args.telegram_token


def run_test_module(module_name, verbose=False, report=False):
    """Запуск указанного тестового модуля."""
    print(f"\n{'='*50}")
    print(f"Запуск тестов: {module_name}")
    print(f"{'='*50}")

    cmd = ["pytest", f"test_{module_name}_e2e.py", "--asyncio-mode=auto"]

    if verbose:
        cmd.append("-v")

    if report:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_path = f"report_{module_name}_{timestamp}.html"
        cmd.extend(["--html", report_path, "--self-contained-html"])

    try:
        subprocess.run(cmd, check=True)
        return True
    except subprocess.CalledProcessError:
        print(f"ОШИБКА: Тесты модуля {module_name} не прошли")
        return False


def main():
    """Основная функция запуска тестов."""
    args = parse_args()
    setup_environment(args)

    # Перейти в директорию с тестами
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    start_time = time.time()
    success = True

    # Определить, какие тесты запускать
    if args.only == "api":
        test_modules = ["api"]
    elif args.only == "admin":
        test_modules = ["admin_api"]
    elif args.only == "telegram":
        test_modules = ["telegram_api"]
    else:
        test_modules = ["api", "admin_api", "telegram_api"]

    # Запуск каждого модуля тестов
    for module in test_modules:
        result = run_test_module(module, args.verbose, args.report)
        success = success and result

    # Вывод общего результата
    end_time = time.time()
    duration = end_time - start_time

    print("\n" + "="*50)
    print(f"Общий результат тестирования: {'УСПЕХ' if success else 'ОШИБКИ'}")
    print(f"Время выполнения: {duration:.2f} секунд")
    print("="*50)

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
