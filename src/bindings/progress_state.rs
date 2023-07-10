use pyo3::{prelude::*, pyclass::CompareOp};

use raft::ProgressState;

#[derive(Clone)]
#[pyclass(name = "ProgressState")]
pub struct PyProgressState(pub ProgressState);

impl From<PyProgressState> for ProgressState {
    fn from(val: PyProgressState) -> Self {
        val.0
    }
}

impl From<ProgressState> for PyProgressState {
    fn from(x: ProgressState) -> Self {
        match x {
            ProgressState::Probe => PyProgressState(ProgressState::Probe),
            ProgressState::Replicate => PyProgressState(ProgressState::Replicate),
            ProgressState::Snapshot => PyProgressState(ProgressState::Snapshot),
        }
    }
}

#[pymethods]
impl PyProgressState {
    pub fn __repr__(&self) -> String {
        match self.0 {
            ProgressState::Probe => "Probe".to_string(),
            ProgressState::Replicate => "Replicate".to_string(),
            ProgressState::Snapshot => "Snapshot".to_string(),
        }
    }

    pub fn __richcmp__(&self, py: Python, rhs: PyProgressState, op: CompareOp) -> PyObject {
        match op {
            CompareOp::Eq => (self.0 == rhs.0).into_py(py),
            CompareOp::Ne => (self.0 != rhs.0).into_py(py),
            _ => py.NotImplemented(),
        }
    }

    pub fn __hash__(&self) -> u64 {
        self.0 as u64
    }

    #[classattr]
    pub fn Probe() -> Self {
        PyProgressState(ProgressState::Probe)
    }

    #[classattr]
    pub fn Replicate() -> Self {
        PyProgressState(ProgressState::Replicate)
    }

    #[classattr]
    pub fn Snapshot() -> Self {
        PyProgressState(ProgressState::Snapshot)
    }
}
