use bindings::get_entries_context::{Py_GetEntriesContext, Py_GetEntriesContext_Ref};
use pyo3::types::PyList;
use pyo3::{intern, prelude::*};

use raft::storage::Storage;
use raft::GetEntriesContext;
use raftpb_bindings::hard_state::Py_HardState;
use utils::errors::to_pyresult;

use raftpb_bindings::entry::Py_Entry_Ref;
use raftpb_bindings::snapshot::{Py_Snapshot, Py_Snapshot_Ref};
use utils::reference::RustRef;

use bindings::raft_state::{Py_RaftState_Mut, Py_RaftState_Ref};
use raftpb_bindings::entry::Py_Entry_Mut;

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

    fn __getattr__(this: PyObject, py: Python<'_>, attr: &str) -> PyResult<PyObject> {
        let reference = this.call_method0(py, intern!(py, "make_ref"))?;
        reference.getattr(py, attr)
    }
}

#[pymethods]
impl Py_Storage_Ref {
    pub fn wl(&mut self) -> PyResult<PyObject> {
        self.inner.map_as_mut(|inner| {
            Python::with_gil(|py| {
                let py_result = inner
                    .storage
                    .as_ref(py)
                    .call_method("wl", (), None)
                    .unwrap();

                let res: PyObject = py_result.extract().unwrap();
                res
            })
        })
    }

    pub fn rl(&self) -> PyResult<PyObject> {
        self.inner.map_as_ref(|inner| {
            Python::with_gil(|py| {
                let py_result = inner
                    .storage
                    .as_ref(py)
                    .call_method("rl", (), None)
                    .unwrap();

                let res: PyObject = py_result.extract().unwrap();
                res
            })
        })
    }
}

#[pymethods]
impl Py_Storage_Ref {
    pub fn append(&mut self, ents: &PyList) -> PyResult<()> {
        self.inner.map_as_mut(|inner| {
            Python::with_gil(|py| {
                inner
                    .storage
                    .as_ref(py)
                    .call_method("append", (ents,), None)
                    .unwrap();
            })
        })
    }

    pub fn apply_snapshot(&mut self, snapshot: &PyAny) -> PyResult<()> {
        self.inner.map_as_mut(|inner| {
            Python::with_gil(|py| {
                inner
                    .storage
                    .as_ref(py)
                    .call_method("apply_snapshot", (snapshot,), None)
                    .unwrap();
            })
        })
    }

    pub fn compact(&mut self, compact_index: u64) -> PyResult<()> {
        self.inner.map_as_mut(|inner| {
            Python::with_gil(|py| {
                inner
                    .storage
                    .as_ref(py)
                    .call_method("compact", (compact_index,), None)
                    .unwrap();
            })
        })
    }

    pub fn commit_to(&mut self, index: u64) -> PyResult<()> {
        self.inner.map_as_mut(|inner| {
            Python::with_gil(|py| {
                inner
                    .storage
                    .as_ref(py)
                    .call_method("commit_to", (index,), None)
                    .unwrap();
            })
        })
    }

    pub fn commit_to_and_set_conf_states(&mut self, idx: u64, cs: Option<&PyAny>) -> PyResult<()> {
        self.inner.map_as_mut(|inner| {
            Python::with_gil(|py| {
                inner
                    .storage
                    .as_ref(py)
                    .call_method("commit_to_and_set_conf_states", (idx, cs), None)
                    .unwrap();
            })
        })
    }

    pub fn hard_state(&mut self) -> PyResult<Py_HardState> {
        self.inner.map_as_mut(|inner| {
            Python::with_gil(|py| {
                let py_result = inner
                    .storage
                    .as_ref(py)
                    .call_method("hard_state", (), None)
                    .unwrap();

                let hs: Py_HardState = py_result.extract().unwrap();
                hs
            })
        })
    }

    pub fn set_hardstate(&mut self, hs: &PyAny) -> PyResult<()> {
        self.inner.map_as_mut(|inner| {
            Python::with_gil(|py| {
                inner
                    .storage
                    .as_ref(py)
                    .call_method("set_hard_state", (hs,), None)
                    .unwrap();
            })
        })
    }

    pub fn set_conf_state(&mut self, cs: &PyAny) -> PyResult<()> {
        self.inner.map_as_mut(|inner| {
            Python::with_gil(|py| {
                inner
                    .storage
                    .as_ref(py)
                    .call_method("set_conf_state", (cs,), None)
                    .unwrap();
            })
        })
    }

    pub fn trigger_snap_unavailable(&mut self) -> PyResult<()> {
        self.inner.map_as_mut(|inner| {
            Python::with_gil(|py| {
                inner
                    .storage
                    .as_ref(py)
                    .call_method("trigger_snap_unavailable", (), None)
                    .unwrap();
            })
        })
    }
}

#[pymethods]
impl Py_Storage_Ref {
    pub fn initial_state(&self) -> PyResult<Py_RaftState_Ref> {
        to_pyresult(Storage::initial_state(self).map(|mut rs| Py_RaftState_Ref {
            inner: RustRef::new(&mut rs),
        }))
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
        to_pyresult(Storage::term(self, idx))
    }

    pub fn first_index(&self) -> PyResult<u64> {
        to_pyresult(Storage::first_index(self))
    }

    pub fn last_index(&self) -> PyResult<u64> {
        to_pyresult(Storage::last_index(self))
    }

    pub fn snapshot(&self, request_index: u64, to: u64) -> PyResult<Py_Snapshot_Ref> {
        to_pyresult(
            Storage::snapshot(self, request_index, to).map(|mut snapshot| Py_Snapshot_Ref {
                inner: RustRef::new(&mut snapshot),
            }),
        )
    }
}

