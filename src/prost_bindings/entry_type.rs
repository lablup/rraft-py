use pyo3::{prelude::*, pyclass::CompareOp};

use raft::eraftpb::EntryType;

#[derive(Clone)]
#[pyclass(name = "EntryType")]
pub struct Py_EntryType(pub EntryType);

impl From<Py_EntryType> for EntryType {
    fn from(val: Py_EntryType) -> Self {
        match val.0 {
            EntryType::EntryConfChange => EntryType::EntryConfChange,
            EntryType::EntryConfChangeV2 => EntryType::EntryConfChangeV2,
            EntryType::EntryNormal => EntryType::EntryNormal,
        }
    }
}

impl From<EntryType> for Py_EntryType {
    fn from(x: EntryType) -> Self {
        match x {
            EntryType::EntryConfChange => Py_EntryType(EntryType::EntryConfChange),
            EntryType::EntryConfChangeV2 => Py_EntryType(EntryType::EntryConfChangeV2),
            EntryType::EntryNormal => Py_EntryType(EntryType::EntryNormal),
        }
    }
}

#[pymethods]
impl Py_EntryType {
    pub fn __richcmp__(
        &self,
        py: Python<'_>,
        rhs: &Py_EntryType,
        op: CompareOp,
    ) -> PyResult<PyObject> {
        Ok(match op {
            CompareOp::Eq => (self.0 == rhs.0).into_py(py),
            CompareOp::Ne => (self.0 != rhs.0).into_py(py),
            _ => py.NotImplemented(),
        })
    }

    pub fn __hash__(&self) -> u64 {
        self.0 as u64
    }

    pub fn __repr__(&self) -> String {
        match self.0 {
            EntryType::EntryConfChange => "EntryConfChange".to_string(),
            EntryType::EntryConfChangeV2 => "EntryConfChangeV2".to_string(),
            EntryType::EntryNormal => "EntryNormal".to_string(),
        }
    }

    #[classattr]
    pub fn EntryConfChange() -> Self {
        Py_EntryType(EntryType::EntryConfChange)
    }

    #[classattr]
    pub fn EntryConfChangeV2() -> Self {
        Py_EntryType(EntryType::EntryConfChangeV2)
    }

    #[classattr]
    pub fn EntryNormal() -> Self {
        Py_EntryType(EntryType::EntryNormal)
    }
}