use pyo3::prelude::*;
use pyo3::PyErr;
use std::sync::{Arc, Mutex};
use crate::errors::destroyed_error as _destroyed_error;

pub struct UncloneableRefMutContainer<T> {
    inner: Arc<Mutex<Option<*mut T>>>,
}

impl<T> UncloneableRefMutContainer<T> {
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

impl<T> Drop for UncloneableRefMutContainer<T> {
    fn drop(&mut self) {
        self.inner.lock().unwrap().take();
    }
}

unsafe impl<T: Send> Send for UncloneableRefMutContainer<T> {}
unsafe impl<T: Sync> Sync for UncloneableRefMutContainer<T> {}

pub struct UncloneableRustRef<FromRust>(pub UncloneableRefMutContainer<FromRust>);

pub trait UncloneableRustRef_Default_Implementation<FromRust> {
    fn new(s: &mut FromRust) -> Self;
    fn destroyed_error() -> PyErr;
    fn map_as_ref<F, U>(&self, f: F) -> PyResult<U>
    where
        F: FnOnce(&FromRust) -> U;
    fn map_as_mut<F, U>(&mut self, f: F) -> PyResult<U>
    where
        F: FnOnce(&mut FromRust) -> U;
}

impl<FromRust> UncloneableRustRef_Default_Implementation<FromRust> for UncloneableRustRef<FromRust> {
    fn new(s: &mut FromRust) -> Self {
        Self(UncloneableRefMutContainer::new(s))
    }

    /// Provides a way to access a reference to the underlying data
    fn map_as_ref<F, U>(&self, f: F) -> PyResult<U>
    where
        F: FnOnce(&FromRust) -> U,
    {
        self.0.map(f).ok_or_else(Self::destroyed_error)
    }

    /// Provides a way to access a mutable reference to the underlying data
    fn map_as_mut<F, U>(&mut self, f: F) -> PyResult<U>
    where
        F: FnOnce(&mut FromRust) -> U,
    {
        self.0.map_mut(f).ok_or_else(Self::destroyed_error)
    }

    fn destroyed_error() -> PyErr {
        _destroyed_error()
    }
}
