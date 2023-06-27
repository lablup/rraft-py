use bindings::get_entries_context::Py_GetEntriesContext;
use pyo3::{intern, prelude::*, types::PyList};

use raft::storage::MemStorageCore;
use utils::{
    errors::Py_RaftError,
    reference::{RefMutContainer, RefMutOwner},
};

use raftpb_bindings::{
    conf_state::Py_ConfState_Mut,
    entry::Py_Entry_Mut,
    hard_state::{Py_HardState_Mut, Py_HardState_Ref},
    snapshot::Py_Snapshot_Mut,
};

#[pyclass(name = "MemStorageCore")]
pub struct Py_MemStorageCore {
    pub inner: RefMutOwner<MemStorageCore>,
}

#[pyclass(name = "MemStorageCore_Ref")]
pub struct Py_MemStorageCore_Ref {
    pub inner: RefMutContainer<MemStorageCore>,
}

#[pymethods]
impl Py_MemStorageCore {
    #[staticmethod]
    pub fn default() -> Self {
        Py_MemStorageCore {
            inner: RefMutOwner::new(MemStorageCore::default()),
        }
    }

    pub fn make_ref(&mut self) -> Py_MemStorageCore_Ref {
        Py_MemStorageCore_Ref {
            inner: RefMutContainer::new(&mut self.inner),
        }
    }

    fn __getattr__(this: PyObject, py: Python, attr: &str) -> PyResult<PyObject> {
        let reference = this.call_method0(py, intern!(py, "make_ref"))?;
        reference.getattr(py, attr)
    }
}

#[pymethods]
impl Py_MemStorageCore_Ref {
    pub fn append(&mut self, ents: &PyList) -> PyResult<()> {
        let mut entries = ents.extract::<Vec<Py_Entry_Mut>>()?;

        self.inner.map_as_mut(|inner| {
            inner
                .append(
                    entries
                        .iter_mut()
                        .map(|x| x.into())
                        .collect::<Vec<_>>()
                        .as_slice(),
                )
                .map_err(|e| Py_RaftError(e).into())
        })?
    }

    pub fn apply_snapshot(&mut self, snapshot: Py_Snapshot_Mut) -> PyResult<()> {
        self.inner.map_as_mut(|inner| {
            inner
                .apply_snapshot(snapshot.into())
                .map_err(|e| Py_RaftError(e).into())
        })?
    }

    pub fn compact(&mut self, compact_index: u64) -> PyResult<()> {
        self.inner.map_as_mut(|inner| {
            inner
                .compact(compact_index)
                .map_err(|e| Py_RaftError(e).into())
        })?
    }

    pub fn commit_to(&mut self, index: u64) -> PyResult<()> {
        self.inner
            .map_as_mut(|inner| inner.commit_to(index).map_err(|e| Py_RaftError(e).into()))?
    }

    pub fn commit_to_and_set_conf_states(
        &mut self,
        idx: u64,
        cs: Option<Py_ConfState_Mut>,
    ) -> PyResult<()> {
        self.inner.map_as_mut(|inner| {
            match cs {
                Some(x) => inner.commit_to_and_set_conf_states(idx, Some(x.into())),
                None => inner.commit_to_and_set_conf_states(idx, None),
            }
            .map_err(|e| Py_RaftError(e).into())
        })?
    }

    pub fn hard_state(&mut self) -> PyResult<Py_HardState_Ref> {
        self.inner.map_as_mut(|inner| Py_HardState_Ref {
            inner: RefMutContainer::new_raw(inner.mut_hard_state()),
        })
    }

    pub fn set_hardstate(&mut self, hs: Py_HardState_Mut) -> PyResult<()> {
        self.inner
            .map_as_mut(|inner| inner.set_hardstate(hs.into()))
    }

    pub fn set_conf_state(&mut self, cs: Py_ConfState_Mut) -> PyResult<()> {
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

    pub fn take_get_entries_context(&mut self) -> PyResult<Option<Py_GetEntriesContext>> {
        self.inner.map_as_mut(|inner| {
            inner
                .take_get_entries_context()
                .map(|ctx| Py_GetEntriesContext {
                    inner: RefMutOwner::new(ctx),
                })
        })
    }
}
