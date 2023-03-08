use pyo3::prelude::*;

use raft::storage::RaftState;
use utils::reference::RustRef;

use crate::eraftpb::{
    conf_state::{Py_ConfState_Mut, Py_ConfState_Ref},
    hard_state::{Py_HardState_Mut, Py_HardState_Ref},
};

#[derive(Clone)]
#[pyclass(name = "RaftState_Owner")]
pub struct Py_RaftState_Owner {
    pub inner: RaftState,
}

#[derive(Clone)]
#[pyclass(name = "RaftState_Ref")]
pub struct Py_RaftState_Ref {
    pub inner: RustRef<RaftState>,
}

#[derive(FromPyObject)]
pub enum Py_RaftState_Mut<'p> {
    Owned(PyRefMut<'p, Py_RaftState_Owner>),
    RefMut(Py_RaftState_Ref),
}

impl Into<RaftState> for Py_RaftState_Mut<'_> {
    fn into(self) -> RaftState {
        match self {
            Py_RaftState_Mut::Owned(x) => x.inner.clone(),
            Py_RaftState_Mut::RefMut(mut x) => x.inner.map_as_mut(|x| x.clone()).unwrap(),
        }
    }
}

impl Into<RaftState> for &mut Py_RaftState_Mut<'_> {
    fn into(self) -> RaftState {
        match self {
            Py_RaftState_Mut::Owned(x) => x.inner.clone(),
            Py_RaftState_Mut::RefMut(x) => x.inner.map_as_mut(|x| x.clone()).unwrap(),
        }
    }
}

#[pymethods]
impl Py_RaftState_Owner {
    #[new]
    pub fn new() -> Self {
        Py_RaftState_Owner {
            inner: RaftState::default(),
        }
    }

    pub fn make_ref(&mut self) -> Py_RaftState_Ref {
        Py_RaftState_Ref {
            inner: RustRef::new(&mut self.inner),
        }
    }

    pub fn clone(&self) -> Py_RaftState_Owner {
        Py_RaftState_Owner {
            inner: self.inner.clone(),
        }
    }

    pub fn __repr__(&self) -> String {
        format!("{:?}", self.inner)
    }
}

#[pymethods]
impl Py_RaftState_Ref {
    pub fn __repr__(&self) -> PyResult<String> {
        self.inner.map_as_ref(|inner| format!("{:?}", inner))
    }

    pub fn clone(&self) -> Py_RaftState_Owner {
        Py_RaftState_Owner {
            inner: self.inner.map_as_ref(|x| x.clone()).unwrap(),
        }
    }

    pub fn initialized(&self) -> PyResult<bool> {
        self.inner.map_as_ref(|inner| inner.initialized())
    }

    pub fn get_conf_state(&mut self) -> PyResult<Py_ConfState_Ref> {
        self.inner.map_as_mut(|inner| Py_ConfState_Ref {
            inner: RustRef::new(&mut inner.conf_state),
        })
    }

    pub fn set_conf_state(&mut self, cs: Py_ConfState_Mut) -> PyResult<()> {
        self.inner.map_as_mut(|inner| inner.conf_state = cs.into())
    }

    pub fn get_hard_state(&mut self) -> PyResult<Py_HardState_Ref> {
        self.inner.map_as_mut(|inner| Py_HardState_Ref {
            inner: RustRef::new(&mut inner.hard_state),
        })
    }

    pub fn set_hard_state(&mut self, hs: Py_HardState_Mut) -> PyResult<()> {
        self.inner.map_as_mut(|inner| inner.hard_state = hs.into())
    }
}
