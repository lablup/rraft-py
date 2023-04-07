use pyo3::{intern, prelude::*};

use raft::storage::RaftState;
use utils::reference::RustRef;

use raftpb_bindings::{
    conf_state::{Py_ConfState_Mut, Py_ConfState_Ref},
    hard_state::{Py_HardState_Mut, Py_HardState_Ref},
};

#[derive(Clone)]
#[pyclass(name = "RaftState")]
pub struct Py_RaftState {
    pub inner: RaftState,
}

#[derive(Clone)]
#[pyclass(name = "RaftState_Ref")]
pub struct Py_RaftState_Ref {
    pub inner: RustRef<RaftState>,
}

#[derive(FromPyObject)]
pub enum Py_RaftState_Mut<'p> {
    Owned(PyRefMut<'p, Py_RaftState>),
    RefMut(Py_RaftState_Ref),
}

impl From<Py_RaftState_Mut<'_>> for RaftState {
    fn from(val: Py_RaftState_Mut<'_>) -> Self {
        match val {
            Py_RaftState_Mut::Owned(x) => x.inner.clone(),
            Py_RaftState_Mut::RefMut(mut x) => x.inner.map_as_mut(|x| x.clone()).unwrap(),
        }
    }
}

impl From<&mut Py_RaftState_Mut<'_>> for RaftState {
    fn from(val: &mut Py_RaftState_Mut<'_>) -> Self {
        match val {
            Py_RaftState_Mut::Owned(x) => x.inner.clone(),
            Py_RaftState_Mut::RefMut(x) => x.inner.map_as_mut(|x| x.clone()).unwrap(),
        }
    }
}

#[pymethods]
impl Py_RaftState {
    #[new]
    pub fn new(hard_state: Py_HardState_Mut, conf_state: Py_ConfState_Mut) -> Self {
        Py_RaftState {
            inner: RaftState::new(hard_state.into(), conf_state.into()),
        }
    }

    #[staticmethod]
    pub fn default() -> Self {
        Py_RaftState {
            inner: RaftState::default(),
        }
    }

    pub fn make_ref(&mut self) -> Py_RaftState_Ref {
        Py_RaftState_Ref {
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
impl Py_RaftState_Ref {
    pub fn __repr__(&self) -> PyResult<String> {
        self.inner.map_as_ref(|inner| format!("{:?}", inner))
    }

    pub fn clone(&self) -> PyResult<Py_RaftState> {
        Ok(Py_RaftState {
            inner: self.inner.map_as_ref(|x| x.clone())?,
        })
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
