use pyo3::{prelude::*, types::PyList};

use raft::raw_node::Peer;

use utils::reference::RustRef;

#[pyclass(name = "Peer_Owner")]
pub struct Py_Peer_Owner {
    pub inner: Peer,
}

#[pyclass(name = "Peer_Ref")]
pub struct Py_Peer_Ref {
    pub inner: RustRef<Peer>,
}

#[pymethods]
impl Py_Peer_Owner {
    #[new]
    pub fn new() -> Self {
        Py_Peer_Owner {
            inner: Peer::default(),
        }
    }

    pub fn make_ref(&mut self) -> Py_Peer_Ref {
        Py_Peer_Ref {
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
impl Py_Peer_Ref {
    pub fn __repr__(&self) -> PyResult<String> {
        self.inner.map_as_ref(|inner| format!("{:?}", inner))
    }

    pub fn get_id(&self) -> PyResult<u64> {
        self.inner.map_as_ref(|inner| inner.id)
    }

    pub fn set_id(&mut self, id: u64) -> PyResult<()> {
        self.inner.map_as_mut(|inner| inner.id = id)
    }

    pub fn get_context(&mut self, py: Python) -> PyResult<Option<Py<PyList>>> {
        self.inner.map_as_mut(|inner| match &inner.context {
            Some(context) => Some(PyList::new(py, context.as_slice()).into()),
            None => None,
        })
    }

    pub fn set_context(&mut self, context: &PyList, py: Python) -> PyResult<()> {
        todo!()
    }
}
