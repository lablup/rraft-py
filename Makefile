build:
	maturin build -b=pyo3
	pip install .

run-example-single-mem-node:
	python examples/single_mem_node/main.py

run-example-five-mem-node:
	python examples/five_mem_node/main.py

unit-test:
	pytest tests