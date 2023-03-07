use pyo3::{prelude::*, pyclass::CompareOp};

use raft::StateRole;

#[pyclass(name = "StateRole")]
pub struct Py_StateRole(pub StateRole);

impl Into<StateRole> for Py_StateRole {
    fn into(self) -> StateRole {
        match self.0 {
            StateRole::Candidate => StateRole::Candidate,
            StateRole::Follower => StateRole::Follower,
            StateRole::Leader => StateRole::Leader,
            StateRole::PreCandidate => StateRole::PreCandidate,
        }
    }
}

impl From<StateRole> for Py_StateRole {
    fn from(opt: StateRole) -> Self {
        match opt {
            StateRole::Candidate => Py_StateRole(StateRole::Candidate),
            StateRole::Follower => Py_StateRole(StateRole::Follower),
            StateRole::Leader => Py_StateRole(StateRole::Leader),
            StateRole::PreCandidate => Py_StateRole(StateRole::PreCandidate),
        }
    }
}

#[pymethods]
impl Py_StateRole {
    pub fn __richcmp__(&self, rhs: &Py_StateRole, op: CompareOp) -> PyResult<bool> {
        Ok(match op {
            CompareOp::Eq => self.0 == rhs.0,
            CompareOp::Ne => self.0 != rhs.0,
            _ => panic!("Undefined operator"),
        })
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
