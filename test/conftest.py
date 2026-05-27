from pathlib import Path
import pytest

def pytest_addoption(parser):
    parser.addoption(
        "--run-manual", action="store_true", default=False, help="run manual tests"
    )

def pytest_configure(config):
    config.addinivalue_line("markers", "manual: mark test as manual to skip by default")

def pytest_collection_modifyitems(config, items):
    if config.getoption("--run-manual"):
        # --run-manual given in cli: do not skip manual tests
        return
    skip_manual = pytest.mark.skip(reason="need --run-manual option to run")
    for item in items:
        if "manual" in item.keywords:
            item.add_marker(skip_manual)

@pytest.fixture
def test_data_path():
    return Path(__file__).parent / "test_data"