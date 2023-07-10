use pyo3::{prelude::*, pyclass::CompareOp};

use raft::StateRole;

#[pyclass(name = "StateRole")]
pub struct PyStateRole(pub StateRole);

impl From<PyStateRole> for StateRole {
    fn from(val: PyStateRole) -> Self {
        val.0
    }
}

impl From<StateRole> for PyStateRole {
    fn from(x: StateRole) -> Self {
        match x {
            StateRole::Candidate => PyStateRole(StateRole::Candidate),
            StateRole::Follower => PyStateRole(StateRole::Follower),
            StateRole::Leader => PyStateRole(StateRole::Leader),
            StateRole::PreCandidate => PyStateRole(StateRole::PreCandidate),
        }
    }
}

#[pymethods]
impl PyStateRole {
    pub fn __richcmp__(&self, py: Python, rhs: &PyStateRole, op: CompareOp) -> PyObject {
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
            StateRole::Candidate => "Candidate".to_string(),
            StateRole::Follower => "Follower".to_string(),
            StateRole::Leader => "Leader".to_string(),
            StateRole::PreCandidate => "PreCandidate".to_string(),
        }
    }

    #[classattr]
    pub fn Candidate() -> Self {
        PyStateRole(StateRole::Candidate)
    }

    #[classattr]
    pub fn Follower() -> Self {
        PyStateRole(StateRole::Follower)
    }

    #[classattr]
    pub fn Leader() -> Self {
        PyStateRole(StateRole::Leader)
    }

    #[classattr]
    pub fn PreCandidate() -> Self {
        PyStateRole(StateRole::PreCandidate)
    }
}
