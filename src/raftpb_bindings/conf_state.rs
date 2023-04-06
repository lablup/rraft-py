use prost::Message as ProstMessage;
use protobuf::Message as PbMessage;
use pyo3::pyclass::CompareOp;
use pyo3::{prelude::*, types::PyList};

use raft::eraftpb::ConfState;

use utils::errors::{runtime_error, to_pyresult};
use utils::reference::RustRef;

#[derive(Clone)]
#[pyclass(name = "ConfState_Owner")]
pub struct Py_ConfState_Owner {
    pub inner: ConfState,
}

#[derive(Clone)]
#[pyclass(name = "ConfState_Ref")]
pub struct Py_ConfState_Ref {
    pub inner: RustRef<ConfState>,
}

#[derive(FromPyObject)]
pub enum Py_ConfState_Mut<'p> {
    Owned(PyRefMut<'p, Py_ConfState_Owner>),
    RefMut(Py_ConfState_Ref),
}

impl From<Py_ConfState_Mut<'_>> for ConfState {
    fn from(val: Py_ConfState_Mut<'_>) -> Self {
        match val {
            Py_ConfState_Mut::Owned(x) => x.inner.clone(),
            Py_ConfState_Mut::RefMut(mut x) => x.inner.map_as_mut(|x| x.clone()).unwrap(),
        }
    }
}

impl From<&mut Py_ConfState_Mut<'_>> for ConfState {
    fn from(val: &mut Py_ConfState_Mut<'_>) -> Self {
        match val {
            Py_ConfState_Mut::Owned(x) => x.inner.clone(),
            Py_ConfState_Mut::RefMut(x) => x.inner.map_as_mut(|x| x.clone()).unwrap(),
        }
    }
}

#[pymethods]
impl Py_ConfState_Owner {
    #[new]
    pub fn new(voters: Option<&PyList>, learners: Option<&PyList>) -> PyResult<Self> {
        if voters.and(learners).is_none() {
            Ok(Py_ConfState_Owner {
                inner: ConfState::new(),
            })
        } else if voters.or(learners).is_none() {
            Err(runtime_error(
                "voters and learners both values should or should not be given.",
            ))
        } else {
            let voters = voters.unwrap().extract::<Vec<u64>>().unwrap();
            let learners = learners.unwrap().extract::<Vec<u64>>().unwrap();
            Ok(Py_ConfState_Owner {
                inner: ConfState::from((voters, learners)),
            })
        }
    }

    #[staticmethod]
    pub fn default() -> Self {
        Py_ConfState_Owner {
            inner: ConfState::default(),
        }
    }

    #[staticmethod]
    pub fn decode(v: &[u8]) -> PyResult<Py_ConfState_Owner> {
        Ok(Py_ConfState_Owner {
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

    pub fn __richcmp__(&self, py: Python<'_>, rhs: Py_ConfState_Mut, op: CompareOp) -> PyObject {
        let rhs: ConfState = rhs.into();

        match op {
            CompareOp::Eq => (self.inner == rhs).into_py(py),
            CompareOp::Ne => (self.inner != rhs).into_py(py),
            _ => py.NotImplemented(),
        }
    }

    fn __getattr__(this: PyObject, py: Python<'_>, attr: &str) -> PyResult<PyObject> {
        let reference = this.call_method0(py, "make_ref")?;
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
        py: Python<'_>,
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

    pub fn clone(&self) -> PyResult<Py_ConfState_Owner> {
        Ok(Py_ConfState_Owner {
            inner: self.inner.map_as_ref(|inner| inner.clone())?,
        })
    }

    pub fn encode(&self, py: Python) -> PyResult<PyObject> {
        self.inner
            .map_as_ref(|inner| inner.encode_to_vec().into_py(py))
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
