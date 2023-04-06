import pytest
from rraft import Progress_Owner


@pytest.mark.benchmark(group="Progress")
def test_progress_creation(benchmark):
    def progress_creation():
        Progress_Owner(9, 10)
    benchmark(progress_creation)
