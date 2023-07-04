use pyo3::{intern, prelude::*};
use raft::GetEntriesContext;
use crate::utils::reference::{RefMutContainer, RefMutOwner};

#[pyclass(name = "GetEntriesContext")]
pub struct Py_GetEntriesContext {
    pub inner: RefMutOwner<GetEntriesContext>,
}

#[pyclass(name = "GetEntriesContext_Ref")]
pub struct Py_GetEntriesContext_Ref {
    pub inner: RefMutContainer<GetEntriesContext>,
}

#[pymethods]
impl Py_GetEntriesContext {
    #[staticmethod]
    pub fn empty(can_async: bool) -> Self {
        Py_GetEntriesContext {
            inner: RefMutOwner::new(GetEntriesContext::empty(can_async)),
        }
    }

    pub fn make_ref(&mut self) -> Py_GetEntriesContext_Ref {
        Py_GetEntriesContext_Ref {
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
impl Py_GetEntriesContext_Ref {
    pub fn __repr__(&self) -> PyResult<String> {
        self.inner.map_as_ref(|inner| format!("{:?}", inner))
    }

    pub fn can_async(&self) -> PyResult<bool> {
        self.inner.map_as_ref(|inner| inner.can_async())
    }
}
