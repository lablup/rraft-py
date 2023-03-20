use pyo3::prelude::*;

use raft::SoftState;

use utils::reference::RustRef;

use super::state_role::Py_StateRole;

#[pyclass(name = "SoftState_Owner")]
pub struct Py_SoftState_Owner {
    pub inner: SoftState,
}

#[pyclass(name = "SoftState_Ref")]
pub struct Py_SoftState_Ref {
    pub inner: RustRef<SoftState>,
}

#[pymethods]
impl Py_SoftState_Owner {
    #[staticmethod]
    pub fn default() -> Self {
        Py_SoftState_Owner {
            inner: SoftState::default(),
        }
    }

    pub fn make_ref(&mut self) -> Py_SoftState_Ref {
        Py_SoftState_Ref {
            inner: RustRef::new(&mut self.inner),
        }
    }

    pub fn __repr__(&self) -> String {
        format!("{:?}", self.inner)
    }

    fn __getattr__(this: PyObject, py: Python<'_>, attr: &str) -> PyResult<PyObject> {
        let reference = this.call_method0(py, "make_ref")?;
        reference.getattr(py, attr)
    }
}

#[pymethods]
impl Py_SoftState_Ref {
    pub fn __repr__(&self) -> PyResult<String> {
        self.inner.map_as_ref(|inner| format!("{:?}", inner))
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
