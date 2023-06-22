// Ref:: https://github.com/huggingface/tokenizers/tree/main/bindings/python
use pyo3::prelude::*;
use pyo3::PyErr;
use std::ops::Deref;
use std::ops::DerefMut;
use std::sync::Weak;
use std::sync::{Arc, Mutex};

use crate::errors::runtime_error;
use crate::errors::DESTROYED_ERR_MSG;

#[derive(Clone)]
pub struct RefMutOwner<T> {
    pub inner: T,
    pub refs: Vec<Weak<Mutex<Option<*mut RefMutOwner<T>>>>>,
}

unsafe impl<T: Send> Send for RefMutOwner<T> {}
unsafe impl<T: Sync> Sync for RefMutOwner<T> {}

impl<T> Drop for RefMutOwner<T> {
    fn drop(&mut self) {
        println!("config drop!");

        self.refs.iter_mut().for_each(|weak_ptr| {
            if let Some(weak_inner) = weak_ptr.upgrade() {
                println!("upgrade!!");
                if let Ok(mut inner) = weak_inner.lock() {
                    *inner = None;
                }
            } else {
                // Weak가 이미 해제되어 있어 Ref를 해제할 수 없는데 정작 내부에 들고 있는 레퍼런스들은 drop 되지 않았다.
                println!("already dropped!!");
            }

            // println!("drop ref!!");
            // let p = r.to_owned();

            // let k = r.upgrade().unwrap();
            // k.lock().unwrap().as_ref().take();
        });
    }
}

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

#[derive(Clone)]
pub struct RefMutContainer<T> {
    inner: Arc<Mutex<Option<*mut RefMutOwner<T>>>>,
}

impl<T> RefMutContainer<T> {
    pub fn new(content: &mut RefMutOwner<T>) -> Self {
        let lock: Arc<Mutex<Option<*mut RefMutOwner<T>>>> = Arc::new(Mutex::new(Some(content)));
        let wk = Arc::downgrade(&lock);
        content.refs.push(wk);

        RefMutContainer {
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
