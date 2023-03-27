build:
	maturin build -b=pyo3
	pip install .

unit-test:
	pytest tests

lint:
	cargo clippy 

lint-fix:
	cargo clippy --fix --lib -p rraft-py