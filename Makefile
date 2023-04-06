build:
	maturin build
	pip install .

test:
	python -m pytest

bench:
	python -m pytest benches/suites/*.py

fmt:
	cargo fmt

lint:
	cargo clippy 

lint-fix:
	cargo clippy --fix --lib -p rraft-py

lint-fix-py:
	python -m black **/*.py
