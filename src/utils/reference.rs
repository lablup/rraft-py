// Ref:
// RefMutContainer implementation is greatly inspired from huggingface/tokenizer's python binding's.
// https://github.com/huggingface/tokenizers/blob/main/bindings/python/src/utils/mod.rs
use pyo3::prelude::*;
use std::collections::HashMap;
use std::ops::{Deref, DerefMut};
use std::ptr::NonNull;
use std::sync::{Arc, Mutex, Weak};

use crate::errors::DestroyedRefUsedError;
use crate::errors::DESTROYED_ERR_MSG;

#[derive(Clone)]
pub struct RefMutOwner<T> {
    pub inner: T,
    // References that need to be cleaned up.
    refs: HashMap<u64, Weak<Mutex<Option<NonNull<T>>>>>,
}

unsafe impl<T: Send> Send for RefMutOwner<T> {}
unsafe impl<T: Sync> Sync for RefMutOwner<T> {}

impl<T> RefMutOwner<T> {
    pub fn new(inner: T) -> Self {
        Self {
            inner,
            refs: HashMap::new(),
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
    owner_table: Option<NonNull<HashMap<u64, Weak<Mutex<Option<NonNull<T>>>>>>>,
}

impl<T> Drop for RefMutContainer<T> {
    fn drop(&mut self) {
        if let Some(id) = self.id {
            let mut owner_table_ptr = self.owner_table.unwrap();
            let owner_table = unsafe { owner_table_ptr.as_mut() };
            owner_table.remove(&id);
        }
    }
}

impl<T> RefMutContainer<T> {
    pub fn new(content: &mut RefMutOwner<T>) -> Self {
        let arc = Arc::new(Mutex::new(NonNull::new(&mut content.inner)));
        let id = content.refs.keys().max().unwrap_or_else(|| &0) + 1;
        content.refs.insert(id, Arc::downgrade(&arc));

        RefMutContainer {
            inner: arc,
            id: Some(id),
            owner_table: NonNull::new(&mut content.refs),
        }
    }

    pub fn new_raw(content: &mut T) -> Self {
        RefMutContainer {
            inner: Arc::new(Mutex::new(NonNull::new(content))),
            id: None,
            owner_table: None,
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
    ($Typ:ty, $Py_Typ_Mut:ident) => {
        use utils::errors::DESTROYED_ERR_MSG;

        impl From<$Py_Typ_Mut<'_>> for $Typ {
            fn from(val: $Py_Typ_Mut<'_>) -> Self {
                match val {
                    $Py_Typ_Mut::Owned(x) => x.inner.inner.clone(),
                    $Py_Typ_Mut::RefMut(mut x) => {
                        x.inner.map_as_mut(|x| x.clone()).expect(DESTROYED_ERR_MSG)
                    }
                }
            }
        }

        impl From<&mut $Py_Typ_Mut<'_>> for $Typ {
            fn from(val: &mut $Py_Typ_Mut<'_>) -> Self {
                match val {
                    $Py_Typ_Mut::Owned(x) => x.inner.inner.clone(),
                    $Py_Typ_Mut::RefMut(x) => {
                        x.inner.map_as_mut(|x| x.clone()).expect(DESTROYED_ERR_MSG)
                    }
                }
            }
        }
    };
}
