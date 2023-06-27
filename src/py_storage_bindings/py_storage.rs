use bindings::get_entries_context::{Py_GetEntriesContext, Py_GetEntriesContext_Ref};
use pyo3::types::PyList;
use pyo3::{intern, prelude::*};

use raft::storage::Storage;
use raft::GetEntriesContext;
use raftpb_bindings::hard_state::Py_HardState;

use raftpb_bindings::entry::Py_Entry_Ref;
use raftpb_bindings::snapshot::{Py_Snapshot_Mut, Py_Snapshot_Ref};

use bindings::raft_state::{Py_RaftState_Mut, Py_RaftState_Ref};
use raftpb_bindings::entry::Py_Entry_Mut;
use utils::errors::{makeNativeRaftError, Py_RaftError, DESTROYED_ERR_MSG};
use utils::reference::{RustRef, RefMutOwner};
use utils::unsafe_cast::make_mut;

#[derive(Clone)]
#[pyclass(name = "Storage")]
pub struct Py_Storage {
    pub storage: Py<PyAny>,
}

#[derive(Clone)]
#[pyclass(name = "Storage_Ref")]
pub struct Py_Storage_Ref {
    pub inner: RustRef<Py_Storage>,
}

#[pymethods]
impl Py_Storage {
    #[new]
    pub fn new(storage: Py<PyAny>) -> Self {
        Py_Storage { storage }
    }

    pub fn make_ref(&mut self) -> Py_Storage_Ref {
        Py_Storage_Ref {
            inner: RustRef::new_raw(self),
        }
    }

    fn __getattr__(this: PyObject, py: Python, attr: &str) -> PyResult<PyObject> {
        let reference = this.call_method0(py, intern!(py, "make_ref"))?;
        reference.getattr(py, attr)
    }
}

#[pymethods]
impl Py_Storage_Ref {
    pub fn wl(&mut self) -> PyResult<PyObject> {
        self.inner.map_as_mut(|inner| {
            Python::with_gil(|py| inner.storage.call_method(py, "wl", (), None))
        })?
    }

    pub fn rl(&self) -> PyResult<PyObject> {
        self.inner.map_as_ref(|inner| {
            Python::with_gil(|py| inner.storage.call_method(py, "rl", (), None))
        })?
    }
}

#[pymethods]
impl Py_Storage_Ref {
    pub fn append(&mut self, py: Python, ents: &PyList) -> PyResult<()> {
        self.inner
            .map_as_mut(|inner| inner.storage.call_method(py, "append", (ents,), None))
            .and(Ok(()))
    }

    pub fn apply_snapshot(&mut self, py: Python, snapshot: &PyAny) -> PyResult<()> {
        self.inner
            .map_as_mut(|inner| {
                inner
                    .storage
                    .call_method(py, "apply_snapshot", (snapshot,), None)
            })
            .and(Ok(()))
    }

    pub fn compact(&mut self, py: Python, compact_index: u64) -> PyResult<()> {
        self.inner
            .map_as_mut(|inner| {
                inner
                    .storage
                    .call_method(py, "compact", (compact_index,), None)
            })
            .and(Ok(()))
    }

    pub fn commit_to(&mut self, py: Python, index: u64) -> PyResult<()> {
        self.inner
            .map_as_mut(|inner| inner.storage.call_method(py, "commit_to", (index,), None))
            .and(Ok(()))
    }

    pub fn commit_to_and_set_conf_states(
        &mut self,
        py: Python,
        idx: u64,
        cs: Option<&PyAny>,
    ) -> PyResult<()> {
        self.inner
            .map_as_mut(|inner| {
                inner
                    .storage
                    .call_method(py, "commit_to_and_set_conf_states", (idx, cs), None)
            })
            .and(Ok(()))
    }

    pub fn hard_state(&mut self, py: Python) -> PyResult<Py_HardState> {
        self.inner.map_as_mut(|inner| {
            inner
                .storage
                .call_method(py, "hard_state", (), None)
                .and_then(|py_result| py_result.extract::<_>(py))
        })?
    }

    pub fn set_hardstate(&mut self, py: Python, hs: &PyAny) -> PyResult<()> {
        self.inner
            .map_as_mut(|inner| inner.storage.call_method(py, "set_hard_state", (hs,), None))
            .and(Ok(()))
    }

