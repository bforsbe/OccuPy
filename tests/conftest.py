"""This file allows you to define testing 'fixtures',
things which are available for multiple tests if requests.

https://docs.pytest.org/en/6.2.x/fixture.html
"""
import pytest


@pytest.fixture
def something_to_resuse() -> int:
    return 1
