import pytest
import requests

from src import map_parser as mp

# --- Фикстуры ---


@pytest.fixture
def sample_html() -> str:
    return """
    <html><body>
      <div class="masstransit-brief-schedule-view">
        107 – ТК Центральный: 3 мин, 11 мин<br/>
        220 – Профилакторий Радугакаждые: 8мин
      </div>
    </body></html>
    """


@pytest.fixture
def empty_html() -> str:
    return "<html><body><p>Пустота</p></body></html>"


@pytest.fixture
def fetch(monkeypatch):
    def _patch(html: str = None, exception: Exception = None):
        if exception:
            monkeypatch.setattr(mp, "fetch_html", lambda url: (_ for _ in ()).throw(exception))
        else:
            monkeypatch.setattr(mp, "fetch_html", lambda url: html)

    return _patch


# --- Тесты parse_arrival_block ---


def test_parse_arrival_block_found(sample_html):
    """Проверяет, что из HTML с данными корректно извлекается текст, содержащий маршруты и остановки."""
    text = mp.parse_arrival_block(sample_html)
    assert "107" in text and "ТК Центральный" in text
    assert "220" in text and "Профилакторий Радуга" in text


def test_parse_arrival_block_empty(empty_html):
    """Проверяет, что из пустого HTML не извлекается ничего (возвращается пустая строка)."""
    assert mp.parse_arrival_block(empty_html) == ""


# --- Тесты extract_buses ---


def test_extract_buses():
    """Проверяет, что из неформатированной строки с маршрутами корректно извлекаются данные по автобусам."""
    raw = "107 – ТК Центральный: 3 мин, 11 мин220 – Профилакторий Радугакаждые: 8мин"
    expected = [
        {"bus_number": "107", "route_name": "ТК Центральный", "arrival_times": ["3 мин", "11 мин"]},
        {"bus_number": "220", "route_name": "Профилакторий Радуга", "arrival_times": ["8мин"]},
    ]
    result = mp.extract_buses(raw)
    assert result == expected


# --- Тесты format_buses ---


def test_format_buses_nonempty():
    """Проверяет форматирование списка автобусов в человекочитаемую строку."""
    buses = [
        {"bus_number": "1", "route_name": "A", "arrival_times": ["5 мин", "10 мин"]},
        {"bus_number": "2", "route_name": "B", "arrival_times": ["7 мин"]},
    ]
    out = mp.format_buses(buses).splitlines()
    assert out == ["1 – A: 5 мин, 10 мин", "2 – B: 7 мин"]


def test_format_buses_empty():
    """Проверяет, что при отсутствии данных возвращается сообщение о недоступности информации."""
    assert mp.format_buses([]) == "Информация по остановке временно недоступна."


# --- Тесты get_buses_info ---


def test_get_buses_info_all_buses(sample_html, fetch):
    """Проверяет, что информация выводится по всем маршрутам, если не указан конкретный номер автобуса."""
    fetch(html=sample_html)
    res = mp.get_buses_info("url", bus_number=None, max_retries=1)
    assert "107 – ТК Центральный" in res
    assert "220 – Профилакторий Радуга" in res


def test_get_buses_info_specific_route(sample_html, fetch):
    """Проверяет, что при указании номера маршрута возвращается информация только по нему."""
    fetch(html=sample_html)
    res = mp.get_buses_info("url", bus_number="107", max_retries=1)
    assert res.startswith("107 – ТК Центральный")


def test_get_buses_info_not_found(sample_html, fetch):
    """Проверяет, что возвращается корректное сообщение, если указанный маршрут не найден."""
    fetch(html=sample_html)
    res = mp.get_buses_info("url", bus_number="999", max_retries=1)
    assert res == "Информация по маршруту 999 не найдена."


def test_get_buses_info_exception(fetch):
    """Проверяет, что при возникновении исключения в запросе возвращается сообщение об ошибке."""
    fetch(exception=requests.RequestException("network error"))
    res = mp.get_buses_info("url", None, max_retries=1)
    assert res.startswith("Ошибка при получении данных:")


def test_get_buses_info_retry_exhaust(empty_html, fetch):
    """Проверяет поведение при повторных неудачных попытках получения данных."""
    fetch(html=empty_html)
    res = mp.get_buses_info("url", None, max_retries=2)
    assert res == "Не удалось получить информацию после нескольких попыток."
