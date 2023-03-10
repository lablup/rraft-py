use pyo3::{prelude::*, pyclass::CompareOp};

use raft::ReadOnlyOption;

#[derive(Clone)]
#[pyclass(name = "ReadOnlyOption")]
pub struct Py_ReadOnlyOption(pub ReadOnlyOption);

impl Into<ReadOnlyOption> for Py_ReadOnlyOption {
    fn into(self) -> ReadOnlyOption {
        match self.0 {
            ReadOnlyOption::Safe => ReadOnlyOption::Safe,
            ReadOnlyOption::LeaseBased => ReadOnlyOption::LeaseBased,
        }
    }
}

impl From<ReadOnlyOption> for Py_ReadOnlyOption {
    fn from(x: ReadOnlyOption) -> Self {
        match x {
            ReadOnlyOption::Safe => Py_ReadOnlyOption(ReadOnlyOption::Safe),
            ReadOnlyOption::LeaseBased => Py_ReadOnlyOption(ReadOnlyOption::LeaseBased),
        }
    }
}

#[pymethods]
impl Py_ReadOnlyOption {
    pub fn __richcmp__(&self, rhs: &Py_ReadOnlyOption, op: CompareOp) -> PyResult<bool> {
        Ok(match op {
            CompareOp::Eq => self.0 == rhs.0,
            CompareOp::Ne => self.0 != rhs.0,
            _ => panic!("Undefined operator"),
        })
    }

    pub fn __hash__(&self) -> u64 {
        self.0 as u64
    }

    pub fn __repr__(&self) -> String {
        match self.0 {
            ReadOnlyOption::Safe => "Safe".to_string(),
            ReadOnlyOption::LeaseBased => "LeaseBased".to_string(),
        }
    }

    #[classattr]
    pub fn Safe() -> Self {
        Py_ReadOnlyOption(ReadOnlyOption::Safe)
    }

    #[classattr]
    pub fn LeaseBased() -> Self {
        Py_ReadOnlyOption(ReadOnlyOption::LeaseBased)
    }
}
