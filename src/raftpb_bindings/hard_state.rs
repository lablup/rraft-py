use prost::Message as ProstMessage;
use protobuf::Message as PbMessage;
use pyo3::{intern, prelude::*, pyclass::CompareOp, types::PyBytes};

use raft::eraftpb::HardState;

use utils::{
    errors::to_pyresult,
    implement_type_conversion,
    reference::{RefMutOwner, RustRef},
};

#[derive(Clone)]
#[pyclass(name = "HardState")]
pub struct Py_HardState {
    pub inner: RefMutOwner<HardState>,
}

#[derive(Clone)]
#[pyclass(name = "HardState_Ref")]
pub struct Py_HardState_Ref {
    pub inner: RustRef<HardState>,
}

#[derive(FromPyObject)]
pub enum Py_HardState_Mut<'p> {
    Owned(PyRefMut<'p, Py_HardState>),
    RefMut(Py_HardState_Ref),
}

implement_type_conversion!(HardState, Py_HardState_Mut);

#[pymethods]
impl Py_HardState {
    #[new]
    pub fn new() -> Self {
        Py_HardState {
            inner: RefMutOwner::new(HardState::new()),
        }
    }

    #[staticmethod]
    pub fn default() -> Self {
        Py_HardState {
            inner: RefMutOwner::new(HardState::default()),
        }
    }

    #[staticmethod]
    pub fn decode(v: &[u8]) -> PyResult<Py_HardState> {
        Ok(Py_HardState {
            inner: RefMutOwner::new(to_pyresult(ProstMessage::decode(v))?),
        })
    }

    pub fn make_ref(&mut self) -> Py_HardState_Ref {
        Py_HardState_Ref {
            inner: RustRef::new(&mut self.inner),
        }
    }

    pub fn __repr__(&mut self) -> String {
        format!("{:?}", self.inner.inner)
    }

    pub fn __richcmp__(&self, py: Python, rhs: Py_HardState_Mut, op: CompareOp) -> PyObject {
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
impl Py_HardState_Ref {
    pub fn __repr__(&self) -> PyResult<String> {
        self.inner.map_as_ref(|inner| format!("{:?}", inner))
    }

    pub fn __richcmp__(
        &self,
        py: Python,
        rhs: Py_HardState_Mut,
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

    pub fn clone(&self) -> PyResult<Py_HardState> {
        Ok(Py_HardState {
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
