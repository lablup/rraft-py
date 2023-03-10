use pyo3::prelude::*;

use crate::{
    eraftpb::{
        entry::{Py_Entry_Owner, Py_Entry_Ref},
        hard_state::Py_HardState_Ref,
        message::{Py_Message_Owner, Py_Message_Ref},
        snapshot::Py_Snapshot_Ref,
    },
    prelude::{
        read_state::{Py_ReadState_Owner, Py_ReadState_Ref},
        soft_state::Py_SoftState_Owner,
    },
};
use raft::{raw_node::Ready, SoftState};
use utils::{reference::RustRef, unsafe_cast::make_mut};

#[pyclass(name = "Ready_Owner")]
pub struct Py_Ready_Owner {
    pub inner: Ready,
}

#[pyclass(name = "Ready_Ref")]
pub struct Py_Ready_Ref {
    pub inner: RustRef<Ready>,
}

#[pymethods]
impl Py_Ready_Owner {
    #[staticmethod]
    pub fn default() -> Self {
        Py_Ready_Owner {
            inner: Ready::default(),
        }
    }

    pub fn make_ref(&mut self) -> Py_Ready_Ref {
        Py_Ready_Ref {
            inner: RustRef::new(&mut self.inner),
        }
    }

    pub fn __repr__(&self) -> String {
        format!("{:?}", self.inner)
    }
}

#[pymethods]
impl Py_Ready_Ref {
    pub fn __repr__(&self) -> PyResult<String> {
        self.inner.map_as_ref(|inner| format!("{:?}", inner))
    }

    pub fn hs(&mut self) -> PyResult<Option<Py_HardState_Ref>> {
        self.inner.map_as_mut(|inner| match inner.hs() {
            Some(hs) => Some(Py_HardState_Ref {
                inner: RustRef::new(unsafe { make_mut(hs) }),
            }),
            None => None,
        })
    }

    pub fn ss(&mut self) -> PyResult<Option<Py_SoftState_Owner>> {
        self.inner.map_as_mut(|inner| match inner.ss() {
            Some(ss) => Some(Py_SoftState_Owner {
                inner: SoftState {
                    leader_id: ss.leader_id,
                    raft_state: ss.raft_state,
                },
            }),
            None => None,
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
            inner: RustRef::new(unsafe { make_mut(inner.snapshot()) }),
        })
    }

    pub fn committed_entries(&self, py: Python) -> PyResult<PyObject> {
        self.inner.map_as_ref(|inner| {
            let entries = unsafe { make_mut(inner.committed_entries()) };
            entries
                .iter_mut()
                .map(|entry| Py_Entry_Ref {
                    inner: RustRef::new(entry),
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

    pub fn entries(&self, py: Python) -> PyResult<PyObject> {
        self.inner.map_as_ref(|inner| {
            let entries = unsafe { make_mut(inner.entries()) };

            entries
                .iter_mut()
                .map(|entry| Py_Entry_Ref {
                    inner: RustRef::new(entry),
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
                .map(|entry| Py_Entry_Owner { inner: entry })
                .collect::<Vec<_>>()
                .into_py(py)
        })
    }

    pub fn messages(&self, py: Python) -> PyResult<PyObject> {
        self.inner.map_as_ref(|inner| {
            inner
                .messages()
                .into_iter()
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

    pub fn persisted_messages(&self, py: Python) -> PyResult<PyObject> {
        self.inner.map_as_ref(|inner| {
            inner
                .persisted_messages()
                .iter()
                .map(|msg| Py_Message_Ref {
                    inner: RustRef::new(unsafe { make_mut(msg) }),
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
                .map(|msg| Py_Message_Owner { inner: msg })
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
                    inner: RustRef::new(unsafe { make_mut(rs) }),
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
                .map(|rs| Py_ReadState_Owner { inner: rs })
                .collect::<Vec<_>>()
                .into_py(py)
        })
    }
}
