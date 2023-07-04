use pyo3::{prelude::*, pyclass::CompareOp};

use crate::utils::errors::runtime_error;
use raft::eraftpb::ConfChangeTransition;

#[derive(Clone)]
#[pyclass(name = "ConfChangeTransition")]
pub struct Py_ConfChangeTransition(pub ConfChangeTransition);

impl From<Py_ConfChangeTransition> for ConfChangeTransition {
    fn from(val: Py_ConfChangeTransition) -> Self {
        val.0
    }
}

impl From<ConfChangeTransition> for Py_ConfChangeTransition {
    fn from(x: ConfChangeTransition) -> Self {
        match x {
            ConfChangeTransition::Auto => Py_ConfChangeTransition(ConfChangeTransition::Auto),
            ConfChangeTransition::Implicit => {
                Py_ConfChangeTransition(ConfChangeTransition::Implicit)
            }
            ConfChangeTransition::Explicit => {
                Py_ConfChangeTransition(ConfChangeTransition::Explicit)
            }
        }
    }
}

#[pymethods]
impl Py_ConfChangeTransition {
    pub fn __richcmp__(
        &self,
        py: Python,
        rhs: &Py_ConfChangeTransition,
        op: CompareOp,
    ) -> PyObject {
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
            ConfChangeTransition::Auto => "Auto".to_string(),
            ConfChangeTransition::Implicit => "Implicit".to_string(),
            ConfChangeTransition::Explicit => "Explicit".to_string(),
        }
    }

    pub fn __int__(&self) -> u64 {
        self.0 as u64
    }

    #[staticmethod]
    pub fn from_int(v: i32, py: Python) -> PyResult<PyObject> {
        ConfChangeTransition::from_i32(v)
            .map(|x| Py_ConfChangeTransition(x).into_py(py))
            .ok_or_else(|| runtime_error("Invalid value"))
    }

    #[classattr]
    pub fn Auto() -> Self {
        Py_ConfChangeTransition(ConfChangeTransition::Auto)
    }

    #[classattr]
    pub fn Implicit() -> Self {
        Py_ConfChangeTransition(ConfChangeTransition::Implicit)
    }

    #[classattr]
    pub fn Explicit() -> Self {
        Py_ConfChangeTransition(ConfChangeTransition::Explicit)
    }
}
