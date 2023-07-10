use pyo3::{intern, prelude::*, pyclass::CompareOp};

use crate::utils::reference::{RefMutContainer, RefMutOwner};
use raft::SoftState;

use super::state_role::PyStateRole;

#[pyclass(name = "SoftState")]
pub struct PySoftState {
    pub inner: RefMutOwner<SoftState>,
}

#[pyclass(name = "SoftStateRef")]
pub struct PySoftStateRef {
    pub inner: RefMutContainer<SoftState>,
}

#[pymethods]
impl PySoftState {
    #[staticmethod]
    pub fn default() -> Self {
        PySoftState {
            inner: RefMutOwner::new(SoftState::default()),
        }
    }

    pub fn make_ref(&mut self) -> PySoftStateRef {
        PySoftStateRef {
            inner: RefMutContainer::new(&mut self.inner),
        }
    }

    pub fn __repr__(&self) -> String {
        format!("{:?}", self.inner.inner)
    }

    pub fn __richcmp__(
        &self,
        py: Python,
        rhs: &PySoftStateRef,
        op: CompareOp,
    ) -> PyResult<PyObject> {
        match op {
            CompareOp::Eq => rhs
                .inner
                .map_as_ref(|x| (x == &self.inner.inner).into_py(py)),
            CompareOp::Ne => rhs
                .inner
                .map_as_ref(|x| (x != &self.inner.inner).into_py(py)),
            _ => Ok(py.NotImplemented()),
        }
    }

    fn __getattr__(this: PyObject, py: Python, attr: &str) -> PyResult<PyObject> {
        let reference = this.call_method0(py, intern!(py, "make_ref"))?;
        reference.getattr(py, attr)
    }
}

#[pymethods]
impl PySoftStateRef {
    pub fn __repr__(&self) -> PyResult<String> {
        self.inner.map_as_ref(|inner| format!("{:?}", inner))
    }

    pub fn __richcmp__(
        &self,
        py: Python,
        rhs: &PySoftStateRef,
        op: CompareOp,
    ) -> PyResult<PyObject> {
        self.inner.map_as_ref(|inner| match op {
            CompareOp::Eq => rhs.inner.map_as_ref(|x| (x == inner).into_py(py)),
            CompareOp::Ne => rhs.inner.map_as_ref(|x| (x != inner).into_py(py)),
            _ => Ok(py.NotImplemented()),
        })?
    }

    pub fn get_leader_id(&self) -> PyResult<u64> {
        self.inner.map_as_ref(|inner| inner.leader_id)
    }

    pub fn set_leader_id(&mut self, leader_id: u64) -> PyResult<()> {
        self.inner.map_as_mut(|inner| inner.leader_id = leader_id)
    }

    pub fn get_raft_state(&self) -> PyResult<PyStateRole> {
        self.inner.map_as_ref(|inner| inner.raft_state.into())
    }

    pub fn set_raft_state(&mut self, rs: &PyStateRole) -> PyResult<()> {
        self.inner.map_as_mut(|inner| inner.raft_state = rs.0)
    }
}
