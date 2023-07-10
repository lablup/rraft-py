use pyo3::{intern, prelude::*};

use crate::raftpb_bindings::{
    entry::{PyEntry, PyEntryRef},
    hard_state::PyHardStateRef,
    message::{PyMessage, PyMessageRef},
    snapshot::PySnapshotRef,
};

use super::{
    read_state::{PyReadState, PyReadStateRef},
    soft_state::PySoftState,
};
use crate::utils::{
    reference::{RefMutContainer, RefMutOwner},
    unsafe_cast::make_mut,
};
use raft::{raw_node::Ready, SoftState};

#[pyclass(name = "Ready")]
pub struct PyReady {
    pub inner: RefMutOwner<Ready>,
}

#[pyclass(name = "ReadyRef")]
pub struct PyReadyRef {
    pub inner: RefMutContainer<Ready>,
}

#[pymethods]
impl PyReady {
    #[staticmethod]
    pub fn default() -> Self {
        PyReady {
            inner: RefMutOwner::new(Ready::default()),
        }
    }

    pub fn make_ref(&mut self) -> PyReadyRef {
        PyReadyRef {
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
impl PyReadyRef {
    pub fn __repr__(&self) -> PyResult<String> {
        self.inner.map_as_ref(|inner| format!("{:?}", inner))
    }

    pub fn hs(&mut self) -> PyResult<Option<PyHardStateRef>> {
        self.inner.map_as_mut(|inner| {
            inner.hs().map(|hs| PyHardStateRef {
                inner: RefMutContainer::new_raw(unsafe { make_mut(hs) }),
            })
        })
    }

    pub fn ss(&mut self) -> PyResult<Option<PySoftState>> {
        self.inner.map_as_mut(|inner| {
            inner.ss().map(|ss| PySoftState {
                inner: RefMutOwner::new(SoftState {
                    leader_id: ss.leader_id,
                    raft_state: ss.raft_state,
                }),
            })
        })
    }

    pub fn must_sync(&self) -> PyResult<bool> {
        self.inner.map_as_ref(|inner| inner.must_sync())
    }

    pub fn number(&self) -> PyResult<u64> {
        self.inner.map_as_ref(|inner| inner.number())
    }

    pub fn snapshot(&mut self) -> PyResult<PySnapshotRef> {
        self.inner.map_as_mut(|inner| PySnapshotRef {
            inner: RefMutContainer::new_raw(unsafe { make_mut(inner.snapshot()) }),
        })
    }

    pub fn committed_entries(&self, py: Python) -> PyResult<PyObject> {
        self.inner.map_as_ref(|inner| {
            unsafe { make_mut(inner.committed_entries()) }
                .iter_mut()
                .map(|entry| PyEntryRef {
                    inner: RefMutContainer::new_raw(entry),
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

    pub fn entries(&self, py: Python) -> PyResult<PyObject> {
        self.inner.map_as_ref(|inner| {
            unsafe { make_mut(inner.entries()) }
                .iter_mut()
                .map(|entry| PyEntryRef {
                    inner: RefMutContainer::new_raw(entry),
                })
                .collect::<Vec<_>>()
                .into_py(py)
        })
    }

    pub fn take_entries(&mut self, py: Python) -> PyResult<PyObject> {
        self.inner.map_as_mut(|inner| {
            inner
                .take_entries()
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

    pub fn persisted_messages(&self, py: Python) -> PyResult<PyObject> {
        self.inner.map_as_ref(|inner| {
            inner
                .persisted_messages()
                .iter()
                .map(|msg| PyMessageRef {
                    inner: RefMutContainer::new_raw(unsafe { make_mut(msg) }),
                })
                .collect::<Vec<_>>()
                .into_py(py)
        })
    }

    pub fn take_persisted_messages(&mut self, py: Python) -> PyResult<PyObject> {
        self.inner.map_as_mut(|inner| {
            inner
                .take_persisted_messages()
                .into_iter()
                .map(|msg| PyMessage {
                    inner: RefMutOwner::new(msg),
                })
                .collect::<Vec<_>>()
                .into_py(py)
        })
    }

    pub fn read_states(&self, py: Python) -> PyResult<PyObject> {
        self.inner.map_as_ref(|inner| {
            inner
                .read_states()
                .iter()
                .map(|rs| PyReadStateRef {
                    inner: RefMutContainer::new_raw(unsafe { make_mut(rs) }),
                })
                .collect::<Vec<_>>()
                .into_py(py)
        })
    }

    pub fn take_read_states(&mut self, py: Python) -> PyResult<PyObject> {
        self.inner.map_as_mut(|inner| {
            inner
                .take_read_states()
                .into_iter()
                .map(|rs| PyReadState {
                    inner: RefMutOwner::new(rs),
                })
                .collect::<Vec<_>>()
                .into_py(py)
        })
    }
}
