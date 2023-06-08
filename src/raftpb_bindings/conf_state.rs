use prost::Message as ProstMessage;
use protobuf::Message as PbMessage;
use pyo3::intern;
use pyo3::pyclass::CompareOp;
use pyo3::types::PyBytes;
use pyo3::{prelude::*, types::PyList};

use raft::eraftpb::ConfState;

use utils::errors::{runtime_error, to_pyresult};
use utils::implement_type_conversion;
use utils::reference::RustRef;

#[derive(Clone)]
#[pyclass(name = "ConfState")]
pub struct Py_ConfState {
    pub inner: ConfState,
}

#[derive(Clone)]
#[pyclass(name = "ConfState_Ref")]
pub struct Py_ConfState_Ref {
    pub inner: RustRef<ConfState>,
}

#[derive(FromPyObject)]
pub enum Py_ConfState_Mut<'p> {
    Owned(PyRefMut<'p, Py_ConfState>),
    RefMut(Py_ConfState_Ref),
}

implement_type_conversion!(ConfState, Py_ConfState_Mut);

#[pymethods]
impl Py_ConfState {
    #[new]
    pub fn new(voters: Option<&PyList>, learners: Option<&PyList>) -> PyResult<Self> {
        if voters.and(learners).is_none() {
            Ok(Py_ConfState {
                inner: ConfState::new(),
            })
        } else if voters.or(learners).is_none() {
            Err(runtime_error(
                "voters and learners both values should or should not be given.",
            ))
        } else {
            let voters = voters.unwrap().extract::<Vec<u64>>().unwrap();
            let learners = learners.unwrap().extract::<Vec<u64>>().unwrap();
            Ok(Py_ConfState {
                inner: ConfState::from((voters, learners)),
            })
        }
    }

    #[staticmethod]
    pub fn default() -> Self {
        Py_ConfState {
            inner: ConfState::default(),
        }
    }

    #[staticmethod]
    pub fn decode(v: &[u8]) -> PyResult<Py_ConfState> {
        Ok(Py_ConfState {
            inner: to_pyresult(ProstMessage::decode(v))?,
        })
    }

    pub fn make_ref(&mut self) -> Py_ConfState_Ref {
        Py_ConfState_Ref {
            inner: RustRef::new(&mut self.inner),
        }
    }

    pub fn __repr__(&self) -> String {
        format!("{:?}", self.inner)
    }

    pub fn __richcmp__(&self, py: Python, rhs: Py_ConfState_Mut, op: CompareOp) -> PyObject {
        let rhs: ConfState = rhs.into();

        match op {
            CompareOp::Eq => (self.inner == rhs).into_py(py),
            CompareOp::Ne => (self.inner != rhs).into_py(py),
            _ => py.NotImplemented(),
        }
    }

    fn __getattr__(this: PyObject, py: Python, attr: &str) -> PyResult<PyObject> {
        let reference = this.call_method0(py, intern!(py, "make_ref"))?;
        reference.getattr(py, attr)
    }
}

#[pymethods]
impl Py_ConfState_Ref {
    pub fn __repr__(&self) -> PyResult<String> {
        self.inner.map_as_ref(|inner| format!("{:?}", inner))
    }

    pub fn __richcmp__(
        &self,
        py: Python,
        rhs: Py_ConfState_Mut,
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

    pub fn clone(&self) -> PyResult<Py_ConfState> {
        Ok(Py_ConfState {
            inner: self.inner.map_as_ref(|inner| inner.clone())?,
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
