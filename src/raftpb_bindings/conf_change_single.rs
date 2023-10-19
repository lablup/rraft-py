use crate::implement_type_conversion;
use crate::utils::{
    errors::to_pyresult,
    reference::{RefMutContainer, RefMutOwner},
};
use prost::Message as ProstMessage;
use protobuf::Message as PbMessage;
use pyo3::types::PyDict;
use pyo3::{intern, prelude::*, pyclass::CompareOp, types::PyBytes};

use super::conf_change_type::PyConfChangeType;

use raft::eraftpb::ConfChangeSingle;

#[derive(Clone)]
#[pyclass(name = "ConfChangeSingle")]
pub struct PyConfChangeSingle {
    pub inner: RefMutOwner<ConfChangeSingle>,
}

#[derive(Clone)]
#[pyclass(name = "ConfChangeSingleRef")]
pub struct PyConfChangeSingleRef {
    pub inner: RefMutContainer<ConfChangeSingle>,
}

#[derive(FromPyObject)]
pub enum PyConfChangeSingleMut<'p> {
    Owned(PyRefMut<'p, PyConfChangeSingle>),
    RefMut(PyConfChangeSingleRef),
}

implement_type_conversion!(ConfChangeSingle, PyConfChangeSingleMut);

#[pymethods]
impl PyConfChangeSingle {
    #[new]
    pub fn new() -> Self {
        PyConfChangeSingle {
            inner: RefMutOwner::new(ConfChangeSingle::new()),
        }
    }

    #[staticmethod]
    pub fn default() -> Self {
        PyConfChangeSingle {
            inner: RefMutOwner::new(ConfChangeSingle::default()),
        }
    }

    #[staticmethod]
    pub fn decode(v: &[u8]) -> PyResult<PyConfChangeSingle> {
        Ok(PyConfChangeSingle {
            inner: RefMutOwner::new(to_pyresult(ProstMessage::decode(v))?),
        })
    }

    pub fn make_ref(&mut self) -> PyConfChangeSingleRef {
        PyConfChangeSingleRef {
            inner: RefMutContainer::new(&mut self.inner),
        }
    }

    pub fn __repr__(&self) -> String {
        format!("{:?}", self.inner.inner)
    }

    pub fn __richcmp__(&self, py: Python, rhs: PyConfChangeSingleMut, op: CompareOp) -> PyObject {
        let rhs: ConfChangeSingle = rhs.into();

        match op {
            CompareOp::Eq => (self.inner.inner == rhs).into_py(py),
            CompareOp::Ne => (self.inner.inner != rhs).into_py(py),
            _ => py.NotImplemented(),
        }
    }

    fn __getattr__(this: PyObject, py: Python, attr: &str) -> PyResult<PyObject> {
        let reference = this.call_method0(py, intern!(py, "make_ref"))?;
        reference.getattr(py, attr)
    }
}

#[pymethods]
impl PyConfChangeSingleRef {
    pub fn __repr__(&self) -> PyResult<String> {
        self.inner.map_as_ref(|inner| format!("{:?}", inner))
    }

    pub fn __richcmp__(
        &self,
        py: Python,
        rhs: PyConfChangeSingleMut,
        op: CompareOp,
    ) -> PyResult<PyObject> {
        self.inner.map_as_ref(|inner| {
            let rhs: ConfChangeSingle = rhs.into();

            match op {
                CompareOp::Eq => (inner == &rhs).into_py(py),
                CompareOp::Ne => (inner != &rhs).into_py(py),
                _ => py.NotImplemented(),
            }
        })
    }

    pub fn to_dict(&mut self, py: Python) -> PyResult<PyObject> {
        let node_id = self.get_node_id()?;
        let change_type = self.get_change_type()?.__repr__();

        self.inner.map_as_ref(|_inner| {
            let res = PyDict::new(py);
            res.set_item("node_id", node_id).unwrap();
            res.set_item("change_type", change_type).unwrap();
            res.into_py(py)
        })
    }

    pub fn clone(&self) -> PyResult<PyConfChangeSingle> {
        Ok(PyConfChangeSingle {
            inner: RefMutOwner::new(self.inner.map_as_ref(|x| x.clone())?),
        })
    }

    pub fn encode(&self, py: Python) -> PyResult<PyObject> {
        self.inner
            .map_as_ref(|inner| PyBytes::new(py, inner.encode_to_vec().as_slice()).into_py(py))
    }

    pub fn get_node_id(&self) -> PyResult<u64> {
        self.inner.map_as_ref(|inner| inner.get_node_id())
    }

    pub fn set_node_id(&mut self, v: u64) -> PyResult<()> {
        self.inner.map_as_mut(|inner| inner.set_node_id(v))
    }

    pub fn clear_node_id(&mut self) -> PyResult<()> {
        self.inner.map_as_mut(|inner| inner.clear_node_id())
    }

    pub fn get_change_type(&self) -> PyResult<PyConfChangeType> {
        self.inner
            .map_as_ref(|inner| PyConfChangeType(inner.get_change_type()))
    }

    pub fn set_change_type(&mut self, v: &PyConfChangeType) -> PyResult<()> {
        self.inner.map_as_mut(|inner| inner.set_change_type(v.0))
    }

    pub fn clear_change_type(&mut self) -> PyResult<()> {
        self.inner.map_as_mut(|inner| inner.clear_change_type())
    }
}
