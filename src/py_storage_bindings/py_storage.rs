use bindings::error::{makeNativeRaftError, Py_RaftError};
use bindings::get_entries_context::{Py_GetEntriesContext, Py_GetEntriesContext_Ref};
use pyo3::types::PyList;
use pyo3::{intern, prelude::*};

use raft::storage::Storage;
use raft::GetEntriesContext;
use raftpb_bindings::hard_state::Py_HardState;
use utils::errors::to_pyresult;

use raftpb_bindings::entry::Py_Entry_Ref;
use raftpb_bindings::snapshot::{Py_Snapshot_Mut, Py_Snapshot_Ref};
use utils::reference::RustRef;

use bindings::raft_state::{Py_RaftState_Mut, Py_RaftState_Ref};
use raftpb_bindings::entry::Py_Entry_Mut;
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
            inner: RustRef::new(self),
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
        self.inner
            .map_as_mut(|inner| {
                Python::with_gil(|py| inner.storage.call_method(py, "wl", (), None))
            })
            .and_then(|x| match x {
                Ok(x) => Ok(x),
                Err(e) => Err(e),
            })
    }

    pub fn rl(&self) -> PyResult<PyObject> {
        self.inner
            .map_as_ref(|inner| {
                Python::with_gil(|py| inner.storage.call_method(py, "rl", (), None))
            })
            .and_then(|x| match x {
                Ok(x) => Ok(x),
                Err(e) => Err(e),
            })
    }
}

#[pymethods]
impl Py_Storage_Ref {
    pub fn append(&mut self, py: Python, ents: &PyList) -> PyResult<()> {
        self.inner
            .map_as_mut(|inner| inner.storage.call_method(py, "append", (ents,), None))
            .and_then(|x| match x {
                Ok(_) => Ok(()),
                Err(e) => Err(e),
            })?;

        Ok(())
    }

    pub fn apply_snapshot(&mut self, py: Python, snapshot: &PyAny) -> PyResult<()> {
        self.inner
            .map_as_mut(|inner| {
                inner
                    .storage
                    .call_method(py, "apply_snapshot", (snapshot,), None)
            })
            .and_then(|x| match x {
                Ok(_) => Ok(()),
                Err(e) => Err(e),
            })?;

        Ok(())
    }

    pub fn compact(&mut self, py: Python, compact_index: u64) -> PyResult<()> {
        self.inner
            .map_as_mut(|inner| {
                inner
                    .storage
                    .call_method(py, "compact", (compact_index,), None)
            })
            .and_then(|x| match x {
                Ok(_) => Ok(()),
                Err(e) => Err(e),
            })?;

        Ok(())
    }

    pub fn commit_to(&mut self, py: Python, index: u64) -> PyResult<()> {
        self.inner
            .map_as_mut(|inner| inner.storage.call_method(py, "commit_to", (index,), None))
            .and_then(|x| match x {
                Ok(_) => Ok(()),
                Err(e) => Err(e),
            })?;

        Ok(())
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
            .and_then(|x| match x {
                Ok(_) => Ok(()),
                Err(e) => Err(e),
            })?;

        Ok(())
    }

    pub fn hard_state(&mut self, py: Python) -> PyResult<Py_HardState> {
        self.inner
            .map_as_mut(|inner| {
                inner
                    .storage
                    .call_method(py, "hard_state", (), None)
                    .and_then(|py_result| py_result.extract::<_>(py))
            })
            .and_then(|x| match x {
                Ok(hs) => Ok(hs),
                Err(e) => Err(e),
            })
    }

    pub fn set_hardstate(&mut self, py: Python, hs: &PyAny) -> PyResult<()> {
        self.inner
            .map_as_mut(|inner| inner.storage.call_method(py, "set_hard_state", (hs,), None))
            .and_then(|x| match x {
                Ok(_) => Ok(()),
                Err(e) => Err(e),
            })?;

        Ok(())
    }

    pub fn set_conf_state(&mut self, py: Python, cs: &PyAny) -> PyResult<()> {
        self.inner
            .map_as_mut(|inner| inner.storage.call_method(py, "set_conf_state", (cs,), None))
            .and_then(|x| match x {
                Ok(_) => Ok(()),
                Err(e) => Err(e),
            })?;

        Ok(())
    }

    pub fn trigger_snap_unavailable(&mut self, py: Python) -> PyResult<()> {
        self.inner
            .map_as_mut(|inner| {
                inner
                    .storage
                    .call_method(py, "trigger_snap_unavailable", (), None)
            })
            .and_then(|x| match x {
                Ok(_) => Ok(()),
                Err(e) => Err(e),
            })?;

        Ok(())
    }
}

#[pymethods]
impl Py_Storage_Ref {
    pub fn initial_state(&self) -> PyResult<Py_RaftState_Ref> {
        Storage::initial_state(self)
            .map(|mut rs| Py_RaftState_Ref {
                inner: RustRef::new(&mut rs),
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

        to_pyresult(
            Storage::entries(self, low, high, max_size, context).map(|mut entries| {
                let py_entries = entries
                    .iter_mut()
                    .map(|x| Py_Entry_Ref {
                        inner: RustRef::new(x),
                    })
                    .collect::<Vec<_>>();
                py_entries.into_py(py)
            }),
        )
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
                inner: RustRef::new(&mut snapshot),
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
                        .and_then(|rs: Py_RaftState_Mut| Ok(rs.into()))
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
        let mut context = Py_GetEntriesContext { inner: context };

        Python::with_gil(|py| {
            self.storage
                .as_ref(py)
                .call_method("entries", (low, high, context.make_ref(), max_size), None)
                .and_then(|entries| {
                    entries
                        .extract::<Vec<Py_Entry_Mut>>()
                        .and_then(|entries| Ok(entries.into_iter().map(|e| e.into()).collect()))
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
                        .and_then(|ss: Py_Snapshot_Mut| Ok(ss.into()))
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
                                .and_then(|rs: Py_RaftState_Mut| Ok(rs.into()))
                        })
                        .map_err(|e| makeNativeRaftError(py, e))
                })
            })
            .unwrap()
    }

    fn entries(
        &self,
        low: u64,
        high: u64,
        max_size: impl Into<Option<u64>>,
        context: GetEntriesContext,
    ) -> raft::Result<Vec<raft::prelude::Entry>> {
        let max_size: Option<u64> = max_size.into();
        let mut context = Py_GetEntriesContext { inner: context };

        unsafe { make_mut(&self.inner) }
            .map_as_mut(|inner| {
                Python::with_gil(|py| {
                    inner
                        .storage
                        .as_ref(py)
                        .call_method("entries", (low, high, context.make_ref(), max_size), None)
                        .and_then(|entries| {
                            entries.extract::<Vec<Py_Entry_Mut>>().and_then(|entries| {
                                Ok(entries.into_iter().map(|e| e.into()).collect())
                            })
                        })
                        .map_err(|e| makeNativeRaftError(py, e))
                })
            })
            .unwrap()
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
            .unwrap()
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
            .unwrap()
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
            .unwrap()
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
                                .and_then(|ss: Py_Snapshot_Mut| Ok(ss.into()))
                        })
                        .map_err(|e| makeNativeRaftError(py, e))
                })
            })
            .unwrap()
    }
}
