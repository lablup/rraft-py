use pyo3::{intern, prelude::*};

use raft::storage::RaftState;

use crate::implement_type_conversion;
use crate::raftpb_bindings::{
    conf_state::{PyConfStateMut, PyConfStateRef},
    hard_state::{PyHardStateMut, PyHardStateRef},
};
use crate::utils::reference::{RefMutContainer, RefMutOwner};

#[derive(Clone)]
#[pyclass(name = "RaftState")]
pub struct PyRaftState {
    pub inner: RefMutOwner<RaftState>,
}

#[derive(Clone)]
#[pyclass(name = "RaftStateRef")]
pub struct PyRaftStateRef {
    pub inner: RefMutContainer<RaftState>,
}

#[derive(FromPyObject)]
pub enum PyRaftStateMut<'p> {
    Owned(PyRefMut<'p, PyRaftState>),
    RefMut(PyRaftStateRef),
}

implement_type_conversion!(RaftState, PyRaftStateMut);

#[pymethods]
impl PyRaftState {
    #[new]
    pub fn new(hard_state: PyHardStateMut, conf_state: PyConfStateMut) -> Self {
        PyRaftState {
            inner: RefMutOwner::new(RaftState::new(hard_state.into(), conf_state.into())),
        }
    }

    #[staticmethod]
    pub fn default() -> Self {
        PyRaftState {
            inner: RefMutOwner::new(RaftState::default()),
        }
    }

    pub fn make_ref(&mut self) -> PyRaftStateRef {
        PyRaftStateRef {
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
impl PyRaftStateRef {
    pub fn __repr__(&self) -> PyResult<String> {
        self.inner.map_as_ref(|inner| format!("{:?}", inner))
    }

    pub fn clone(&self) -> PyResult<PyRaftState> {
        Ok(PyRaftState {
            inner: RefMutOwner::new(self.inner.map_as_ref(|x| x.clone())?),
        })
    }

    pub fn initialized(&self) -> PyResult<bool> {
        self.inner.map_as_ref(|inner| inner.initialized())
    }

    pub fn get_conf_state(&mut self) -> PyResult<PyConfStateRef> {
        self.inner.map_as_mut(|inner| PyConfStateRef {
            inner: RefMutContainer::new_raw(&mut inner.conf_state),
        })
    }

    pub fn set_conf_state(&mut self, cs: PyConfStateMut) -> PyResult<()> {
        self.inner.map_as_mut(|inner| inner.conf_state = cs.into())
    }

    pub fn get_hard_state(&mut self) -> PyResult<PyHardStateRef> {
        self.inner.map_as_mut(|inner| PyHardStateRef {
            inner: RefMutContainer::new_raw(&mut inner.hard_state),
        })
    }

    pub fn set_hard_state(&mut self, hs: PyHardStateMut) -> PyResult<()> {
        self.inner.map_as_mut(|inner| inner.hard_state = hs.into())
    }
}
