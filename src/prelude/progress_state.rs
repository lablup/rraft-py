use pyo3::{prelude::*, pyclass::CompareOp};

use raft::ProgressState;

#[derive(Clone)]
#[pyclass(name = "ProgressState")]
pub struct Py_ProgressState(pub ProgressState);

impl Into<ProgressState> for Py_ProgressState {
    fn into(self) -> ProgressState {
        match self.0 {
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
    pub fn __richcmp__(&self, rhs: Py_ProgressState, op: CompareOp) -> PyResult<bool> {
        Ok(match op {
            CompareOp::Eq => self.0 == rhs.0,
            CompareOp::Ne => self.0 != rhs.0,
            _ => panic!("Undefined operator"),
        })
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