    pub fn set_conf_state(&mut self, py: Python, cs: &PyAny) -> PyResult<()> {
        self.inner
            .map_as_mut(|inner| inner.storage.call_method(py, "set_conf_state", (cs,), None))
            .and(Ok(()))
    }

    pub fn trigger_snap_unavailable(&mut self, py: Python) -> PyResult<()> {
        self.inner
            .map_as_mut(|inner| {
                inner
                    .storage
                    .call_method(py, "trigger_snap_unavailable", (), None)
            })
            .and(Ok(()))
    }
}

#[pymethods]
impl Py_Storage_Ref {
    pub fn initial_state(&self) -> PyResult<Py_RaftState_Ref> {
        Storage::initial_state(self)
            .map(|mut rs| Py_RaftState_Ref {
                inner: RustRef::new_raw(&mut rs),
            })
            .map_err(|e| Py_RaftError(e).into())
    }

    pub fn entries(
        &self,
        low: u64,
        high: u64,
        context: &mut Py_GetEntriesContext_Ref,
        max_size: Option<u64>,
        py: Python,
    ) -> PyResult<PyObject> {
        let context = context.inner.map_as_mut(|context| unsafe {
            std::ptr::replace(context, GetEntriesContext::empty(false))
        })?;

        Storage::entries(self, low, high, max_size, context)
            .map(|mut entries| {
                let py_entries = entries
                    .iter_mut()
                    .map(|x| Py_Entry_Ref {
                        inner: RustRef::new_raw(x),
                    })
                    .collect::<Vec<_>>();
                py_entries.into_py(py)
            })
            .map_err(|e| Py_RaftError(e).into())
    }

    pub fn term(&self, idx: u64) -> PyResult<u64> {
        Storage::term(self, idx).map_err(|e| Py_RaftError(e).into())
    }

    pub fn first_index(&self) -> PyResult<u64> {
        Storage::first_index(self).map_err(|e| Py_RaftError(e).into())
    }

    pub fn last_index(&self) -> PyResult<u64> {
        Storage::last_index(self).map_err(|e| Py_RaftError(e).into())
    }

    pub fn snapshot(&self, request_index: u64, to: u64) -> PyResult<Py_Snapshot_Ref> {
        Storage::snapshot(self, request_index, to)
            .map(|mut snapshot| Py_Snapshot_Ref {
                inner: RustRef::new_raw(&mut snapshot),
            })
            .map_err(|e| Py_RaftError(e).into())
    }
}

impl Storage for Py_Storage {
    fn initial_state(&self) -> raft::Result<raft::RaftState> {
        Python::with_gil(|py| {
            self.storage
                .as_ref(py)
                .call_method("initial_state", (), None)
                .and_then(|py_result| {
                    py_result
                        .extract::<_>()
                        .map(|rs: Py_RaftState_Mut| rs.into())
                })
                .map_err(|e| makeNativeRaftError(py, e))
        })
    }

    fn entries(
        &self,
        low: u64,
        high: u64,
        max_size: impl Into<Option<u64>>,
        context: GetEntriesContext,
    ) -> raft::Result<Vec<raft::prelude::Entry>> {
        let max_size: Option<u64> = max_size.into();
        let mut context = Py_GetEntriesContext { inner: RefMutOwner::new(context) };

        Python::with_gil(|py| {
            self.storage
                .as_ref(py)
                .call_method("entries", (low, high, context.make_ref(), max_size), None)
                .and_then(|entries| {
                    entries
                        .extract::<Vec<Py_Entry_Mut>>()
                        .map(|entries| entries.into_iter().map(|e| e.into()).collect())
                })
                .map_err(|e| makeNativeRaftError(py, e))
        })
    }

    fn term(&self, idx: u64) -> raft::Result<u64> {
        Python::with_gil(|py| {
            self.storage
                .as_ref(py)
                .call_method("term", (idx,), None)
                .and_then(|term| term.extract::<u64>())
                .map_err(|e| makeNativeRaftError(py, e))
        })
    }

    fn first_index(&self) -> raft::Result<u64> {
        Python::with_gil(|py| {
            self.storage
                .as_ref(py)
                .call_method("first_index", (), None)
                .and_then(|term| term.extract::<u64>())
                .map_err(|e| makeNativeRaftError(py, e))
        })
    }

