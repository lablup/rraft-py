# rraft-py

🚧 This repository is WIP and not yet *production-ready*. I'd recommend not use this lib unless you're not interested in contributing to this bindings. The API will change.

---

This crate provides Python bindings for the *[tikv/raft-rs](https://github.com/tikv/raft-rs)* crate, allowing for integration of the [*Raft consensus algorithm*](https://en.wikipedia.org/wiki/Raft_(algorithm)) in Python applications.

The `raft-rs` crate implements the *Raft consensus algorithm*, which is a widely used and well-documented method for maintaining a replicated state machine in a distributed system.

Whether you're building a distributed database, a highly-available service, or any other type of application that requires consensus among a set of nodes, this binding makes it simple to get started.

> Note: This binding only includes the core consensus module of *raft-rs*. The log, state system, and transport components must be written and integrated  through your Python code.

## Why?

This library is an unofficial Python binding for the `tikv/raft-rs` using *[pyo3](https://github.com/PyO3/pyo3)*.

There have been several attempts to implement a *Raft implementation* in the Python ecosystem before, but unfortunately, there is no library being used as a *de-facto* standard as of now.

This binding was created to resolve this problem and to make it possible to integrate your Python code with *low-level Raft implementation*.

### When to use and when not to use

This library is a binding for `tikv/raft-rs` and only contains an implementation of the consensus module. Therefore, you need to write the logic for both the transport and storage layers yourself. If you just want to quickly integrate Raft with your Python application, using this library might not be suitable. I'd personally recommend considering using [PySyncObj](https://github.com/bakwc/PySyncObj).

However, if you want to integrate *well-tested* Raft implementation that is reliable for production-level use in Python, or want to change the transport layer to a different layer, or want to change *fine-grained* settings according to your application's specific use case, this binding could provide you a valid starting point.

### Disclaimer

#### Memory management

This library works differently from other *Python* libraries to handle differences in memory management.

In this library, General types have [*ownership*](https://doc.rust-lang.org/book/ch04-01-what-is-ownership.html) of their respective types. For example, instances created with the `Config` constructor have *ownership* of the `Config` object in *Rust*.

In addition, there is a separate type named `Config_Ref`, which acts as a "Container Object" that holds a reference to the `Config` type.

Most of the APIs in `rraft-py` handle both "General types" and "Container Object types," but some APIs require only types with ownership. You can find information about this in [rraft.pyi](https://github.com/lablup/rraft-py/blob/main/rraft.pyi).

It is important to note that passing a reference pointing an invalid object in Python to `rraft-py`'s API can cause a **Segmentation fault** that is difficult to debug. Understanding Rust's ownership concept can help you avoid such problems.

#### Comments

All the comments of the codes have been copy-pasted from the upstream repository (`raft-rs`) and there might be some missing comments.

### Benchmarks

TBU

## Getting started

<!-- ### Installation

#### With pip

```
$ pip install rraft-py
``` -->

#### Example

- [Example using coroutine with single in-memory node](https://github.com/lablup/rraft-py/blob/main/example/single_mem_node/use_coroutine.py)

- [Example using coroutine with multi in-memory nodes](https://github.com/lablup/rraft-py/blob/main/example/multi_mem_node/main.py)

## Contribution

Are you interested in this project? The project is in need of various improvements such as code reviews, adding benchmarks, and adding missing methods. All kinds of contributions will be highly appreciated.

### To do

Currently there are following issues.

- [ ] Fill in missing methods and bindings.
- [ ] Fill in missing [benchmark code](https://github.com/lablup/rraft-py/blob/main/benches/suites/raw_node.py).
- [ ] Add more understandable example codes.
- [ ] Look for [Github issues](https://github.com/lablup/rraft-py/issues?q=is%3Aopen).

## Reference

- [tikv/raft-rs](https://docs.rs/raft/latest/raft) - This binding provides almost completely similar APIs with raft-rs, so it would be helpful to refer to its documentation.
- [huggingface/tokenizer](https://github.com/huggingface/tokenizers/tree/main/bindings/python) - This lib's Reference type implementation is greatly inspired from this binding.
