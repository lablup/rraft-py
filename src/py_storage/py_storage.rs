// Ref: https://pyo3.rs/main/trait_bounds
use pyo3::prelude::*;

use raft::storage::Storage;
use utils::errors::to_pyresult;

use eraftpb::entry::Py_Entry_Ref;
use eraftpb::snapshot::{Py_Snapshot_Owner, Py_Snapshot_Ref};
use utils::reference::RustRef;

use bindings::raft_state::{Py_RaftState_Mut, Py_RaftState_Ref};
use eraftpb::entry::Py_Entry_Mut;

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
        to_pyresult(Storage::initial_state(self).map(|mut rs| Py_RaftState_Ref {
            inner: RustRef::new(&mut rs),
        }))
    }

    pub fn entries(
        &self,
        low: u64,
        high: u64,
        max_size: Option<u64>,
        py: Python,
    ) -> PyResult<PyObject> {
        to_pyresult(
            Storage::entries(self, low, high, max_size).map(|mut entries| {
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

    pub fn snapshot(&self, request_index: u64) -> PyResult<Py_Snapshot_Ref> {
        to_pyresult(
            Storage::snapshot(self, request_index).map(|mut snapshot| Py_Snapshot_Ref {
                inner: RustRef::new(&mut snapshot),
            }),
        )
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
