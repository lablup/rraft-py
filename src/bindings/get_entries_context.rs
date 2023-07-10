use crate::utils::reference::{RefMutContainer, RefMutOwner};
use pyo3::{intern, prelude::*};
use raft::GetEntriesContext;

#[pyclass(name = "GetEntriesContext")]
pub struct PyGetEntriesContext {
    pub inner: RefMutOwner<GetEntriesContext>,
}

#[pyclass(name = "GetEntriesContextRef")]
pub struct PyGetEntriesContextRef {
    pub inner: RefMutContainer<GetEntriesContext>,
}

#[pymethods]
impl PyGetEntriesContext {
    #[staticmethod]
    pub fn empty(can_async: bool) -> Self {
        PyGetEntriesContext {
            inner: RefMutOwner::new(GetEntriesContext::empty(can_async)),
        }
    }

    pub fn make_ref(&mut self) -> PyGetEntriesContextRef {
        PyGetEntriesContextRef {
            inner: RefMutContainer::new(&mut self.inner),
        }
    }

    pub fn __repr__(&self) -> String {
        format!("{:?}", self.inner.inner)
    }

    fn __getattr__(this: PyObject, py: Python, attr: &str) -> PyResult<PyObject> {
        let reference = this.call_method0(py, intern!(py, "make_ref"))?;
        reference.getattr(py, attr)
    }
}

#[pymethods]
impl PyGetEntriesContextRef {
    pub fn __repr__(&self) -> PyResult<String> {
        self.inner.map_as_ref(|inner| format!("{:?}", inner))
    }

    pub fn can_async(&self) -> PyResult<bool> {
        self.inner.map_as_ref(|inner| inner.can_async())
    }
}
