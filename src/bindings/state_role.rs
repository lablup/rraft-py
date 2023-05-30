use pyo3::{prelude::*, pyclass::CompareOp};

use raft::StateRole;

#[pyclass(name = "StateRole")]
pub struct Py_StateRole(pub StateRole);

impl From<Py_StateRole> for StateRole {
    fn from(val: Py_StateRole) -> Self {
        val.0
    }
}

impl From<StateRole> for Py_StateRole {
    fn from(x: StateRole) -> Self {
        match x {
            StateRole::Candidate => Py_StateRole(StateRole::Candidate),
            StateRole::Follower => Py_StateRole(StateRole::Follower),
            StateRole::Leader => Py_StateRole(StateRole::Leader),
            StateRole::PreCandidate => Py_StateRole(StateRole::PreCandidate),
        }
    }
}

#[pymethods]
impl Py_StateRole {
    pub fn __richcmp__(&self, py: Python<'_>, rhs: &Py_StateRole, op: CompareOp) -> PyObject {
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
        Py_StateRole(StateRole::Candidate)
    }

    #[classattr]
    pub fn Follower() -> Self {
        Py_StateRole(StateRole::Follower)
    }

    #[classattr]
    pub fn Leader() -> Self {
        Py_StateRole(StateRole::Leader)
    }

    #[classattr]
    pub fn PreCandidate() -> Self {
        Py_StateRole(StateRole::PreCandidate)
    }
}
