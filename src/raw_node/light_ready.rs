use crate::eraftpb::{
    entry::{Py_Entry_Owner, Py_Entry_Ref},
    message::{Py_Message_Owner, Py_Message_Ref},
};
use pyo3::prelude::*;
use raft::raw_node::LightReady;
use utils::unsafe_cast::make_mut;
use utils::reference::RustRef;

#[pyclass(name = "LightReady_Owner")]
pub struct Py_LightReady_Owner {
    pub inner: LightReady,
}

#[pyclass(name = "LightReady_Ref")]
pub struct Py_LightReady_Ref {
    pub inner: RustRef<LightReady>,
}

#[pymethods]
impl Py_LightReady_Owner {
    #[new]
    pub fn new() -> Self {
        Py_LightReady_Owner {
            inner: LightReady::default(),
        }
    }

    pub fn make_ref(&mut self) -> Py_LightReady_Ref {
        Py_LightReady_Ref {
            inner: RustRef::new(&mut self.inner),
        }
    }

    pub fn __repr__(&self) -> String {
        format!("{:?}", self.inner)
    }
}

#[pymethods]
impl Py_LightReady_Ref {
    pub fn __repr__(&self) -> PyResult<String> {
        self.inner.map_as_ref(|inner| format!("{:?}", inner))
    }

    pub fn commit_index(&self) -> PyResult<Option<u64>> {
        self.inner.map_as_ref(|inner| inner.commit_index())
    }

    pub fn committed_entries(&self, py: Python) -> PyResult<PyObject> {
        self.inner.map_as_ref(|inner| {
            inner
                .committed_entries()
                .iter()
                .map(|entry| Py_Entry_Ref {
                    inner: RustRef::new(unsafe { make_mut(entry) }),
                })
                .collect::<Vec<_>>()
                .into_py(py)
        })
    }

    pub fn take_committed_entries(&mut self, py: Python) -> PyResult<PyObject> {
        self.inner.map_as_mut(|inner| {
            inner
                .take_committed_entries()
                .into_iter()
                .map(|entry| Py_Entry_Owner { inner: entry })
                .collect::<Vec<_>>()
                .into_py(py)
        })
    }

    pub fn messages(&self, py: Python) -> PyResult<PyObject> {
        self.inner.map_as_ref(|inner| {
            inner
                .messages()
                .iter()
                .map(|msg| Py_Message_Ref {
                    inner: RustRef::new(unsafe { make_mut(msg) }),
                })
                .collect::<Vec<_>>()
                .into_py(py)
        })
    }

    pub fn take_messages(&mut self, py: Python) -> PyResult<PyObject> {
        self.inner.map_as_mut(|inner| {
            inner
                .take_messages()
                .into_iter()
                .map(|msg| Py_Message_Owner { inner: msg })
                .collect::<Vec<_>>()
                .into_py(py)
        })
    }
}
