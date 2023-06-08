build:
	maturin build

install:
	maturin build
	pip install .

install-release:
	maturin build --release --strip
	pip install .

clean:
	cargo clean

test:
	python -m pytest

bench:
	python -m pytest benches/suites/*.py

fmt:
	cargo fmt

lint:
	cargo clippy 

lint-fix:
	cargo clippy --fix --lib -p bindings
	cargo clippy --fix --lib -p external_bindings
	cargo clippy --fix --lib -p mem_storage_bindings
	cargo clippy --fix --lib -p py_storage_bindings
	cargo clippy --fix --lib -p raftpb_bindings
	cargo clippy --fix --lib -p utils

lint-fix-py:
	python -m black **/*.py
