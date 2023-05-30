use pyo3::{prelude::*, pyclass::CompareOp};

use raft::eraftpb::ConfChangeType;
use utils::errors::runtime_error;

#[derive(Clone)]
#[pyclass(name = "ConfChangeType")]
pub struct Py_ConfChangeType(pub ConfChangeType);

impl From<Py_ConfChangeType> for ConfChangeType {
    fn from(val: Py_ConfChangeType) -> Self {
        val.0
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
    pub fn __richcmp__(&self, py: Python<'_>, rhs: &Py_ConfChangeType, op: CompareOp) -> PyObject {
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
            ConfChangeType::AddNode => "AddNode".to_string(),
            ConfChangeType::AddLearnerNode => "AddLearnerNode".to_string(),
            ConfChangeType::RemoveNode => "RemoveNode".to_string(),
        }
    }

    pub fn __int__(&self) -> u64 {
        self.0 as u64
    }

    #[staticmethod]
    pub fn from_int(v: i32, py: Python) -> PyResult<PyObject> {
        ConfChangeType::from_i32(v)
            .map(|x| Py_ConfChangeType(x).into_py(py))
            .ok_or_else(|| runtime_error("Invalid value"))
    }

    #[staticmethod]
    pub fn from_str(v: &str, py: Python) -> PyObject {
        match v {
            "AddNode" => Py_ConfChangeType(ConfChangeType::AddNode).into_py(py),
            "AddLearnerNode" => Py_ConfChangeType(ConfChangeType::AddLearnerNode).into_py(py),
            "RemoveNode" => Py_ConfChangeType(ConfChangeType::RemoveNode).into_py(py),
            _ => py.None(),
        }
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
