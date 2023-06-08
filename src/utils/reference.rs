// Ref:: https://github.com/huggingface/tokenizers/tree/main/bindings/python
use pyo3::prelude::*;
use pyo3::PyErr;
use std::sync::{Arc, Mutex};

use crate::errors::runtime_error;
use crate::errors::DESTROYED_ERR_MSG;

#[derive(Clone)]
pub struct RefMutContainer<T> {
    inner: Arc<Mutex<Option<*mut T>>>,
}

impl<T> RefMutContainer<T> {
    pub fn new(content: &mut T) -> Self {
        Self {
            inner: Arc::new(Mutex::new(Some(content))),
        }
    }

    pub fn map<F: FnOnce(&T) -> U, U>(&self, f: F) -> Option<U> {
        let lock = self.inner.lock().unwrap();
        let ptr = lock.as_ref()?;
        Some(f(unsafe { ptr.as_ref().unwrap() }))
    }

    pub fn map_mut<F: FnOnce(&mut T) -> U, U>(&mut self, f: F) -> Option<U> {
        let lock = self.inner.lock().unwrap();
        let ptr = lock.as_ref()?;
        Some(f(unsafe { ptr.as_mut().unwrap() }))
    }
}

impl<T> Drop for RefMutContainer<T> {
    fn drop(&mut self) {
        self.inner.lock().unwrap().take();
    }
}

unsafe impl<T: Send> Send for RefMutContainer<T> {}
unsafe impl<T: Sync> Sync for RefMutContainer<T> {}

#[derive(Clone)]
pub struct RustRef<FromRust>(pub RefMutContainer<FromRust>);

impl<FromRust> RustRef<FromRust> {
    pub fn new(s: &mut FromRust) -> Self {
        Self(RefMutContainer::new(s))
    }

    /// Provides a way to access a reference to the underlying data
    pub fn map_as_ref<F, U>(&self, f: F) -> PyResult<U>
    where
        F: FnOnce(&FromRust) -> U,
    {
        self.0.map(f).ok_or_else(Self::destroyed_error)
    }

    /// Provides a way to access a mutable reference to the underlying data
    pub fn map_as_mut<F, U>(&mut self, f: F) -> PyResult<U>
    where
        F: FnOnce(&mut FromRust) -> U,
    {
        self.0.map_mut(f).ok_or_else(Self::destroyed_error)
    }

    pub fn destroyed_error() -> PyErr {
        runtime_error(DESTROYED_ERR_MSG)
    }
}

#[macro_export]
// This macro accepts the raft-rs (Rust) type as the first argument and the Py type as the second argument,
// And adds some boilerplate codes implementing the From trait for conversion between the two types.
macro_rules! implement_type_conversion {
    ($Typ:ty, $Py_Typ_Mut:ident) => {
        use utils::errors::DESTROYED_ERR_MSG;

        impl From<$Py_Typ_Mut<'_>> for $Typ {
            fn from(val: $Py_Typ_Mut<'_>) -> Self {
                match val {
                    $Py_Typ_Mut::Owned(x) => x.inner.clone(),
                    $Py_Typ_Mut::RefMut(mut x) => {
                        x.inner.map_as_mut(|x| x.clone()).expect(DESTROYED_ERR_MSG)
                    }
                }
            }
        }

        impl From<&mut $Py_Typ_Mut<'_>> for $Typ {
            fn from(val: &mut $Py_Typ_Mut<'_>) -> Self {
                match val {
                    $Py_Typ_Mut::Owned(x) => x.inner.clone(),
                    $Py_Typ_Mut::RefMut(x) => {
                        x.inner.map_as_mut(|x| x.clone()).expect(DESTROYED_ERR_MSG)
                    }
                }
            }
        }
    };
}
