use pyo3::{prelude::*, pyclass::CompareOp};

use raft::eraftpb::ConfChangeTransition;

#[derive(Clone)]
#[pyclass(name = "ConfChangeTransition")]
pub struct Py_ConfChangeTransition(pub ConfChangeTransition);

impl Into<ConfChangeTransition> for Py_ConfChangeTransition {
    fn into(self) -> ConfChangeTransition {
        match self.0 {
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
    pub fn __richcmp__(&self, rhs: &Py_ConfChangeTransition, op: CompareOp) -> PyResult<bool> {
        Ok(match op {
            CompareOp::Eq => self.0 == rhs.0,
            CompareOp::Ne => self.0 != rhs.0,
            _ => panic!("Undefined operator"),
        })
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
