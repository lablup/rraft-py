use crate::raftpb_bindings::{
    entry::{PyEntry, PyEntryRef},
    message::{PyMessage, PyMessageRef},
};
use crate::utils::{
    reference::{RefMutContainer, RefMutOwner},
    unsafe_cast::make_mut,
};
use pyo3::{intern, prelude::*};
use raft::raw_node::LightReady;

#[pyclass(name = "LightReady")]
pub struct PyLightReady {
    pub inner: RefMutOwner<LightReady>,
}

#[pyclass(name = "LightReadyRef")]
pub struct PyLightReadyRef {
    pub inner: RefMutContainer<LightReady>,
}

#[pymethods]
impl PyLightReady {
    #[staticmethod]
    pub fn default() -> Self {
        PyLightReady {
            inner: RefMutOwner::new(LightReady::default()),
        }
    }

    pub fn make_ref(&mut self) -> PyLightReadyRef {
        PyLightReadyRef {
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
impl PyLightReadyRef {
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
                .map(|entry| PyEntryRef {
                    inner: RefMutContainer::new_raw(unsafe { make_mut(entry) }),
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
                .map(|entry| PyEntry {
                    inner: RefMutOwner::new(entry),
                })
                .collect::<Vec<_>>()
                .into_py(py)
        })
    }

    pub fn messages(&self, py: Python) -> PyResult<PyObject> {
        self.inner.map_as_ref(|inner| {
            inner
                .messages()
                .iter()
                .map(|msg| PyMessageRef {
                    inner: RefMutContainer::new_raw(unsafe { make_mut(msg) }),
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
                .map(|msg| PyMessage {
                    inner: RefMutOwner::new(msg),
                })
                .collect::<Vec<_>>()
                .into_py(py)
        })
    }
}
