// Ref: https://pyo3.rs/main/trait_bounds
use pyo3::{exceptions::PyRuntimeError, prelude::*};

use raft::storage::Storage;

use crate::eraftpb::entry::Py_Entry_Ref;
use crate::eraftpb::snapshot::{Py_Snapshot_Owner, Py_Snapshot_Ref};
use utils::reference::{RustRef, RustRef_Default_Implementation};

use super::super::eraftpb::entry::Py_Entry_Mut;
use super::raft_state::{Py_RaftState_Mut, Py_RaftState_Ref};

#[pyclass(name = "Storage")]
pub struct Py_Storage {
    pub storage: Py<PyAny>,
}

#[pymethods]
impl Py_Storage {
    #[new]
    pub fn new(storage: Py<PyAny>) -> Self {
        Py_Storage { storage }
    }

    pub fn initial_state(&self) -> PyResult<Py_RaftState_Ref> {
        match Storage::initial_state(self) {
            Ok(mut rs) => Ok(Py_RaftState_Ref {
                inner: RustRef::new(&mut rs),
            }),
            Err(err) => Err(PyRuntimeError::new_err(err.to_string())),
        }
    }

    pub fn entries(
        &self,
        low: u64,
        high: u64,
        max_size: Option<u64>,
        py: Python,
    ) -> PyResult<PyObject> {
        match Storage::entries(self, low, high, max_size) {
            Ok(mut entries) => {
                let py_entries = entries
                    .iter_mut()
                    .map(|x| Py_Entry_Ref {
                        inner: RustRef::new(x),
                    })
                    .collect::<Vec<_>>();
                Ok(py_entries.into_py(py))
            }
            Err(err) => Err(PyRuntimeError::new_err(err.to_string())),
        }
    }

    pub fn term(&self, idx: u64) -> PyResult<u64> {
        match Storage::term(self, idx) {
            Ok(term) => Ok(term),
            Err(err) => Err(PyRuntimeError::new_err(err.to_string())),
        }
    }

    pub fn first_index(&self) -> PyResult<u64> {
        match Storage::first_index(self) {
            Ok(idx) => Ok(idx),
            Err(err) => Err(PyRuntimeError::new_err(err.to_string())),
        }
    }

    pub fn last_index(&self) -> PyResult<u64> {
        match Storage::last_index(self) {
            Ok(idx) => Ok(idx),
            Err(err) => Err(PyRuntimeError::new_err(err.to_string())),
        }
    }

    pub fn snapshot(&self, request_index: u64) -> PyResult<Py_Snapshot_Ref> {
        match Storage::snapshot(self, request_index) {
            Ok(mut snapshot) => Ok(Py_Snapshot_Ref {
                inner: RustRef::new(&mut snapshot),
            }),
            Err(err) => Err(PyRuntimeError::new_err(err.to_string())),
        }
    }
}

impl Storage for Py_Storage {
    fn initial_state(&self) -> raft::Result<raft::RaftState> {
        Python::with_gil(|py| {
            let py_result: &PyAny = self
                .storage
                .as_ref(py)
                .call_method("initial_state", (), None)
                .unwrap();

            let raft_state: Py_RaftState_Mut = py_result.extract().unwrap();
            Ok(raft_state.into())
        })
    }

    fn entries(
        &self,
        low: u64,
        high: u64,
        max_size: impl Into<Option<u64>>,
    ) -> raft::Result<Vec<raft::prelude::Entry>> {
        let max_size: Option<u64> = max_size.into();

        Python::with_gil(|py| {
            let py_result: &PyAny = self
                .storage
                .as_ref(py)
                .call_method("entries", (low, high, max_size), None)
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

    fn snapshot(&self, request_index: u64) -> raft::Result<raft::prelude::Snapshot> {
        Python::with_gil(|py| {
            let py_result: &PyAny = self
                .storage
                .as_ref(py)
                .call_method("snapshot", (request_index,), None)
                .unwrap();

            let res: PyResult<Py_Snapshot_Owner> = py_result.extract();
            Ok(res.unwrap().inner)
        })
    }
}
