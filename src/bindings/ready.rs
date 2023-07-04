use pyo3::{intern, prelude::*};

use crate::raftpb_bindings::{
    entry::{Py_Entry, Py_Entry_Ref},
    hard_state::Py_HardState_Ref,
    message::{Py_Message, Py_Message_Ref},
    snapshot::Py_Snapshot_Ref,
};

use super::{
    read_state::{Py_ReadState, Py_ReadState_Ref},
    soft_state::Py_SoftState,
};
use crate::utils::{
    reference::{RefMutContainer, RefMutOwner},
    unsafe_cast::make_mut,
};
use raft::{raw_node::Ready, SoftState};

#[pyclass(name = "Ready")]
pub struct Py_Ready {
    pub inner: RefMutOwner<Ready>,
}

#[pyclass(name = "Ready_Ref")]
pub struct Py_Ready_Ref {
    pub inner: RefMutContainer<Ready>,
}

#[pymethods]
impl Py_Ready {
    #[staticmethod]
    pub fn default() -> Self {
        Py_Ready {
            inner: RefMutOwner::new(Ready::default()),
        }
    }

    pub fn make_ref(&mut self) -> Py_Ready_Ref {
        Py_Ready_Ref {
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
impl Py_Ready_Ref {
    pub fn __repr__(&self) -> PyResult<String> {
        self.inner.map_as_ref(|inner| format!("{:?}", inner))
    }

    pub fn hs(&mut self) -> PyResult<Option<Py_HardState_Ref>> {
        self.inner.map_as_mut(|inner| {
            inner.hs().map(|hs| Py_HardState_Ref {
                inner: RefMutContainer::new_raw(unsafe { make_mut(hs) }),
            })
        })
    }

    pub fn ss(&mut self) -> PyResult<Option<Py_SoftState>> {
        self.inner.map_as_mut(|inner| {
            inner.ss().map(|ss| Py_SoftState {
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

    pub fn snapshot(&mut self) -> PyResult<Py_Snapshot_Ref> {
        self.inner.map_as_mut(|inner| Py_Snapshot_Ref {
            inner: RefMutContainer::new_raw(unsafe { make_mut(inner.snapshot()) }),
        })
    }

    pub fn committed_entries(&self, py: Python) -> PyResult<PyObject> {
        self.inner.map_as_ref(|inner| {
            unsafe { make_mut(inner.committed_entries()) }
                .iter_mut()
                .map(|entry| Py_Entry_Ref {
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
                .map(|entry| Py_Entry {
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
                .map(|entry| Py_Entry_Ref {
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
                .map(|entry| Py_Entry {
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
                .map(|msg| Py_Message_Ref {
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
                .map(|msg| Py_Message {
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
                .map(|msg| Py_Message_Ref {
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
                .map(|msg| Py_Message {
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
                .map(|rs| Py_ReadState_Ref {
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
                .map(|rs| Py_ReadState {
                    inner: RefMutOwner::new(rs),
                })
                .collect::<Vec<_>>()
                .into_py(py)
        })
    }
}
