use std::ops::{Deref, DerefMut};

use pyo3::{intern, prelude::*};

use crate::implement_type_conversion;
use crate::utils::{
    errors::PyRaftError,
    reference::{RefMutContainer, RefMutOwner},
    unsafe_cast::make_mut,
};
use raft::{prelude::ConfState, storage::MemStorage, storage::Storage, GetEntriesContext};

use crate::raftpb_bindings::{conf_state::PyConfStateMut, entry::PyEntry, snapshot::PySnapshot};

use super::mem_storage_core::PyMemStorageCoreRef;

use crate::bindings::{get_entries_context::PyGetEntriesContextRef, raft_state::PyRaftState};

#[derive(Clone)]
#[pyclass(name = "MemStorage")]
pub struct PyMemStorage {
    pub inner: RefMutOwner<MemStorage>,
}

#[derive(Clone)]
#[pyclass(name = "MemStorageRef")]
pub struct PyMemStorageRef {
    pub inner: RefMutContainer<MemStorage>,
}

#[derive(FromPyObject)]
pub enum PyMemStorageMut<'p> {
    Owned(PyRefMut<'p, PyMemStorage>),
    RefMut(PyMemStorageRef),
}

implement_type_conversion!(MemStorage, PyMemStorageMut);

#[pymethods]
impl PyMemStorage {
    #[new]
    pub fn new() -> Self {
        PyMemStorage {
            inner: RefMutOwner::new(MemStorage::new()),
        }
    }

    #[staticmethod]
    pub fn default() -> Self {
        PyMemStorage {
            inner: RefMutOwner::new(MemStorage::default()),
        }
    }

    #[staticmethod]
    pub fn new_with_conf_state(cs: PyConfStateMut) -> Self {
        PyMemStorage {
            inner: RefMutOwner::new(MemStorage::new_with_conf_state::<ConfState>(cs.into())),
        }
    }

    pub fn make_ref(&mut self) -> PyMemStorageRef {
        PyMemStorageRef {
            inner: RefMutContainer::new(&mut self.inner),
        }
    }

    fn __getattr__(this: PyObject, py: Python, attr: &str) -> PyResult<PyObject> {
        let reference = this.call_method0(py, intern!(py, "make_ref"))?;
        reference.getattr(py, attr)
    }
}

#[pymethods]
impl PyMemStorageRef {
    pub fn clone(&mut self) -> PyResult<PyMemStorage> {
        Ok(PyMemStorage {
            inner: RefMutOwner::new(self.inner.map_as_mut(|x| x.clone())?),
        })
    }

    pub fn initialize_with_conf_state(&mut self, cs: PyConfStateMut) -> PyResult<()> {
        self.inner
            .map_as_mut(|inner| inner.initialize_with_conf_state::<ConfState>(cs.into()))
    }

    pub fn initial_state(&self) -> PyResult<PyRaftState> {
        self.inner.map_as_ref(|inner| {
            inner
                .initial_state()
                .map(|state| PyRaftState {
                    inner: RefMutOwner::new(state),
                })
                .map_err(|e| PyRaftError(e).into())
        })?
    }

    pub fn first_index(&self) -> PyResult<u64> {
        self.inner
            .map_as_ref(|inner| inner.first_index().map_err(|e| PyRaftError(e).into()))?
    }

    pub fn last_index(&self) -> PyResult<u64> {
        self.inner
            .map_as_ref(|inner| inner.last_index().map_err(|e| PyRaftError(e).into()))?
    }

    pub fn term(&self, idx: u64) -> PyResult<u64> {
        self.inner
            .map_as_ref(|inner| inner.term(idx).map_err(|e| PyRaftError(e).into()))?
    }

    pub fn snapshot(&self, request_index: u64, _to: u64) -> PyResult<PySnapshot> {
        self.inner.map_as_ref(|inner| {
            inner
                .snapshot(request_index, _to)
                .map(|snapshot| PySnapshot {
                    inner: RefMutOwner::new(snapshot),
                })
                .map_err(|e| PyRaftError(e).into())
        })?
    }

    pub fn entries(
        &self,
        low: u64,
        high: u64,
        context: &mut PyGetEntriesContextRef,
        max_size: Option<u64>,
        py: Python,
    ) -> PyResult<PyObject> {
        let context = context.inner.map_as_mut(|context| unsafe {
            std::ptr::replace(context, GetEntriesContext::empty(false))
        })?;

        self.inner.map_as_ref(|inner| {
            inner
                .entries(low, high, max_size, context)
                .map(|entries| {
                    entries
                        .into_iter()
                        .map(|entry| PyEntry {
                            inner: RefMutOwner::new(entry),
                        })
                        .collect::<Vec<_>>()
                        .into_py(py)
                })
                .map_err(|e| PyRaftError(e).into())
        })?
    }

    pub fn wl(&mut self) -> PyResult<PyMemStorageCoreRef> {
        self.inner.map_as_mut(|inner| PyMemStorageCoreRef {
            inner: RefMutContainer::new_raw(inner.wl().deref_mut()),
        })
    }

    pub fn rl(&self) -> PyResult<PyMemStorageCoreRef> {
        self.inner.map_as_ref(|inner| PyMemStorageCoreRef {
            inner: RefMutContainer::new_raw(unsafe { make_mut(inner.rl().deref()) }),
        })
    }
}
