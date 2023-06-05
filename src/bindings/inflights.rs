use pyo3::{intern, prelude::*, pyclass::CompareOp};

use raft::Inflights;

use utils::reference::RustRef;

#[derive(Clone)]
#[pyclass(name = "Inflights")]
pub struct Py_Inflights {
    pub inner: Inflights,
}

#[derive(Clone)]
#[pyclass(name = "Inflights_Ref")]
pub struct Py_Inflights_Ref {
    pub inner: RustRef<Inflights>,
}

#[derive(FromPyObject)]
pub enum Py_Inflights_Mut<'p> {
    Owned(PyRefMut<'p, Py_Inflights>),
    RefMut(Py_Inflights_Ref),
}

impl From<Py_Inflights_Mut<'_>> for Inflights {
    fn from(val: Py_Inflights_Mut<'_>) -> Self {
        match val {
            Py_Inflights_Mut::Owned(x) => x.inner.clone(),
            Py_Inflights_Mut::RefMut(mut x) => x.inner.map_as_mut(|x| x.clone()).unwrap(),
        }
    }
}

impl From<&mut Py_Inflights_Mut<'_>> for Inflights {
    fn from(val: &mut Py_Inflights_Mut<'_>) -> Self {
        match val {
            Py_Inflights_Mut::Owned(x) => x.inner.clone(),
            Py_Inflights_Mut::RefMut(x) => x.inner.map_as_mut(|x| x.clone()).unwrap(),
        }
    }
}

#[pymethods]
impl Py_Inflights {
    #[new]
    pub fn new(cap: usize) -> Self {
        Py_Inflights {
            inner: Inflights::new(cap),
        }
    }

    pub fn make_ref(&mut self) -> Py_Inflights_Ref {
        Py_Inflights_Ref {
            inner: RustRef::new(&mut self.inner),
        }
    }

    pub fn __repr__(&self) -> String {
        format!("{:?}", self.inner)
    }

    pub fn __richcmp__(&self, py: Python, rhs: Py_Inflights_Mut, op: CompareOp) -> PyObject {
        let rhs: Inflights = rhs.into();

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
impl Py_Inflights_Ref {
    pub fn __repr__(&self) -> PyResult<String> {
        self.inner.map_as_ref(|inner| format!("{:?}", inner))
    }

    pub fn __richcmp__(
        &self,
        py: Python,
        rhs: Py_Inflights_Mut,
        op: CompareOp,
    ) -> PyResult<PyObject> {
        self.inner.map_as_ref(|inner| {
            let rhs: Inflights = rhs.into();

            match op {
                CompareOp::Eq => (inner == &rhs).into_py(py),
                CompareOp::Ne => (inner != &rhs).into_py(py),
                _ => py.NotImplemented(),
            }
        })
    }

    pub fn clone(&self) -> PyResult<Py_Inflights> {
        Ok(Py_Inflights {
            inner: self.inner.map_as_ref(|inner| inner.clone())?,
        })
    }

    pub fn add(&mut self, inflight: u64) -> PyResult<()> {
        self.inner.map_as_mut(|inner| inner.add(inflight))
    }

    pub fn set_cap(&mut self, incoming_cap: usize) -> PyResult<()> {
        self.inner.map_as_mut(|inner| inner.set_cap(incoming_cap))
    }

    pub fn full(&self) -> PyResult<bool> {
        self.inner.map_as_ref(|inner| inner.full())
    }

    pub fn reset(&mut self) -> PyResult<()> {
        self.inner.map_as_mut(|inner| inner.reset())
    }

    pub fn free_to(&mut self, to: u64) -> PyResult<()> {
        self.inner.map_as_mut(|inner| inner.free_to(to))
    }

    pub fn free_first_one(&mut self) -> PyResult<()> {
        self.inner.map_as_mut(|inner| inner.free_first_one())
    }

    pub fn maybe_free_buffer(&mut self) -> PyResult<()> {
        self.inner.map_as_mut(|inner| inner.maybe_free_buffer())
    }

    pub fn buffer_capacity(&self) -> PyResult<usize> {
        self.inner.map_as_ref(|inner| inner.buffer_capacity())
    }

    pub fn buffer_is_allocated(&self) -> PyResult<bool> {
        self.inner.map_as_ref(|inner| inner.buffer_is_allocated())
    }

    pub fn count(&self) -> PyResult<usize> {
        self.inner.map_as_ref(|inner| inner.count())
    }
}
