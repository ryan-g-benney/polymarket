import pytest
from gamma import GammaAPI
from clob import ClobAPI
from data import DataAPI


@pytest.fixture(scope="module", autouse=True)
async def close_clients():
    yield
    for cls in (GammaAPI, ClobAPI, DataAPI):
        await cls.aclose()
