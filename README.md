# rraft-py

This library provides Python bindings of the *[tikv/raft-rs](https://github.com/tikv/raft-rs)* crate, allowing for integration of the [*Raft consensus algorithm*](https://en.wikipedia.org/wiki/Raft_(algorithm)) in Python applications.

Whether you're building a distributed database, a highly-available service, or any other type of application that requires consensus among a set of nodes, this binding makes it simple to get started.

## ✨ Hightlights

* Provides almost the same APIs with `tikv/raft-rs` to Python, even along with concrete type hints and comments for all types.

* Provides reliable implementation with more than 10,000 lines of test code porting.

* Provides flexible design inherited from `tikv/raft-rs`, which means `rraft-py` lets users could combine any storage and network layer they want through Python.

## 🤔 Why?

There have been several attempts to implement a *Raft implementation* in the Python ecosystem before, but unfortunately, there is no library being used as a *de-facto* standard as of now.

This binding was created to resolve this problem and to make it possible to integrate your Python code with *low-level Raft implementation*.

### When to use and when not to use

This library is a binding for *tikv/raft-rs* and only contains an implementation of the consensus module. Therefore, you need to write the logic for both the transport and storage layers yourself. If you just want to quickly integrate Raft with your Python application, using this library might not be suitable. In this case, you can consider to using [*Raftify*](https://github.com/lablup/raftify) or [*PySyncObj*](https://github.com/bakwc/PySyncObj).

However, if you want to integrate *well-tested* Raft implementation that is reliable for production-level use in Python, or want to change the transport layer to a different layer, or want to change *fine-grained* settings according to your application's specific use case, this binding could provide you a valid starting point.

### Disclaimer

#### Memory management

The library provides a different API compared to other Python libraries to bypass the memory management differences between Python and Rust.

Refer to the [*How it works*](https://github.com/lablup/rraft-py/wiki/How-it-works) page in the Wiki for more details.

## 🚀 Getting started

### Installation

#### With pip

```
$ pip install rraft-py
```

#### Example

- [Example using coroutine with single in-memory node](https://github.com/lablup/rraft-py/blob/main/example/single_mem_node/use_coroutine.py)

- [Example using coroutine with multi in-memory nodes](https://github.com/lablup/rraft-py/blob/main/example/multi_mem_node/main.py)

## References

- [tikv/raft-rs](https://docs.rs/raft/latest/raft) - This binding provides almost completely similar APIs with raft-rs, so it would be helpful to refer to its documentation.
- [huggingface/tokenizer](https://github.com/huggingface/tokenizers/tree/main/bindings/python) - This lib's RefMutContainer implementation is greatly inspired from this binding.
