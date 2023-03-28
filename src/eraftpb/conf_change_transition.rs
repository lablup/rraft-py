use pyo3::{prelude::*, pyclass::CompareOp};

use raft::eraftpb::ConfChangeTransition;

#[derive(Clone)]
#[pyclass(name = "ConfChangeTransition")]
pub struct Py_ConfChangeTransition(pub ConfChangeTransition);

impl From<Py_ConfChangeTransition> for ConfChangeTransition {
    fn from(val: Py_ConfChangeTransition) -> Self {
        match val.0 {
            ConfChangeTransition::Auto => ConfChangeTransition::Auto,
            ConfChangeTransition::Explicit => ConfChangeTransition::Explicit,
            ConfChangeTransition::Implicit => ConfChangeTransition::Implicit,
        }
    }
}

impl From<ConfChangeTransition> for Py_ConfChangeTransition {
    fn from(x: ConfChangeTransition) -> Self {
        match x {
            ConfChangeTransition::Auto => Py_ConfChangeTransition(ConfChangeTransition::Auto),
            ConfChangeTransition::Explicit => {
                Py_ConfChangeTransition(ConfChangeTransition::Explicit)
            }
            ConfChangeTransition::Implicit => {
                Py_ConfChangeTransition(ConfChangeTransition::Implicit)
            }
        }
    }
}

#[pymethods]
impl Py_ConfChangeTransition {
    pub fn __richcmp__(
        &self,
        py: Python<'_>,
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
            ConfChangeTransition::Explicit => "Explicit".to_string(),
            ConfChangeTransition::Implicit => "Implicit".to_string(),
        }
    }

    #[classattr]
    pub fn Auto() -> Self {
        Py_ConfChangeTransition(ConfChangeTransition::Auto)
    }

    #[classattr]
    pub fn Explicit() -> Self {
        Py_ConfChangeTransition(ConfChangeTransition::Explicit)
    }

    #[classattr]
    pub fn Implicit() -> Self {
        Py_ConfChangeTransition(ConfChangeTransition::Implicit)
    }
}
