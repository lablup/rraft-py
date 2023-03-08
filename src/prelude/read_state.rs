use pyo3::{prelude::*, pyclass::CompareOp, types::PyList};

use raft::ReadState;

use utils::reference::RustRef;

#[derive(Clone)]
#[pyclass(name = "ReadState_Owner")]
pub struct Py_ReadState_Owner {
    pub inner: ReadState,
}

#[derive(Clone)]
#[pyclass(name = "ReadState_Ref")]
pub struct Py_ReadState_Ref {
    pub inner: RustRef<ReadState>,
}

#[derive(FromPyObject)]
pub enum Py_ReadState_Mut<'p> {
    Owned(PyRefMut<'p, Py_ReadState_Owner>),
    RefMut(Py_ReadState_Ref),
}

impl Into<ReadState> for Py_ReadState_Mut<'_> {
    fn into(self) -> ReadState {
        match self {
            Py_ReadState_Mut::Owned(x) => x.inner.clone(),
            Py_ReadState_Mut::RefMut(mut x) => x.inner.map_as_mut(|x| x.clone()).unwrap(),
        }
    }
}

impl Into<ReadState> for &mut Py_ReadState_Mut<'_> {
    fn into(self) -> ReadState {
        match self {
            Py_ReadState_Mut::Owned(x) => x.inner.clone(),
            Py_ReadState_Mut::RefMut(x) => x.inner.map_as_mut(|x| x.clone()).unwrap(),
        }
    }
}

#[pymethods]
impl Py_ReadState_Owner {
    #[new]
    pub fn new() -> Self {
        Py_ReadState_Owner {
            inner: ReadState::default(),
        }
    }

    pub fn make_ref(&mut self) -> Py_ReadState_Ref {
        Py_ReadState_Ref {
            inner: RustRef::new(&mut self.inner),
        }
    }

    pub fn clone(&self) -> Py_ReadState_Owner {
        Py_ReadState_Owner {
            inner: self.inner.clone(),
        }
    }

    pub fn __repr__(&self) -> String {
        format!("{:?}", self.inner)
    }

    pub fn __richcmp__(&self, rhs: Py_ReadState_Mut, op: CompareOp) -> bool {
        let rhs: ReadState = rhs.into();

        match op {
            CompareOp::Eq => self.inner == rhs,
            CompareOp::Ne => self.inner != rhs,
            _ => panic!("Undefined operator"),
        }
    }
}

#[pymethods]
impl Py_ReadState_Ref {
    pub fn __repr__(&self) -> PyResult<String> {
        self.inner.map_as_ref(|inner| format!("{:?}", inner))
    }

    pub fn __richcmp__(&self, rhs: Py_ReadState_Mut, op: CompareOp) -> PyResult<bool> {
        self.inner.map_as_ref(|inner| {
            let rhs: ReadState = rhs.into();

            match op {
                CompareOp::Eq => inner == &rhs,
                CompareOp::Ne => inner != &rhs,
                _ => panic!("Undefined operator"),
            }
        })
    }

    pub fn clone(&self) -> Py_ReadState_Owner {
        Py_ReadState_Owner {
            inner: self.inner.map_as_ref(|x| x.clone()).unwrap(),
        }
    }

    pub fn get_index(&self) -> PyResult<u64> {
        self.inner.map_as_ref(|inner| inner.index)
    }

    pub fn set_index(&mut self, idx: u64) -> PyResult<()> {
        self.inner.map_as_mut(|inner| inner.index = idx)
    }

    pub fn get_request_ctx(&self, py: Python) -> PyResult<PyObject> {
        self.inner
            .map_as_ref(|inner| inner.request_ctx.to_object(py))
    }

    pub fn set_request_ctx(&mut self, request_ctx: &PyList) -> PyResult<()> {
        self.inner
            .map_as_mut(|inner| inner.request_ctx = request_ctx.extract().unwrap())
    }
}
