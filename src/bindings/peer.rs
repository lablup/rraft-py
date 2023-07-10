use pyo3::{intern, prelude::*, types::PyBytes};

use crate::utils::reference::{RefMutContainer, RefMutOwner};
use raft::raw_node::Peer;

#[pyclass(name = "Peer")]
pub struct PyPeer {
    pub inner: RefMutOwner<Peer>,
}

#[pyclass(name = "PeerRef")]
pub struct PyPeerRef {
    pub inner: RefMutContainer<Peer>,
}

#[pymethods]
impl PyPeer {
    #[new]
    pub fn new() -> Self {
        PyPeer {
            inner: RefMutOwner::new(Peer::default()),
        }
    }

    pub fn make_ref(&mut self) -> PyPeerRef {
        PyPeerRef {
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
impl PyPeerRef {
    pub fn __repr__(&self) -> PyResult<String> {
        self.inner.map_as_ref(|inner| format!("{:?}", inner))
    }

    pub fn get_id(&self) -> PyResult<u64> {
        self.inner.map_as_ref(|inner| inner.id)
    }

    pub fn set_id(&mut self, id: u64) -> PyResult<()> {
        self.inner.map_as_mut(|inner| inner.id = id)
    }

    pub fn get_context(&mut self, py: Python) -> PyResult<Option<Py<PyBytes>>> {
        self.inner.map_as_mut(|inner| {
            inner
                .context
                .as_ref()
                .map(|context| PyBytes::new(py, context.as_slice()).into())
        })
    }

    pub fn set_context(&mut self, _context: &PyBytes, _py: Python) -> PyResult<()> {
        todo!()
    }
}
