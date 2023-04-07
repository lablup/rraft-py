use pyo3::{intern, prelude::*, pyclass::CompareOp, types::PyBytes};

use raft::ReadState;

use utils::reference::RustRef;

#[derive(Clone)]
#[pyclass(name = "ReadState")]
pub struct Py_ReadState {
    pub inner: ReadState,
}

#[derive(Clone)]
#[pyclass(name = "ReadState_Ref")]
pub struct Py_ReadState_Ref {
    pub inner: RustRef<ReadState>,
}

#[derive(FromPyObject)]
pub enum Py_ReadState_Mut<'p> {
    Owned(PyRefMut<'p, Py_ReadState>),
    RefMut(Py_ReadState_Ref),
}

impl From<Py_ReadState_Mut<'_>> for ReadState {
    fn from(val: Py_ReadState_Mut<'_>) -> Self {
        match val {
            Py_ReadState_Mut::Owned(x) => x.inner.clone(),
            Py_ReadState_Mut::RefMut(mut x) => x.inner.map_as_mut(|x| x.clone()).unwrap(),
        }
    }
}

impl From<&mut Py_ReadState_Mut<'_>> for ReadState {
    fn from(val: &mut Py_ReadState_Mut<'_>) -> Self {
        match val {
            Py_ReadState_Mut::Owned(x) => x.inner.clone(),
            Py_ReadState_Mut::RefMut(x) => x.inner.map_as_mut(|x| x.clone()).unwrap(),
        }
    }
}

#[pymethods]
impl Py_ReadState {
    #[staticmethod]
    pub fn default() -> Self {
        Py_ReadState {
            inner: ReadState::default(),
        }
    }

    pub fn make_ref(&mut self) -> Py_ReadState_Ref {
        Py_ReadState_Ref {
            inner: RustRef::new(&mut self.inner),
        }
    }

    pub fn clone(&self) -> Py_ReadState {
        Py_ReadState {
            inner: self.inner.clone(),
        }
    }

    pub fn __repr__(&self) -> String {
        format!("{:?}", self.inner)
    }

    pub fn __richcmp__(&self, py: Python<'_>, rhs: Py_ReadState_Mut, op: CompareOp) -> PyObject {
        let rhs: ReadState = rhs.into();

        match op {
            CompareOp::Eq => (self.inner == rhs).into_py(py),
            CompareOp::Ne => (self.inner != rhs).into_py(py),
            _ => py.NotImplemented(),
        }
    }

    fn __getattr__(this: PyObject, py: Python<'_>, attr: &str) -> PyResult<PyObject> {
        let reference = this.call_method0(py, intern!(py, "make_ref"))?;
        reference.getattr(py, attr)
    }
}

#[pymethods]
impl Py_ReadState_Ref {
    pub fn __repr__(&self) -> PyResult<String> {
        self.inner.map_as_ref(|inner| format!("{:?}", inner))
    }

    pub fn __richcmp__(
        &self,
        py: Python<'_>,
        rhs: Py_ReadState_Mut,
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

    pub fn clone(&self) -> PyResult<Py_ReadState> {
        Ok(Py_ReadState {
            inner: self.inner.map_as_ref(|x| x.clone())?,
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
