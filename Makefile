build:
	maturin build -b=pyo3
	pip install .

unit-test:
	pytest tests

fmt:
	cargo fmt

lint:
	cargo clippy 

lint-fix:
	cargo clippy --fix --lib -p rraft-py