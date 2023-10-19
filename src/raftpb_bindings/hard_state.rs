use prost::Message as ProstMessage;
use protobuf::Message as PbMessage;
use pyo3::types::PyDict;
use pyo3::{intern, prelude::*, pyclass::CompareOp, types::PyBytes};

use raft::eraftpb::HardState;

use crate::implement_type_conversion;
use crate::utils::{
    errors::to_pyresult,
    reference::{RefMutContainer, RefMutOwner},
};

#[derive(Clone)]
#[pyclass(name = "HardState")]
pub struct PyHardState {
    pub inner: RefMutOwner<HardState>,
}

#[derive(Clone)]
#[pyclass(name = "HardStateRef")]
pub struct PyHardStateRef {
    pub inner: RefMutContainer<HardState>,
}

#[derive(FromPyObject)]
pub enum PyHardStateMut<'p> {
    Owned(PyRefMut<'p, PyHardState>),
    RefMut(PyHardStateRef),
}

implement_type_conversion!(HardState, PyHardStateMut);

#[pymethods]
impl PyHardState {
    #[new]
    pub fn new() -> Self {
        PyHardState {
            inner: RefMutOwner::new(HardState::new()),
        }
    }

    #[staticmethod]
    pub fn default() -> Self {
        PyHardState {
            inner: RefMutOwner::new(HardState::default()),
        }
    }

    #[staticmethod]
    pub fn decode(v: &[u8]) -> PyResult<PyHardState> {
        Ok(PyHardState {
            inner: RefMutOwner::new(to_pyresult(ProstMessage::decode(v))?),
        })
    }

    pub fn make_ref(&mut self) -> PyHardStateRef {
        PyHardStateRef {
            inner: RefMutContainer::new(&mut self.inner),
        }
    }

    pub fn __repr__(&mut self) -> String {
        format!("{:?}", self.inner.inner)
    }

    pub fn __richcmp__(&self, py: Python, rhs: PyHardStateMut, op: CompareOp) -> PyObject {
        let rhs: HardState = rhs.into();

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
impl PyHardStateRef {
    pub fn __repr__(&self) -> PyResult<String> {
        self.inner.map_as_ref(|inner| format!("{:?}", inner))
    }

    pub fn __richcmp__(
        &self,
        py: Python,
        rhs: PyHardStateMut,
        op: CompareOp,
    ) -> PyResult<PyObject> {
        self.inner.map_as_ref(|inner| {
            let rhs: HardState = rhs.into();

            match op {
                CompareOp::Eq => (inner == &rhs).into_py(py),
                CompareOp::Ne => (inner != &rhs).into_py(py),
                _ => py.NotImplemented(),
            }
        })
    }

    pub fn to_dict(&self, py: Python) -> PyResult<PyObject> {
        self.inner.map_as_ref(|inner| {
            let res = PyDict::new(py);
            res.set_item("term", inner.get_term()).unwrap();
            res.set_item("commit", inner.get_commit()).unwrap();
            res.set_item("vote", inner.get_vote()).unwrap();
            res.into_py(py)
        })
    }

    pub fn clone(&self) -> PyResult<PyHardState> {
        Ok(PyHardState {
            inner: RefMutOwner::new(self.inner.map_as_ref(|x| x.clone())?),
        })
    }

    pub fn encode(&self, py: Python) -> PyResult<PyObject> {
        self.inner
            .map_as_ref(|inner| PyBytes::new(py, inner.encode_to_vec().as_slice()).into_py(py))
    }

    pub fn get_commit(&self) -> PyResult<u64> {
        self.inner.map_as_ref(|inner| inner.get_commit())
    }

    pub fn set_commit(&mut self, v: u64) -> PyResult<()> {
        self.inner.map_as_mut(|inner| inner.set_commit(v))
    }

    pub fn clear_commit(&mut self) -> PyResult<()> {
        self.inner.map_as_mut(|inner| inner.clear_commit())
    }

    pub fn get_term(&self) -> PyResult<u64> {
        self.inner.map_as_ref(|inner| inner.get_term())
    }

    pub fn set_term(&mut self, v: u64) -> PyResult<()> {
        self.inner.map_as_mut(|inner| inner.set_term(v))
    }

    pub fn clear_term(&mut self) -> PyResult<()> {
        self.inner.map_as_mut(|inner| inner.clear_term())
    }

    pub fn get_vote(&self) -> PyResult<u64> {
        self.inner.map_as_ref(|inner| inner.get_vote())
    }

    pub fn set_vote(&mut self, v: u64) -> PyResult<()> {
        self.inner.map_as_mut(|inner| inner.set_vote(v))
    }

    pub fn clear_vote(&mut self) -> PyResult<()> {
        self.inner.map_as_mut(|inner| inner.clear_vote())
    }
}
