use prost::Message as ProstMessage;
use protobuf::Message as PbMessage;
use pyo3::{intern, prelude::*, pyclass::CompareOp, types::PyBytes};
use crate::implement_type_conversion;
use crate::utils::{
    errors::to_pyresult,
    reference::{RefMutContainer, RefMutOwner},
};

use super::conf_change_type::Py_ConfChangeType;

use raft::eraftpb::ConfChangeSingle;

#[derive(Clone)]
#[pyclass(name = "ConfChangeSingle")]
pub struct Py_ConfChangeSingle {
    pub inner: RefMutOwner<ConfChangeSingle>,
}

#[derive(Clone)]
#[pyclass(name = "ConfChangeSingle_Ref")]
pub struct Py_ConfChangeSingle_Ref {
    pub inner: RefMutContainer<ConfChangeSingle>,
}

#[derive(FromPyObject)]
pub enum Py_ConfChangeSingle_Mut<'p> {
    Owned(PyRefMut<'p, Py_ConfChangeSingle>),
    RefMut(Py_ConfChangeSingle_Ref),
}

implement_type_conversion!(ConfChangeSingle, Py_ConfChangeSingle_Mut);

#[pymethods]
impl Py_ConfChangeSingle {
    #[new]
    pub fn new() -> Self {
        Py_ConfChangeSingle {
            inner: RefMutOwner::new(ConfChangeSingle::new()),
        }
    }

    #[staticmethod]
    pub fn default() -> Self {
        Py_ConfChangeSingle {
            inner: RefMutOwner::new(ConfChangeSingle::default()),
        }
    }

    #[staticmethod]
    pub fn decode(v: &[u8]) -> PyResult<Py_ConfChangeSingle> {
        Ok(Py_ConfChangeSingle {
            inner: RefMutOwner::new(to_pyresult(ProstMessage::decode(v))?),
        })
    }

    pub fn make_ref(&mut self) -> Py_ConfChangeSingle_Ref {
        Py_ConfChangeSingle_Ref {
            inner: RefMutContainer::new(&mut self.inner),
        }
    }

    pub fn __repr__(&self) -> String {
        format!("{:?}", self.inner.inner)
    }

    pub fn __richcmp__(&self, py: Python, rhs: Py_ConfChangeSingle_Mut, op: CompareOp) -> PyObject {
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
impl Py_ConfChangeSingle_Ref {
    pub fn __repr__(&self) -> PyResult<String> {
        self.inner.map_as_ref(|inner| format!("{:?}", inner))
    }

    pub fn __richcmp__(
        &self,
        py: Python,
        rhs: Py_ConfChangeSingle_Mut,
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

    pub fn clone(&self) -> PyResult<Py_ConfChangeSingle> {
        Ok(Py_ConfChangeSingle {
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

    pub fn get_change_type(&self) -> PyResult<Py_ConfChangeType> {
        self.inner
            .map_as_ref(|inner| Py_ConfChangeType(inner.get_change_type()))
    }

    pub fn set_change_type(&mut self, v: &Py_ConfChangeType) -> PyResult<()> {
        self.inner.map_as_mut(|inner| inner.set_change_type(v.0))
    }

    pub fn clear_change_type(&mut self) -> PyResult<()> {
        self.inner.map_as_mut(|inner| inner.clear_change_type())
    }
}
