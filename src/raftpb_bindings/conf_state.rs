use prost::Message as ProstMessage;
use protobuf::Message as PbMessage;
use pyo3::intern;
use pyo3::pyclass::CompareOp;
use pyo3::types::{PyBytes, PyDict};
use pyo3::{prelude::*, types::PyList};

use raft::eraftpb::ConfState;

use crate::implement_type_conversion;
use crate::utils::errors::{runtime_error, to_pyresult};
use crate::utils::reference::{RefMutContainer, RefMutOwner};

#[derive(Clone)]
#[pyclass(name = "ConfState")]
pub struct PyConfState {
    pub inner: RefMutOwner<ConfState>,
}

#[derive(Clone)]
#[pyclass(name = "ConfStateRef")]
pub struct PyConfStateRef {
    pub inner: RefMutContainer<ConfState>,
}

#[derive(FromPyObject)]
pub enum PyConfStateMut<'p> {
    Owned(PyRefMut<'p, PyConfState>),
    RefMut(PyConfStateRef),
}

implement_type_conversion!(ConfState, PyConfStateMut);

#[pymethods]
impl PyConfState {
    #[new]
    pub fn new(voters: Option<&PyList>, learners: Option<&PyList>) -> PyResult<Self> {
        if voters.and(learners).is_none() {
            Ok(PyConfState {
                inner: RefMutOwner::new(ConfState::new()),
            })
        } else if voters.or(learners).is_none() {
            Err(runtime_error(
                "voters and learners both values should or should not be given.",
            ))
        } else {
            let voters = voters.unwrap().extract::<Vec<u64>>()?;
            let learners = learners.unwrap().extract::<Vec<u64>>()?;
            Ok(PyConfState {
                inner: RefMutOwner::new(ConfState::from((voters, learners))),
            })
        }
    }

    #[staticmethod]
    pub fn default() -> Self {
        PyConfState {
            inner: RefMutOwner::new(ConfState::default()),
        }
    }

    #[staticmethod]
    pub fn decode(v: &[u8]) -> PyResult<PyConfState> {
        Ok(PyConfState {
            inner: RefMutOwner::new(to_pyresult(ProstMessage::decode(v))?),
        })
    }

    pub fn make_ref(&mut self) -> PyConfStateRef {
        PyConfStateRef {
            inner: RefMutContainer::new(&mut self.inner),
        }
    }

    pub fn __repr__(&self) -> String {
        format!("{:?}", self.inner.inner)
    }

    pub fn __richcmp__(&self, py: Python, rhs: PyConfStateMut, op: CompareOp) -> PyObject {
        let rhs: ConfState = rhs.into();

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
impl PyConfStateRef {
    pub fn __repr__(&self) -> PyResult<String> {
        self.inner.map_as_ref(|inner| format!("{:?}", inner))
    }

    pub fn __richcmp__(
        &self,
        py: Python,
        rhs: PyConfStateMut,
        op: CompareOp,
    ) -> PyResult<PyObject> {
        self.inner.map_as_ref(|inner| {
            let rhs: ConfState = rhs.into();

            match op {
                CompareOp::Eq => (inner == &rhs).into_py(py),
                CompareOp::Ne => (inner != &rhs).into_py(py),
                _ => py.NotImplemented(),
            }
        })
    }

    pub fn to_dict(&self, py: Python) -> PyResult<PyObject> {
        let voters = self.get_voters(py)?;
        let voters_outgoing = self.get_voters_outgoing(py)?;
        let learners = self.get_learners(py)?;
        let learners_next = self.get_learners_next(py)?;
        let auto_leave = self.get_auto_leave()?;

        self.inner.map_as_ref(|_inner| {
            let res = PyDict::new(py);
            res.set_item("voters", voters).unwrap();
            res.set_item("voters_outgoing", voters_outgoing).unwrap();
            res.set_item("learners", learners).unwrap();
            res.set_item("learners_next", learners_next).unwrap();
            res.set_item("auto_leave", auto_leave).unwrap();
            res.into_py(py)
        })
    }

    pub fn clone(&self) -> PyResult<PyConfState> {
        Ok(PyConfState {
            inner: RefMutOwner::new(self.inner.map_as_ref(|inner| inner.clone())?),
        })
    }

    pub fn encode(&self, py: Python) -> PyResult<PyObject> {
        self.inner
            .map_as_ref(|inner| PyBytes::new(py, inner.encode_to_vec().as_slice()).into_py(py))
    }

    pub fn get_auto_leave(&self) -> PyResult<bool> {
        self.inner.map_as_ref(|inner| inner.get_auto_leave())
    }

    pub fn set_auto_leave(&mut self, v: bool) -> PyResult<()> {
        self.inner.map_as_mut(|inner| inner.set_auto_leave(v))
    }

    pub fn clear_auto_leave(&mut self) -> PyResult<()> {
        self.inner.map_as_mut(|inner| inner.clear_auto_leave())
    }

    pub fn get_voters(&self, py: Python) -> PyResult<PyObject> {
        self.inner.map_as_ref(|inner| {
            inner
                .get_voters()
                .iter()
                .map(|x| x.into_py(py))
                .collect::<Vec<_>>()
                .into_py(py)
        })
    }

    pub fn set_voters(&mut self, list: &PyList) -> PyResult<()> {
        let v = list.extract::<Vec<u64>>()?;
        self.inner.map_as_mut(|inner| inner.set_voters(v))
    }

    pub fn clear_voters(&mut self) -> PyResult<()> {
        self.inner.map_as_mut(|inner| inner.clear_voters())
    }

    pub fn get_voters_outgoing(&self, py: Python) -> PyResult<PyObject> {
        self.inner.map_as_ref(|inner| {
            inner
                .get_voters_outgoing()
                .iter()
                .map(|x| x.into_py(py))
                .collect::<Vec<_>>()
                .into_py(py)
        })
    }

    pub fn set_voters_outgoing(&mut self, list: &PyList) -> PyResult<()> {
        let v = list.extract::<Vec<u64>>()?;
        self.inner.map_as_mut(|inner| inner.set_voters_outgoing(v))
    }

    pub fn clear_voters_outgoing(&mut self) -> PyResult<()> {
        self.inner.map_as_mut(|inner| inner.clear_voters_outgoing())
    }

    pub fn get_learners(&self, py: Python) -> PyResult<PyObject> {
        self.inner.map_as_ref(|inner| {
            inner
                .get_learners()
                .iter()
                .map(|x| x.into_py(py))
                .collect::<Vec<_>>()
                .into_py(py)
        })
    }

    pub fn set_learners(&mut self, list: &PyList) -> PyResult<()> {
        let v = list.extract::<Vec<u64>>()?;
        self.inner.map_as_mut(|inner| inner.set_learners(v))
    }

    pub fn clear_learners(&mut self) -> PyResult<()> {
        self.inner.map_as_mut(|inner| inner.clear_learners())
    }

    pub fn get_learners_next(&self, py: Python) -> PyResult<PyObject> {
        self.inner.map_as_ref(|inner| {
            inner
                .get_learners_next()
                .iter()
                .map(|x| x.into_py(py))
                .collect::<Vec<_>>()
                .into_py(py)
        })
    }

    pub fn set_learners_next(&mut self, list: &PyList) -> PyResult<()> {
        let v = list.extract::<Vec<u64>>()?;
        self.inner.map_as_mut(|inner| inner.set_learners_next(v))
    }

    pub fn clear_learners_next(&mut self) -> PyResult<()> {
        self.inner.map_as_mut(|inner| inner.clear_learners_next())
    }
}
