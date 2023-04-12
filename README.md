# rraft-py

This crate provides Python bindings for the [tikv/raft-rs](https://github.com/tikv/raft-rs) crate, allowing for integration of the [*Raft consensus algorithm*](https://en.wikipedia.org/wiki/Raft_(algorithm)) in Python applications.

The `raft-rs` crate implements the *Raft consensus algorithm*, which is a widely used and well-documented method for maintaining a replicated state machine in a distributed system.

Whether you're building a distributed database, a highly-available service, or any other type of application that requires consensus among a set of nodes, this binding makes it simple to get started.


> Note: This binding only includes the core consensus module of *raft-rs*. The log, state system, and transport components must be written and integrated  through your Python code.

## Why?

This library is an unofficial Python binding for the `tikv/raft-rs` using *pyo3*.

There have been several attempts to implement a *Raft implementation* in the Python ecosystem before, but unfortunately, there is no library being used as a *de-facto* standard as of now.

This binding was created to resolve this problem and to make it possible to integrate your Python code with *low-level Raft implementation*.

### Disclaimer

This binding bypasses the memory management differences between Python and Rust through the following API modeling, which is quite different from typical Python use cases.

General types have *ownership* of their respective types.

For example, instances created with the `Config` constructor are modeled to have ownership of the `Config` object in Rust.

Apart from this, there is a type named `Config_Ref`, which is modeled as a reference "Container Object" that only holds a reference to the `Config` type.

The most of APIs of `rraft-py` are modeled internally to handle both "General type" and "Container Object types".

However, a few APIs may require only types with ownership. This kind of type information is specified in the [rraft.pyi](https://github.com/lablup/rraft-py/blob/main/rraft.pyi). 

Note that passing a reference pointing an invalid instance in Python to an API causes a segmentation fault (named `destored_error`) which is hard to debugging. Understanding Rust's ownership concept can help you resolve these kinds of problems.

## Getting started

### Installation

#### With pip

```
$ pip install rraft-py
```

## Reference

- [tikv/raft-rs](https://docs.rs/raft/latest/raft) - This binding provides almost completely similar APIs with raft-rs, so it would be helpful to refer to its documentation.
- [huggingface/tokenizer](https://github.com/huggingface/tokenizers/tree/main/bindings/python) - This lib's Reference type implementation is greatly inspired from this binding.
