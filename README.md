# rraft-py

This crate provides a Python binding for the [raft-rs](https://github.com/tikv/raft-rs) crate, allowing for easy integration of the Raft consensus algorithm in Python applications.

The `raft-rs` crate implements the Raft consensus algorithm, which is a widely used and well-documented method for maintaining a replicated state machine in a distributed system.

Whether you're building a distributed database, a highly-available service, or any other type of application that requires consensus among a set of nodes, this binding makes it simple to get started.

## Installation

### With pip

```
$ pip install rraft-py
```

## How to build

You can build this project using [maturin](https://github.com/PyO3/maturin).

```
$ maturin build -b=pyo3
```