    fn last_index(&self) -> raft::Result<u64> {
        Python::with_gil(|py| {
            self.storage
                .as_ref(py)
                .call_method("last_index", (), None)
                .and_then(|term| term.extract::<u64>())
                .map_err(|e| makeNativeRaftError(py, e))
        })
    }

    fn snapshot(&self, request_index: u64, to: u64) -> raft::Result<raft::prelude::Snapshot> {
        Python::with_gil(|py| {
            self.storage
                .as_ref(py)
                .call_method("snapshot", (request_index, to), None)
                .and_then(|py_result| {
                    py_result
                        .extract::<_>()
                        .map(|ss: Py_Snapshot_Mut| ss.into())
                })
                .map_err(|e| makeNativeRaftError(py, e))
        })
    }
}

impl Storage for Py_Storage_Ref {
    fn initial_state(&self) -> raft::Result<raft::RaftState> {
        unsafe { make_mut(&self.inner) }
            .map_as_mut(|inner| {
                Python::with_gil(|py| {
                    inner
                        .storage
                        .call_method(py, "initial_state", (), None)
                        .and_then(|py_result| {
                            py_result
                                .extract::<_>(py)
                                .map(|rs: Py_RaftState_Mut| rs.into())
                        })
                        .map_err(|e| makeNativeRaftError(py, e))
                })
            })
            .expect(DESTROYED_ERR_MSG)
    }

    fn entries(
        &self,
        low: u64,
        high: u64,
        max_size: impl Into<Option<u64>>,
        context: GetEntriesContext,
    ) -> raft::Result<Vec<raft::prelude::Entry>> {
        let max_size: Option<u64> = max_size.into();
        let mut context = Py_GetEntriesContext { inner: RefMutOwner::new(context) };

        unsafe { make_mut(&self.inner) }
            .map_as_mut(|inner| {
                Python::with_gil(|py| {
                    inner
                        .storage
                        .as_ref(py)
                        .call_method("entries", (low, high, context.make_ref(), max_size), None)
                        .and_then(|entries| {
                            entries
                                .extract::<Vec<Py_Entry_Mut>>()
                                .map(|entries| entries.into_iter().map(|e| e.into()).collect())
                        })
                        .map_err(|e| makeNativeRaftError(py, e))
                })
            })
            .expect(DESTROYED_ERR_MSG)
    }

    fn term(&self, idx: u64) -> raft::Result<u64> {
        unsafe { make_mut(&self.inner) }
            .map_as_mut(|inner| {
                Python::with_gil(|py| {
                    inner
                        .storage
                        .as_ref(py)
                        .call_method("term", (idx,), None)
                        .and_then(|term| term.extract::<u64>())
                        .map_err(|e| makeNativeRaftError(py, e))
                })
            })
            .expect(DESTROYED_ERR_MSG)
    }

    fn first_index(&self) -> raft::Result<u64> {
        unsafe { make_mut(&self.inner) }
            .map_as_mut(|inner| {
                Python::with_gil(|py| {
                    inner
                        .storage
                        .as_ref(py)
                        .call_method("first_index", (), None)
                        .and_then(|term| term.extract::<u64>())
                        .map_err(|e| makeNativeRaftError(py, e))
                })
            })
            .expect(DESTROYED_ERR_MSG)
    }

    fn last_index(&self) -> raft::Result<u64> {
        unsafe { make_mut(&self.inner) }
            .map_as_mut(|inner| {
                Python::with_gil(|py| {
                    inner
                        .storage
                        .as_ref(py)
                        .call_method("last_index", (), None)
                        .and_then(|term| term.extract::<u64>())
                        .map_err(|e| makeNativeRaftError(py, e))
                })
            })
            .expect(DESTROYED_ERR_MSG)
    }

    fn snapshot(&self, request_index: u64, to: u64) -> raft::Result<raft::prelude::Snapshot> {
        unsafe { make_mut(&self.inner) }
            .map_as_mut(|inner| {
                Python::with_gil(|py| {
                    inner
                        .storage
                        .call_method(py, "snapshot", (request_index, to), None)
                        .and_then(|py_result| {
                            py_result
                                .extract::<_>(py)
                                .map(|ss: Py_Snapshot_Mut| ss.into())
                        })
                        .map_err(|e| makeNativeRaftError(py, e))
                })
            })
            .expect(DESTROYED_ERR_MSG)
    }
}
