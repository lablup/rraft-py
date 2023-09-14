use crate::bindings::get_entries_context::{PyGetEntriesContext, PyGetEntriesContextRef};
use pyo3::types::PyList;
use pyo3::{intern, prelude::*};

use crate::raftpb_bindings::hard_state::PyHardState;
use raft::storage::Storage;
use raft::GetEntriesContext;

use crate::raftpb_bindings::entry::PyEntryRef;
use crate::raftpb_bindings::snapshot::{PySnapshotMut, PySnapshotRef};

use crate::bindings::raft_state::{PyRaftStateMut, PyRaftStateRef};
use crate::raftpb_bindings::entry::PyEntryMut;
use crate::utils::errors::{make_native_raft_error, PyRaftError, DESTROYED_ERR_MSG};
use crate::utils::reference::{RefMutContainer, RefMutOwner};
use crate::utils::unsafe_cast::make_mut;

#[derive(Clone)]
#[pyclass(name = "Storage")]
pub struct PyStorage {
    pub storage: Py<PyAny>,
}

#[derive(Clone)]
#[pyclass(name = "StorageRef")]
pub struct PyStorageRef {
    pub inner: RefMutContainer<PyStorage>,
}

#[pymethods]
impl PyStorage {
    #[new]
    pub fn new(storage: Py<PyAny>) -> Self {
        PyStorage { storage }
    }

    // !TODO: Implement below method.
    // #[staticmethod]
    // pub fn new_with_conf_state(cs: PyConfStateMut) -> Self {

    // }

    pub fn make_ref(&mut self) -> PyStorageRef {
        PyStorageRef {
            inner: RefMutContainer::new_raw(self),
        }
    }

    fn __getattr__(this: PyObject, py: Python, attr: &str) -> PyResult<PyObject> {
        let reference = this.call_method0(py, intern!(py, "make_ref"))?;
        reference.getattr(py, attr)
    }
}

#[pymethods]
impl PyStorageRef {
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
impl PyStorageRef {
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

    pub fn hard_state(&mut self, py: Python) -> PyResult<PyHardState> {
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
impl PyStorageRef {
    pub fn initial_state(&self) -> PyResult<PyRaftStateRef> {
        Storage::initial_state(self)
            .map(|mut rs| PyRaftStateRef {
                inner: RefMutContainer::new_raw(&mut rs),
            })
            .map_err(|e| PyRaftError(e).into())
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

        Storage::entries(self, low, high, max_size, context)
            .map(|mut entries| {
                let py_entries = entries
                    .iter_mut()
                    .map(|x| PyEntryRef {
                        inner: RefMutContainer::new_raw(x),
                    })
                    .collect::<Vec<_>>();
                py_entries.into_py(py)
            })
            .map_err(|e| PyRaftError(e).into())
    }

    pub fn term(&self, idx: u64) -> PyResult<u64> {
        Storage::term(self, idx).map_err(|e| PyRaftError(e).into())
    }

    pub fn first_index(&self) -> PyResult<u64> {
        Storage::first_index(self).map_err(|e| PyRaftError(e).into())
    }

    pub fn last_index(&self) -> PyResult<u64> {
        Storage::last_index(self).map_err(|e| PyRaftError(e).into())
    }

    pub fn snapshot(&self, request_index: u64, to: u64) -> PyResult<PySnapshotRef> {
        Storage::snapshot(self, request_index, to)
            .map(|mut snapshot| PySnapshotRef {
                inner: RefMutContainer::new_raw(&mut snapshot),
            })
            .map_err(|e| PyRaftError(e).into())
    }
}

impl Storage for PyStorage {
    fn initial_state(&self) -> raft::Result<raft::RaftState> {
        Python::with_gil(|py| {
            self.storage
                .as_ref(py)
                .call_method("initial_state", (), None)
                .and_then(|py_result| py_result.extract::<_>().map(|rs: PyRaftStateMut| rs.into()))
                .map_err(|e| make_native_raft_error(py, e))
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
        let mut context = PyGetEntriesContext {
            inner: RefMutOwner::new(context),
        };

        Python::with_gil(|py| {
            self.storage
                .as_ref(py)
                .call_method("entries", (low, high, context.make_ref(), max_size), None)
                .and_then(|entries| {
                    entries
                        .extract::<Vec<PyEntryMut>>()
                        .map(|entries| entries.into_iter().map(|e| e.into()).collect())
                })
                .map_err(|e| make_native_raft_error(py, e))
        })
    }

    fn term(&self, idx: u64) -> raft::Result<u64> {
        Python::with_gil(|py| {
            self.storage
                .as_ref(py)
                .call_method("term", (idx,), None)
                .and_then(|term| term.extract::<u64>())
                .map_err(|e| make_native_raft_error(py, e))
        })
    }

    fn first_index(&self) -> raft::Result<u64> {
        Python::with_gil(|py| {
            self.storage
                .as_ref(py)
                .call_method("first_index", (), None)
                .and_then(|term| term.extract::<u64>())
                .map_err(|e| make_native_raft_error(py, e))
        })
    }

    fn last_index(&self) -> raft::Result<u64> {
        Python::with_gil(|py| {
            self.storage
                .as_ref(py)
                .call_method("last_index", (), None)
                .and_then(|term| term.extract::<u64>())
                .map_err(|e| make_native_raft_error(py, e))
        })
    }

    fn snapshot(&self, request_index: u64, to: u64) -> raft::Result<raft::prelude::Snapshot> {
        Python::with_gil(|py| {
            self.storage
                .as_ref(py)
                .call_method("snapshot", (request_index, to), None)
                .and_then(|py_result| py_result.extract::<_>().map(|ss: PySnapshotMut| ss.into()))
                .map_err(|e| make_native_raft_error(py, e))
        })
    }
}

impl Storage for PyStorageRef {
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
                                .map(|rs: PyRaftStateMut| rs.into())
                        })
                        .map_err(|e| make_native_raft_error(py, e))
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
        let mut context = PyGetEntriesContext {
            inner: RefMutOwner::new(context),
        };

        unsafe { make_mut(&self.inner) }
            .map_as_mut(|inner| {
                Python::with_gil(|py| {
                    inner
                        .storage
                        .as_ref(py)
                        .call_method("entries", (low, high, context.make_ref(), max_size), None)
                        .and_then(|entries| {
                            entries
                                .extract::<Vec<PyEntryMut>>()
                                .map(|entries| entries.into_iter().map(|e| e.into()).collect())
                        })
                        .map_err(|e| make_native_raft_error(py, e))
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
                        .map_err(|e| make_native_raft_error(py, e))
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
                        .map_err(|e| make_native_raft_error(py, e))
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
                        .map_err(|e| make_native_raft_error(py, e))
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
                                .map(|ss: PySnapshotMut| ss.into())
                        })
                        .map_err(|e| make_native_raft_error(py, e))
                })
            })
            .expect(DESTROYED_ERR_MSG)
    }
}
