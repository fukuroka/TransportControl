import re
import time

import requests
from bs4 import BeautifulSoup

# --- Модуль для работы с данными с Яндекс.Карт ---


def fetch_html(url: str) -> str:
    """
    Получает HTML-страницу по указанному URL.
    Если происходит ошибка, возбуждается исключение.
    """
    response = requests.get(url)
    response.raise_for_status()  # если статус не 200, будет выброшено исключение
    return response.text


def parse_arrival_block(html: str) -> str | None:
    """
    Извлекает блок с информацией о прибытии транспорта.
    Предполагается, что нужный блок находится в div с классом
    'masstransit-brief-schedule-view'.
    """
    soup = BeautifulSoup(html, "html.parser")
    arrival_block = soup.find("div", class_="masstransit-brief-schedule-view")
    if arrival_block:
        return arrival_block.get_text(strip=True)
    return None


def extract_bus_info(text: str, bus_number: str) -> dict | None:
    """
    Извлекает информацию о маршруте и времени прибытия для указанного автобуса.
    Ищет шаблон вида "<номер маршрута>до <название маршрута> <время прибытия>".

    Возвращает словарь:
       {
         "bus_number": номер маршрута,
         "route_name": название маршрута,
         "arrival_times": список времен прибытия
       }
    или None, если данные не найдены.
    """
    # Шаблон, который ищет последовательность: [номер маршрута]до, затем название и времена
    pattern = rf"{bus_number}\s*([^0-9]+?)((?:\s*\d+\s*мин)+)"
    match = re.search(pattern, text)
    if not match:
        return None

    route_name = match.group(1).strip()
    arrival_times_raw = match.group(2)
    arrival_times = re.findall(r"\d+\s*мин", arrival_times_raw)

    return {"bus_number": bus_number, "route_name": route_name, "arrival_times": arrival_times}


def get_bus_arrival_info(
    bus_number: str, url: str, max_retries: int = 20, delay: float = 1.0
) -> str:
    """
    Получает информацию о прибытии автобуса с указанным номером.
    Повторяет попытки до тех пор, пока не получит данные или не достигнет лимита попыток.

    :param bus_number: Номер маршрута автобуса
    :param url: URL остановки
    :param max_retries: Максимум попыток (по умолчанию 10)
    :param delay: Задержка между попытками (в секундах)
    :return: Строка с информацией или сообщение об ошибке
    """
    for attempt in range(1, max_retries + 1):
        try:
            html_content = fetch_html(url)
        except requests.RequestException as e:
            return f"Ошибка при получении данных: {e}"

        arrival_text = parse_arrival_block(html_content)
        if not arrival_text:
            print(f"[Попытка {attempt}] Нет блока прибытия, жду {delay} секунд...")
            time.sleep(delay)
            continue

        bus_info = extract_bus_info(arrival_text, bus_number)
        if bus_info:
            arrival_times = ", ".join(bus_info["arrival_times"])
            return f"Маршрут: {bus_info['bus_number']}\nВремя прибытия: {arrival_times}"
        else:
            print(f"[Попытка {attempt}] Нет данных по маршруту {bus_number}, жду {delay} секунд...")
            time.sleep(delay)

    return f"Не удалось получить информацию по маршруту {bus_number} после {max_retries} попыток."
