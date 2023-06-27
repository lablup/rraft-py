use pyo3::{intern, prelude::*, pyclass::CompareOp};

use raft::SoftState;
use utils::reference::{RefMutContainer, RefMutOwner};

use super::state_role::Py_StateRole;

#[pyclass(name = "SoftState")]
pub struct Py_SoftState {
    pub inner: RefMutOwner<SoftState>,
}

#[pyclass(name = "SoftState_Ref")]
pub struct Py_SoftState_Ref {
    pub inner: RefMutContainer<SoftState>,
}

#[pymethods]
impl Py_SoftState {
    #[staticmethod]
    pub fn default() -> Self {
        Py_SoftState {
            inner: RefMutOwner::new(SoftState::default()),
        }
    }

    pub fn make_ref(&mut self) -> Py_SoftState_Ref {
        Py_SoftState_Ref {
            inner: RefMutContainer::new(&mut self.inner),
        }
    }

    pub fn __repr__(&self) -> String {
        format!("{:?}", self.inner.inner)
    }

    pub fn __richcmp__(
        &self,
        py: Python,
        rhs: &Py_SoftState_Ref,
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
impl Py_SoftState_Ref {
    pub fn __repr__(&self) -> PyResult<String> {
        self.inner.map_as_ref(|inner| format!("{:?}", inner))
    }

    pub fn __richcmp__(
        &self,
        py: Python,
        rhs: &Py_SoftState_Ref,
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

    pub fn get_raft_state(&self) -> PyResult<Py_StateRole> {
        self.inner.map_as_ref(|inner| inner.raft_state.into())
    }

    pub fn set_raft_state(&mut self, rs: &Py_StateRole) -> PyResult<()> {
        self.inner.map_as_mut(|inner| inner.raft_state = rs.0)
    }
}
