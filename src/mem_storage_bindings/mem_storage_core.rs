use crate::bindings::get_entries_context::PyGetEntriesContext;
use pyo3::{intern, prelude::*, types::PyList};

use crate::utils::{
    errors::PyRaftError,
    reference::{RefMutContainer, RefMutOwner},
};
use raft::storage::MemStorageCore;

use crate::raftpb_bindings::{
    conf_state::PyConfStateMut,
    entry::PyEntryMut,
    hard_state::{PyHardStateMut, PyHardStateRef},
    snapshot::PySnapshotMut,
};

#[pyclass(name = "MemStorageCore")]
pub struct PyMemStorageCore {
    pub inner: RefMutOwner<MemStorageCore>,
}

#[pyclass(name = "MemStorageCoreRef")]
pub struct PyMemStorageCoreRef {
    pub inner: RefMutContainer<MemStorageCore>,
}

#[pymethods]
impl PyMemStorageCore {
    #[staticmethod]
    pub fn default() -> Self {
        PyMemStorageCore {
            inner: RefMutOwner::new(MemStorageCore::default()),
        }
    }

    pub fn make_ref(&mut self) -> PyMemStorageCoreRef {
        PyMemStorageCoreRef {
            inner: RefMutContainer::new(&mut self.inner),
        }
    }

    fn __getattr__(this: PyObject, py: Python, attr: &str) -> PyResult<PyObject> {
        let reference = this.call_method0(py, intern!(py, "make_ref"))?;
        reference.getattr(py, attr)
    }
}

#[pymethods]
impl PyMemStorageCoreRef {
    pub fn append(&mut self, ents: &PyList) -> PyResult<()> {
        let mut entries = ents.extract::<Vec<PyEntryMut>>()?;

        self.inner.map_as_mut(|inner| {
            inner
                .append(
                    entries
                        .iter_mut()
                        .map(|x| x.into())
                        .collect::<Vec<_>>()
                        .as_slice(),
                )
                .map_err(|e| PyRaftError(e).into())
        })?
    }

    pub fn apply_snapshot(&mut self, snapshot: PySnapshotMut) -> PyResult<()> {
        self.inner.map_as_mut(|inner| {
            inner
                .apply_snapshot(snapshot.into())
                .map_err(|e| PyRaftError(e).into())
        })?
    }

    pub fn compact(&mut self, compact_index: u64) -> PyResult<()> {
        self.inner.map_as_mut(|inner| {
            inner
                .compact(compact_index)
                .map_err(|e| PyRaftError(e).into())
        })?
    }

    pub fn commit_to(&mut self, index: u64) -> PyResult<()> {
        self.inner
            .map_as_mut(|inner| inner.commit_to(index).map_err(|e| PyRaftError(e).into()))?
    }

    pub fn commit_to_and_set_conf_states(
        &mut self,
        idx: u64,
        cs: Option<PyConfStateMut>,
    ) -> PyResult<()> {
        self.inner.map_as_mut(|inner| {
            match cs {
                Some(x) => inner.commit_to_and_set_conf_states(idx, Some(x.into())),
                None => inner.commit_to_and_set_conf_states(idx, None),
            }
            .map_err(|e| PyRaftError(e).into())
        })?
    }

    pub fn hard_state(&mut self) -> PyResult<PyHardStateRef> {
        self.inner.map_as_mut(|inner| PyHardStateRef {
            inner: RefMutContainer::new_raw(inner.mut_hard_state()),
        })
    }

    pub fn set_hardstate(&mut self, hs: PyHardStateMut) -> PyResult<()> {
        self.inner
            .map_as_mut(|inner| inner.set_hardstate(hs.into()))
    }

    pub fn set_conf_state(&mut self, cs: PyConfStateMut) -> PyResult<()> {
        self.inner
            .map_as_mut(|inner| inner.set_conf_state(cs.into()))
    }

    pub fn trigger_snap_unavailable(&mut self) -> PyResult<()> {
        self.inner
            .map_as_mut(|inner| inner.trigger_snap_unavailable())
    }

    pub fn trigger_log_unavailable(&mut self, v: bool) -> PyResult<()> {
        self.inner
            .map_as_mut(|inner| inner.trigger_log_unavailable(v))
    }

    pub fn take_get_entries_context(&mut self) -> PyResult<Option<PyGetEntriesContext>> {
        self.inner.map_as_mut(|inner| {
            inner
                .take_get_entries_context()
                .map(|ctx| PyGetEntriesContext {
                    inner: RefMutOwner::new(ctx),
                })
        })
    }
}
