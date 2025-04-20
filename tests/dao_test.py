import pytest
import pytest_asyncio

from src.bus_stop_dao import BusStopDAO


@pytest_asyncio.fixture
async def dao():
    dao_instance = BusStopDAO(":memory:")
    await dao_instance.connect()
    async with dao_instance.conn.cursor() as cur:
        await cur.execute("""
            CREATE TABLE stops (
                stop_name TEXT NOT NULL,
                stop_url TEXT NOT NULL
            )
        """)
        await cur.executemany(
            "INSERT INTO stops (stop_name, stop_url) VALUES (?, ?)",
            [
                ("ТК Центральный", "http://example.com/central"),
                ("Парк Победы", "http://example.com/park"),
            ],
        )
        await dao_instance.conn.commit()
    return dao_instance


@pytest.mark.asyncio
async def test_connect(dao):
    assert dao.conn is not None
    stops = await dao.get_all_stops()
    assert len(stops) == 2
    assert "ТК Центральный" in stops


@pytest.mark.asyncio
async def test_close(dao):
    await dao.close()
    with pytest.raises(ValueError, match="no active connection"):
        await dao.get_all_stops()


@pytest.mark.asyncio
async def test_get_all_stops(dao):
    stops = await dao.get_all_stops()
    assert sorted(stops) == ["Парк Победы", "ТК Центральный"]


@pytest.mark.asyncio
async def test_get_stop_link(dao):
    assert await dao.get_stop_link("ТК Центральный") == "http://example.com/central"
    assert await dao.get_stop_link("Неизвестная") is None
