// Ref:: https://github.com/huggingface/tokenizers/tree/main/bindings/python
use pyo3::prelude::*;
use pyo3::PyErr;
use std::ops::Deref;
use std::ops::DerefMut;
use std::sync::{Arc, Mutex, Weak};

use crate::errors::runtime_error;
use crate::errors::DESTROYED_ERR_MSG;

#[derive(Clone)]
pub struct RefMutOwner<T> {
    pub inner: T,
    pub refs: Vec<Weak<Mutex<Option<*mut RefMutOwner<T>>>>>,
}

unsafe impl<T: Send> Send for RefMutOwner<T> {}
unsafe impl<T: Sync> Sync for RefMutOwner<T> {}

impl<T> RefMutOwner<T> {
    pub fn new(inner: T) -> Self {
        Self {
            inner,
            refs: vec![],
        }
    }
}

impl<T> Deref for RefMutOwner<T> {
    type Target = T;

    fn deref(&self) -> &Self::Target {
        &self.inner
    }
}

impl<T> DerefMut for RefMutOwner<T> {
    fn deref_mut(&mut self) -> &mut T {
        &mut self.inner
    }
}

impl<T> Drop for RefMutOwner<T> {
    fn drop(&mut self) {
        self.refs.iter_mut().for_each(|weak_ref| {
            if let Some(arc) = weak_ref.upgrade() {
                if let Ok(mut ptr) = arc.lock() {
                    ptr.take();
                }
            }
        });
    }
}

#[derive(Clone)]
pub struct RefMutContainer<T> {
    inner: Arc<Mutex<Option<*mut RefMutOwner<T>>>>,
}

impl<T> RefMutContainer<T> {
    pub fn new(content: &mut RefMutOwner<T>) -> Self {
        let arc: Arc<Mutex<Option<*mut RefMutOwner<T>>>> = Arc::new(Mutex::new(Some(content)));
        content.refs.push(Arc::downgrade(&arc));
        RefMutContainer { inner: arc }
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

unsafe impl<T: Send> Send for RefMutContainer<T> {}
unsafe impl<T: Sync> Sync for RefMutContainer<T> {}

#[derive(Clone)]
pub struct RustRef<T>(pub RefMutContainer<T>);

impl<T> RustRef<T> {
    pub fn new(s: &mut RefMutOwner<T>) -> Self {
        Self(RefMutContainer::new(s))
    }

    /// Provides a way to access a reference to the underlying data
    pub fn map_as_ref<F, U>(&self, f: F) -> PyResult<U>
    where
        F: FnOnce(&T) -> U,
    {
        self.0.map(f).ok_or_else(Self::destroyed_error)
    }

    /// Provides a way to access a mutable reference to the underlying data
    pub fn map_as_mut<F, U>(&mut self, f: F) -> PyResult<U>
    where
        F: FnOnce(&mut T) -> U,
    {
        self.0.map_mut(f).ok_or_else(Self::destroyed_error)
    }

    pub fn destroyed_error() -> PyErr {
        runtime_error(DESTROYED_ERR_MSG)
    }
}
