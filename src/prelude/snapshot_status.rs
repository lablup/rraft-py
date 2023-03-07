use pyo3::{prelude::*, pyclass::CompareOp};

use raft::SnapshotStatus;

#[derive(Clone)]
#[pyclass(name = "SnapshotStatus")]
pub struct Py_SnapshotStatus(pub SnapshotStatus);

impl Into<SnapshotStatus> for Py_SnapshotStatus {
    fn into(self) -> SnapshotStatus {
        match self.0 {
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

    #[classattr]
    pub fn Finish() -> Self {
        Py_SnapshotStatus(SnapshotStatus::Finish)
    }

    #[classattr]
    pub fn Failure() -> Self {
        Py_SnapshotStatus(SnapshotStatus::Failure)
    }
}
