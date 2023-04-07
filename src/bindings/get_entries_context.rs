use pyo3::{intern, prelude::*};
use raft::GetEntriesContext;

use utils::reference::RustRef;

#[pyclass(name = "GetEntriesContext")]
pub struct Py_GetEntriesContext {
    pub inner: GetEntriesContext,
}

#[pyclass(name = "GetEntriesContext_Ref")]
pub struct Py_GetEntriesContext_Ref {
    pub inner: RustRef<GetEntriesContext>,
}

#[pymethods]
impl Py_GetEntriesContext {
    #[staticmethod]
    pub fn empty(can_async: bool) -> Self {
        Py_GetEntriesContext {
            inner: GetEntriesContext::empty(can_async),
        }
    }

    pub fn make_ref(&mut self) -> Py_GetEntriesContext_Ref {
        Py_GetEntriesContext_Ref {
            inner: RustRef::new(&mut self.inner),
        }
    }

    pub fn __repr__(&self) -> String {
        format!("{:?}", self.inner)
    }

    fn __getattr__(this: PyObject, py: Python<'_>, attr: &str) -> PyResult<PyObject> {
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
