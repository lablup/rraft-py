use pyo3::{prelude::*, types::PyList};

use raft::storage::MemStorageCore;
use utils::{errors::to_pyresult, reference::RustRef, unsafe_cast::make_mut};

use crate::eraftpb::{
    conf_state::Py_ConfState_Mut,
    entry::Py_Entry_Mut,
    hard_state::{Py_HardState_Mut, Py_HardState_Ref},
    snapshot::Py_Snapshot_Mut,
};

#[pyclass(name = "MemStorageCore_Owner")]
pub struct Py_MemStorageCore_Owner {
    pub inner: MemStorageCore,
}

#[pyclass(name = "MemStorageCore_Ref")]
pub struct Py_MemStorageCore_Ref {
    pub inner: RustRef<MemStorageCore>,
}

#[pymethods]
impl Py_MemStorageCore_Owner {
    #[staticmethod]
    pub fn default() -> Self {
        Py_MemStorageCore_Owner {
            inner: MemStorageCore::default(),
        }
    }

    pub fn make_ref(&mut self) -> Py_MemStorageCore_Ref {
        Py_MemStorageCore_Ref {
            inner: RustRef::new(&mut self.inner),
        }
    }

    fn __getattr__(this: PyObject, py: Python<'_>, attr: &str) -> PyResult<PyObject> {
        let reference = this.call_method0(py, "make_ref")?;
        reference.getattr(py, attr)
    }
}

#[pymethods]
impl Py_MemStorageCore_Ref {
    pub fn append(&mut self, ents: &PyList) -> PyResult<()> {
        let mut entries = ents.extract::<Vec<Py_Entry_Mut>>()?;

        self.inner
            .map_as_mut(|inner| {
                inner.append(
                    entries
                        .iter_mut()
                        .map(|x| x.into())
                        .collect::<Vec<_>>()
                        .as_slice(),
                )
            })
            .and_then(to_pyresult)
    }

    pub fn apply_snapshot(&mut self, snapshot: Py_Snapshot_Mut) -> PyResult<()> {
        self.inner
            .map_as_mut(|inner| inner.apply_snapshot(snapshot.into()))
            .and_then(to_pyresult)
    }

    pub fn compact(&mut self, compact_index: u64) -> PyResult<()> {
        self.inner
            .map_as_mut(|inner| inner.compact(compact_index))
            .and_then(to_pyresult)
    }

    pub fn commit_to(&mut self, index: u64) -> PyResult<()> {
        self.inner
            .map_as_mut(|inner| inner.commit_to(index))
            .and_then(to_pyresult)
    }

    pub fn commit_to_and_set_conf_states(
        &mut self,
        idx: u64,
        cs: Option<Py_ConfState_Mut>,
    ) -> PyResult<()> {
        self.inner
            .map_as_mut(|inner| match cs {
                Some(x) => inner.commit_to_and_set_conf_states(idx, Some(x.into())),
                None => inner.commit_to_and_set_conf_states(idx, None),
            })
            .and_then(to_pyresult)
    }

    pub fn hard_state(&self) -> PyResult<Py_HardState_Ref> {
        self.inner.map_as_ref(|inner| Py_HardState_Ref {
            inner: RustRef::new(unsafe { make_mut(inner.hard_state()) }),
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
}
