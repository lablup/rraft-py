use pyo3::{intern, prelude::*, pyclass::CompareOp, types::PyBytes};

use crate::implement_type_conversion;
use crate::utils::reference::{RefMutContainer, RefMutOwner};
use raft::ReadState;

#[derive(Clone)]
#[pyclass(name = "ReadState")]
pub struct PyReadState {
    pub inner: RefMutOwner<ReadState>,
}

#[derive(Clone)]
#[pyclass(name = "ReadStateRef")]
pub struct PyReadStateRef {
    pub inner: RefMutContainer<ReadState>,
}

#[derive(FromPyObject)]
pub enum PyReadStateMut<'p> {
    Owned(PyRefMut<'p, PyReadState>),
    RefMut(PyReadStateRef),
}

implement_type_conversion!(ReadState, PyReadStateMut);

#[pymethods]
impl PyReadState {
    #[staticmethod]
    pub fn default() -> Self {
        PyReadState {
            inner: RefMutOwner::new(ReadState::default()),
        }
    }

    pub fn make_ref(&mut self) -> PyReadStateRef {
        PyReadStateRef {
            inner: RefMutContainer::new(&mut self.inner),
        }
    }

    pub fn clone(&self) -> PyReadState {
        PyReadState {
            inner: self.inner.clone(),
        }
    }

    pub fn __repr__(&self) -> String {
        format!("{:?}", self.inner.inner)
    }

    pub fn __richcmp__(&self, py: Python, rhs: PyReadStateMut, op: CompareOp) -> PyObject {
        let rhs: ReadState = rhs.into();

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
impl PyReadStateRef {
    pub fn __repr__(&self) -> PyResult<String> {
        self.inner.map_as_ref(|inner| format!("{:?}", inner))
    }

    pub fn __richcmp__(
        &self,
        py: Python,
        rhs: PyReadStateMut,
        op: CompareOp,
    ) -> PyResult<PyObject> {
        self.inner.map_as_ref(|inner| {
            let rhs: ReadState = rhs.into();

            match op {
                CompareOp::Eq => (inner == &rhs).into_py(py),
                CompareOp::Ne => (inner != &rhs).into_py(py),
                _ => py.NotImplemented(),
            }
        })
    }

    pub fn clone(&self) -> PyResult<PyReadState> {
        Ok(PyReadState {
            inner: RefMutOwner::new(self.inner.map_as_ref(|x| x.clone())?),
        })
    }

    pub fn get_index(&self) -> PyResult<u64> {
        self.inner.map_as_ref(|inner| inner.index)
    }

    pub fn set_index(&mut self, idx: u64) -> PyResult<()> {
        self.inner.map_as_mut(|inner| inner.index = idx)
    }

    pub fn get_request_ctx(&self, py: Python) -> PyResult<PyObject> {
        self.inner
            .map_as_ref(|inner| PyBytes::new(py, inner.request_ctx.as_slice()).to_object(py))
    }

    pub fn set_request_ctx(&mut self, request_ctx: &PyAny) -> PyResult<()> {
        let v = request_ctx.extract()?;
        self.inner.map_as_mut(|inner| inner.request_ctx = v)
    }
}
