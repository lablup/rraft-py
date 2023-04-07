import pytest
from rraft import Progress


@pytest.mark.benchmark(group="Progress", warmup=True)
def test_progress_creation(benchmark):
    def progress_creation():
        Progress(9, 10)
    benchmark(progress_creation)
