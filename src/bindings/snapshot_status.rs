use pyo3::{prelude::*, pyclass::CompareOp};

use raft::SnapshotStatus;

#[derive(Clone)]
#[pyclass(name = "SnapshotStatus")]
pub struct PySnapshotStatus(pub SnapshotStatus);

impl From<PySnapshotStatus> for SnapshotStatus {
    fn from(val: PySnapshotStatus) -> Self {
        val.0
    }
}

impl From<SnapshotStatus> for PySnapshotStatus {
    fn from(x: SnapshotStatus) -> Self {
        match x {
            SnapshotStatus::Finish => PySnapshotStatus(SnapshotStatus::Finish),
            SnapshotStatus::Failure => PySnapshotStatus(SnapshotStatus::Failure),
        }
    }
}

#[pymethods]
impl PySnapshotStatus {
    pub fn __richcmp__(&self, py: Python, rhs: &PySnapshotStatus, op: CompareOp) -> PyObject {
        match op {
            CompareOp::Eq => (self.0 == rhs.0).into_py(py),
            CompareOp::Ne => (self.0 != rhs.0).into_py(py),
            _ => py.NotImplemented(),
        }
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
        PySnapshotStatus(SnapshotStatus::Finish)
    }

    #[classattr]
    pub fn Failure() -> Self {
        PySnapshotStatus(SnapshotStatus::Failure)
    }
}
