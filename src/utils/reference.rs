// Ref:
// RefMutContainer implementation is greatly inspired from huggingface/tokenizer's python binding's.
// https://github.com/huggingface/tokenizers/blob/main/bindings/python/src/utils/mod.rs
use pyo3::prelude::*;
use std::collections::HashMap;
use std::ops::{Deref, DerefMut};
use std::ptr::NonNull;
use std::sync::{Arc, Mutex, Weak};

use super::errors::{DestroyedRefUsedError, DESTROYED_ERR_MSG};

// References that need to be cleaned up.
type RefMutContainerTable<T> = HashMap<u64, Weak<Mutex<Option<NonNull<T>>>>>;

#[derive(Clone)]
pub struct RefMutOwner<T> {
    pub inner: T,
    refs: Arc<Mutex<RefMutContainerTable<T>>>,
}

unsafe impl<T: Send> Send for RefMutOwner<T> {}
unsafe impl<T: Sync> Sync for RefMutOwner<T> {}

impl<T> RefMutOwner<T> {
    pub fn new(inner: T) -> Self {
        Self {
            inner,
            refs: Arc::new(Mutex::new(HashMap::new())),
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
        self.refs.lock().unwrap().iter_mut().for_each(|weak_ref| {
            if let Some(arc) = weak_ref.1.upgrade() {
                if let Ok(mut ptr) = arc.lock() {
                    ptr.take();
                }
            }
        });
    }
}

#[derive(Clone)]
pub struct RefMutContainer<T> {
    inner: Arc<Mutex<Option<NonNull<T>>>>,
    id: Option<u64>,
    owner_refs: Weak<Mutex<RefMutContainerTable<T>>>,
}

impl<T> Drop for RefMutContainer<T> {
    fn drop(&mut self) {
        if let Some(owner_refs_ptr) = self.owner_refs.upgrade() {
            owner_refs_ptr.lock().unwrap().remove(&self.id.unwrap());
        }
    }
}

impl<T> RefMutContainer<T> {
    pub fn new(content: &mut RefMutOwner<T>) -> Self {
        let arc = Arc::new(Mutex::new(NonNull::new(&mut content.inner)));
        let mut map = content.refs.lock().unwrap();
        let id = map.keys().max().cloned().unwrap_or(0) + 1;
        map.insert(id, Arc::downgrade(&arc));

        RefMutContainer {
            inner: arc,
            id: Some(id),
            owner_refs: Arc::downgrade(&content.refs),
        }
    }

    pub fn new_raw(content: &mut T) -> Self {
        RefMutContainer {
            inner: Arc::new(Mutex::new(NonNull::new(content))),
            id: None,
            owner_refs: Weak::new(),
        }
    }

    pub fn map_as_ref<F, U>(&self, f: F) -> PyResult<U>
    where
        F: FnOnce(&T) -> U,
    {
        let lock = self.inner.lock().unwrap();
        let ptr = lock
            .as_ref()
            .ok_or(DestroyedRefUsedError::new_err(DESTROYED_ERR_MSG))?;
        Ok(f(unsafe { ptr.as_ref() }))
    }

    pub fn map_as_mut<F, U>(&mut self, f: F) -> PyResult<U>
    where
        F: FnOnce(&mut T) -> U,
    {
        let mut lock = self.inner.lock().unwrap();
        let ptr = lock
            .as_mut()
            .ok_or(DestroyedRefUsedError::new_err(DESTROYED_ERR_MSG))?;
        Ok(f(unsafe { ptr.as_mut() }))
    }
}

unsafe impl<T: Send> Send for RefMutContainer<T> {}
unsafe impl<T: Sync> Sync for RefMutContainer<T> {}

#[macro_export]
// This macro accepts the raft-rs (Rust) type as the first argument and the Py type as the second argument,
// And adds some boilerplate codes implementing the From trait for conversion between the two types.
macro_rules! implement_type_conversion {
    ($Typ:ty, $PyTypMut:ident) => {
        use $crate::utils::errors::DESTROYED_ERR_MSG;

        impl From<$PyTypMut<'_>> for $Typ {
            fn from(val: $PyTypMut<'_>) -> Self {
                match val {
                    $PyTypMut::Owned(x) => x.inner.inner.clone(),
                    $PyTypMut::RefMut(mut x) => {
                        x.inner.map_as_mut(|x| x.clone()).expect(DESTROYED_ERR_MSG)
                    }
                }
            }
        }

        impl From<&mut $PyTypMut<'_>> for $Typ {
            fn from(val: &mut $PyTypMut<'_>) -> Self {
                match val {
                    $PyTypMut::Owned(x) => x.inner.inner.clone(),
                    $PyTypMut::RefMut(x) => {
                        x.inner.map_as_mut(|x| x.clone()).expect(DESTROYED_ERR_MSG)
                    }
                }
            }
        }
    };
}
