use std::ops::{Deref, DerefMut};

use pyo3::prelude::*;

use raft::{prelude::ConfState, storage::MemStorage, storage::Storage};
use utils::{
    errors::to_pyresult,
    reference::RustRef,
    uncloneable_reference::UncloneableRustRef,
    unsafe_cast::make_mut,
};

use crate::eraftpb::{
    conf_state::Py_ConfState_Mut, entry::Py_Entry_Owner, snapshot::Py_Snapshot_Owner,
};

use super::{mem_storage_core::Py_MemStorageCore_Ref, raft_state::Py_RaftState_Owner};

#[derive(Clone)]
#[pyclass(name = "MemStorage_Owner")]
pub struct Py_MemStorage_Owner {
    pub inner: MemStorage,
}

#[derive(Clone)]
#[pyclass(name = "MemStorage_Ref")]
pub struct Py_MemStorage_Ref {
    pub inner: RustRef<MemStorage>,
}

#[derive(FromPyObject)]
pub enum Py_MemStorage_Mut<'p> {
    Owned(PyRefMut<'p, Py_MemStorage_Owner>),
    RefMut(Py_MemStorage_Ref),
}

impl Into<MemStorage> for Py_MemStorage_Mut<'_> {
    fn into(self) -> MemStorage {
        match self {
            Py_MemStorage_Mut::Owned(x) => x.inner.clone(),
            Py_MemStorage_Mut::RefMut(mut x) => x.inner.map_as_mut(|x| x.clone()).unwrap(),
        }
    }
}

impl Into<MemStorage> for &mut Py_MemStorage_Mut<'_> {
    fn into(self) -> MemStorage {
        match self {
            Py_MemStorage_Mut::Owned(x) => x.inner.clone(),
            Py_MemStorage_Mut::RefMut(x) => x.inner.map_as_mut(|x| x.clone()).unwrap(),
        }
    }
}

#[pymethods]
impl Py_MemStorage_Owner {
    #[new]
    pub fn new() -> Self {
        Py_MemStorage_Owner {
            inner: MemStorage::default(),
        }
    }

    #[staticmethod]
    pub fn new_with_conf_state(cs: Py_ConfState_Mut) -> Self {
        Py_MemStorage_Owner {
            inner: MemStorage::new_with_conf_state::<ConfState>(cs.into()),
        }
    }

    pub fn make_ref(&mut self) -> Py_MemStorage_Ref {
        Py_MemStorage_Ref {
            inner: RustRef::new(&mut self.inner),
        }
    }

    pub fn clone(&mut self) -> Py_MemStorage_Owner {
        Py_MemStorage_Owner {
            inner: self.inner.clone(),
        }
    }
}

#[pymethods]
impl Py_MemStorage_Ref {
    pub fn clone(&mut self) -> Py_MemStorage_Owner {
        Py_MemStorage_Owner {
            inner: self.inner.map_as_mut(|x| x.clone()).unwrap(),
        }
    }

    pub fn initialize_with_conf_state(&mut self, cs: Py_ConfState_Mut) -> PyResult<()> {
        self.inner
            .map_as_mut(|inner| inner.initialize_with_conf_state::<ConfState>(cs.into()))
    }

    pub fn initial_state(&self) -> PyResult<Py_RaftState_Owner> {
        self.inner.map_as_ref(|inner| Py_RaftState_Owner {
            inner: inner.initial_state().unwrap(),
        })
    }

    pub fn first_index(&self) -> PyResult<u64> {
        self.inner.map_as_ref(|inner| inner.first_index().unwrap())
    }

    pub fn last_index(&self) -> PyResult<u64> {
        self.inner.map_as_ref(|inner| inner.last_index().unwrap())
    }

    pub fn term(&self, idx: u64) -> PyResult<u64> {
        self.inner.map_as_ref(|inner| inner.term(idx).unwrap())
    }

    pub fn snapshot(&self, request_index: u64) -> PyResult<Py_Snapshot_Owner> {
        self.inner.map_as_ref(|inner| Py_Snapshot_Owner {
            inner: inner.snapshot(request_index).unwrap(),
        })
    }

    pub fn entries(
        &self,
        low: u64,
        high: u64,
        max_size: Option<u64>,
        py: Python,
    ) -> PyResult<PyObject> {
        self.inner.map_as_ref(|inner| {
            let entries = inner.entries(low, high, max_size).unwrap();

            entries
                .into_iter()
                .map(|entry| Py_Entry_Owner { inner: entry })
                .collect::<Vec<_>>()
                .into_py(py)
        })
    }

    pub fn wl(&mut self, cb: PyObject, py: Python) -> PyResult<()> {
        self.inner.map_as_mut(|inner| {
            let mut wl = inner.wl();

            let arg = Py_MemStorageCore_Ref {
                inner: UncloneableRustRef::new(wl.deref_mut()),
            };

            cb.call1(py, (arg,));
        })
    }

    pub fn rl(&self, cb: PyObject, py: Python) -> PyResult<()> {
        self.inner.map_as_ref(|inner| {
            let rl = inner.rl();

            let arg = Py_MemStorageCore_Ref {
                inner: UncloneableRustRef::new(unsafe { make_mut(rl.deref()) }),
            };

            cb.call1(py, (arg,));
        })
    }
}
