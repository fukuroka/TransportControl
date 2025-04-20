import re

import requests
from bs4 import BeautifulSoup


def fetch_html(url: str) -> str:
    response = requests.get(url)
    response.raise_for_status()
    return response.text


def parse_arrival_block(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    block = soup.find("div", class_="masstransit-brief-schedule-view")
    return block.get_text(strip=True) if block else ""


def extract_buses(text: str) -> list[dict]:
    """
    Универсальный парсер всех записей вида:
      107 – ТК Центральный: 3 мин, 11 мин
      220 – Профилакторий Радугакаждые: 8 мин
    и т.п.
    """
    pattern = (
        r"(\d+)\s*(?:–|to|до)\s*([^\d:]+?)(?=каждые|:|\d+\s*мин|завтра)"
        r"(.*?)(?=\d{1,3}\s*(?:–|to|до)|$)"
    )
    results = []
    for m in re.finditer(pattern, text):
        num = m.group(1)
        name = m.group(2).replace("каждые", "").strip("–: ")
        times = re.findall(r"\d+\s*мин", m.group(3))
        results.append({"bus_number": num, "route_name": name, "arrival_times": times})
    return results


def format_buses(buses: list[dict]) -> str:
    lines = []
    for b in buses:
        times = ", ".join(b["arrival_times"])
        lines.append(f"{b['bus_number']} – {b['route_name']}: {times}")
    return "\n".join(lines) or "Информация по остановке временно недоступна."


def get_buses_info(url: str, bus_number: str | None = None, max_retries: int = 10) -> str:
    """
    Если bus_number задан — ищем только его и возвращаем одну строку.
    Иначе — возвращаем все найденные рейсы.
    """
    for _ in range(max_retries):
        try:
            html = fetch_html(url)
        except requests.RequestException as e:
            return f"Ошибка при получении данных: {e}"
        text = parse_arrival_block(html)
        if not text:
            continue

        buses = extract_buses(text)
        if bus_number:
            for b in buses:
                if b["bus_number"] == bus_number:
                    return format_buses([b])
            return f"Информация по маршруту {bus_number} не найдена."
        else:
            return format_buses(buses)
    return "Не удалось получить информацию после нескольких попыток."
