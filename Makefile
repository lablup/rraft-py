build:
	maturin build -b=pyo3
	pip install .

unit-test:
	pytest tests