impl Storage for Py_Storage {
    fn initial_state(&self) -> raft::Result<raft::RaftState> {
        Python::with_gil(|py| {
            match self.storage.as_ref(py).call_method("initial_state", (), None) {
                Ok(py_result) => {
                    match py_result.extract::<Py_RaftState_Mut>() {
                        Ok(rs) => {
                            let rs: raft::RaftState = rs.into();
                            Ok(rs)
                        },
                        Err(e) => Err(raft::Error::Store(raft::StorageError::Other(Box::new(e)))),
                    }
                },
                Err(e) => {
                    Err(raft::Error::Store(raft::StorageError::Other(Box::new(e))))
                }
            }
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
            let py_result: &PyAny = self
                .storage
                .as_ref(py)
                .call_method("entries", (low, high, context.make_ref(), max_size), None)
                .unwrap();

            let mut entries: Vec<Py_Entry_Mut> = py_result.extract().unwrap();
            let entries = entries.iter_mut().map(|x| x.into()).collect::<Vec<_>>();
            Ok(entries)
        })
    }

    fn term(&self, idx: u64) -> raft::Result<u64> {
        Python::with_gil(|py| {
            let py_result: &PyAny = self
                .storage
                .as_ref(py)
                .call_method("term", (idx,), None)
                .unwrap();

            let res: u64 = py_result.extract().unwrap();
            Ok(res)
        })
    }

    fn first_index(&self) -> raft::Result<u64> {
        Python::with_gil(|py| {
            let py_result: &PyAny = self
                .storage
                .as_ref(py)
                .call_method("first_index", (), None)
                .unwrap();

            let res: u64 = py_result.extract().unwrap();
            Ok(res)
        })
    }

    fn last_index(&self) -> raft::Result<u64> {
        Python::with_gil(|py| {
            let py_result: &PyAny = self
                .storage
                .as_ref(py)
                .call_method("last_index", (), None)
                .unwrap();

            let res: u64 = py_result.extract().unwrap();
            Ok(res)
        })
    }

    fn snapshot(&self, request_index: u64, to: u64) -> raft::Result<raft::prelude::Snapshot> {
        Python::with_gil(|py| {
            let py_result: &PyAny = self
                .storage
                .as_ref(py)
                .call_method("snapshot", (request_index, to), None)
                .unwrap();

            let res: PyResult<Py_Snapshot> = py_result.extract();
            Ok(res.unwrap().inner)
        })
    }
}

impl Storage for Py_Storage_Ref {
    fn initial_state(&self) -> raft::Result<raft::RaftState> {
        Python::with_gil(|py| {
            self.inner
                .map_as_ref(|inner| {
                    let py_result = inner
                        .storage
                        .as_ref(py)
                        .call_method("initial_state", (), None)
                        .unwrap();

                    let raft_state: Py_RaftState_Mut = py_result.extract().unwrap();
                    Ok(raft_state.into())
                })
                .unwrap()
        })
    }

    fn entries(
        &self,
        low: u64,
        high: u64,
        max_size: impl Into<Option<u64>>,
        context: GetEntriesContext,
    ) -> raft::Result<Vec<raft::prelude::Entry>> {
        let mut context = Py_GetEntriesContext { inner: context };
        let max_size: Option<u64> = max_size.into();

        Python::with_gil(|py| {
            self.inner
                .map_as_ref(|inner| {
                    let py_result: &PyAny = inner
                        .storage
                        .as_ref(py)
                        .call_method("entries", (low, high, context.make_ref(), max_size), None)
                        .unwrap();

                    let mut entries: Vec<Py_Entry_Mut> = py_result.extract().unwrap();
                    let entries = entries.iter_mut().map(|x| x.into()).collect::<Vec<_>>();
                    Ok(entries)
                })
                .unwrap()
        })
    }

    fn term(&self, idx: u64) -> raft::Result<u64> {
        Python::with_gil(|py| {
            self.inner.map_as_ref(|inner| {
                let py_result: &PyAny = inner
                    .storage
                    .as_ref(py)
                    .call_method("term", (idx,), None)
                    .unwrap();

                let res: u64 = py_result.extract().unwrap();
                Ok(res)
            })
        })
        .unwrap()
    }

    fn first_index(&self) -> raft::Result<u64> {
        Python::with_gil(|py| {
            self.inner.map_as_ref(|inner| {
                let py_result: &PyAny = inner
                    .storage
                    .as_ref(py)
                    .call_method("first_index", (), None)
                    .unwrap();

                let res: u64 = py_result.extract().unwrap();
                Ok(res)
            })
        })
        .unwrap()
    }

    fn last_index(&self) -> raft::Result<u64> {
        Python::with_gil(|py| {
            self.inner.map_as_ref(|inner| {
                let py_result: &PyAny = inner
                    .storage
                    .as_ref(py)
                    .call_method("last_index", (), None)
                    .unwrap();

                let res: u64 = py_result.extract().unwrap();
                Ok(res)
            })
        })
        .unwrap()
    }

    fn snapshot(&self, request_index: u64, to: u64) -> raft::Result<raft::prelude::Snapshot> {
        Python::with_gil(|py| {
            self.inner.map_as_ref(|inner| {
                let py_result: &PyAny = inner
                    .storage
                    .as_ref(py)
                    .call_method("snapshot", (request_index, to), None)
                    .unwrap();

                let res: PyResult<Py_Snapshot> = py_result.extract();
                Ok(res.unwrap().inner)
            })
        })
        .unwrap()
    }
}
