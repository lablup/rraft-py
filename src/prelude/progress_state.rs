use pyo3::{prelude::*, pyclass::CompareOp};

use raft::ProgressState;

#[derive(Clone)]
#[pyclass(name = "ProgressState")]
pub struct Py_ProgressState(pub ProgressState);

impl From<Py_ProgressState> for ProgressState {
    fn from(val: Py_ProgressState) -> Self {
        match val.0 {
            ProgressState::Probe => ProgressState::Probe,
            ProgressState::Replicate => ProgressState::Replicate,
            ProgressState::Snapshot => ProgressState::Snapshot,
        }
    }
}

impl From<ProgressState> for Py_ProgressState {
    fn from(x: ProgressState) -> Self {
        match x {
            ProgressState::Probe => Py_ProgressState(ProgressState::Probe),
            ProgressState::Replicate => Py_ProgressState(ProgressState::Replicate),
            ProgressState::Snapshot => Py_ProgressState(ProgressState::Snapshot),
        }
    }
}

#[pymethods]
impl Py_ProgressState {
    pub fn __repr__(&self) -> String {
        match self.0 {
            ProgressState::Probe => "Probe".to_string(),
            ProgressState::Replicate => "Replicate".to_string(),
            ProgressState::Snapshot => "Snapshot".to_string(),
        }
    }

    pub fn __richcmp__(&self, py: Python<'_>, rhs: Py_ProgressState, op: CompareOp) -> PyObject {
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
        Py_ProgressState(ProgressState::Probe)
    }

    #[classattr]
    pub fn Replicate() -> Self {
        Py_ProgressState(ProgressState::Replicate)
    }

    #[classattr]
    pub fn Snapshot() -> Self {
        Py_ProgressState(ProgressState::Snapshot)
    }
}
