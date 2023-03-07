use pyo3::{prelude::*, pyclass::CompareOp};

use raft::eraftpb::ConfChangeType;

#[derive(Clone)]
#[pyclass(name = "ConfChangeType")]
pub struct Py_ConfChangeType(pub ConfChangeType);

impl Into<ConfChangeType> for Py_ConfChangeType {
    fn into(self) -> ConfChangeType {
        match self.0 {
            ConfChangeType::AddNode => ConfChangeType::AddNode,
            ConfChangeType::AddLearnerNode => ConfChangeType::AddLearnerNode,
            ConfChangeType::RemoveNode => ConfChangeType::RemoveNode,
        }
    }
}

impl From<ConfChangeType> for Py_ConfChangeType {
    fn from(x: ConfChangeType) -> Self {
        match x {
            ConfChangeType::AddNode => Py_ConfChangeType(ConfChangeType::AddNode),
            ConfChangeType::AddLearnerNode => Py_ConfChangeType(ConfChangeType::AddLearnerNode),
            ConfChangeType::RemoveNode => Py_ConfChangeType(ConfChangeType::RemoveNode),
        }
    }
}

#[pymethods]
impl Py_ConfChangeType {
    pub fn __richcmp__(&self, rhs: &Py_ConfChangeType, op: CompareOp) -> PyResult<bool> {
        Ok(match op {
            CompareOp::Eq => self.0 == rhs.0,
            CompareOp::Ne => self.0 != rhs.0,
            _ => panic!("Undefined operator"),
        })
    }

    #[classattr]
    pub fn AddNode() -> Self {
        Py_ConfChangeType(ConfChangeType::AddNode)
    }

    #[classattr]
    pub fn AddLearnerNode() -> Self {
        Py_ConfChangeType(ConfChangeType::AddLearnerNode)
    }

    #[classattr]
    pub fn RemoveNode() -> Self {
        Py_ConfChangeType(ConfChangeType::RemoveNode)
    }
}
