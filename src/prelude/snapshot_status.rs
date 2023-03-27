use pyo3::{prelude::*, pyclass::CompareOp};

use raft::SnapshotStatus;

#[derive(Clone)]
#[pyclass(name = "SnapshotStatus")]
pub struct Py_SnapshotStatus(pub SnapshotStatus);

impl From<Py_SnapshotStatus> for SnapshotStatus {
    fn from(val: Py_SnapshotStatus) -> Self {
        match val.0 {
            SnapshotStatus::Finish => SnapshotStatus::Finish,
            SnapshotStatus::Failure => SnapshotStatus::Failure,
        }
    }
}

impl From<SnapshotStatus> for Py_SnapshotStatus {
    fn from(x: SnapshotStatus) -> Self {
        match x {
            SnapshotStatus::Finish => Py_SnapshotStatus(SnapshotStatus::Finish),
            SnapshotStatus::Failure => Py_SnapshotStatus(SnapshotStatus::Failure),
        }
    }
}

#[pymethods]
impl Py_SnapshotStatus {
    pub fn __richcmp__(&self, rhs: &Py_SnapshotStatus, op: CompareOp) -> PyResult<bool> {
        Ok(match op {
            CompareOp::Eq => self.0 == rhs.0,
            CompareOp::Ne => self.0 != rhs.0,
            _ => panic!("Undefined operator"),
        })
    }

    pub fn __hash__(&self) -> u64 {
        self.0 as u64
    }

    pub fn __repr__(&self) -> String {
        match self.0 {
            SnapshotStatus::Finish => "Finish".to_string(),
            SnapshotStatus::Failure => "Failure".to_string(),
        }
    }

    #[classattr]
    pub fn Finish() -> Self {
        Py_SnapshotStatus(SnapshotStatus::Finish)
    }

    #[classattr]
    pub fn Failure() -> Self {
        Py_SnapshotStatus(SnapshotStatus::Failure)
    }
}
