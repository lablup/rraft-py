use pyo3::{intern, prelude::*, pyclass::CompareOp};

use crate::implement_type_conversion;
use crate::utils::reference::{RefMutContainer, RefMutOwner};
use raft::Inflights;

#[derive(Clone)]
#[pyclass(name = "Inflights")]
pub struct PyInflights {
    pub inner: RefMutOwner<Inflights>,
}

#[derive(Clone)]
#[pyclass(name = "InflightsRef")]
pub struct PyInflightsRef {
    pub inner: RefMutContainer<Inflights>,
}

#[derive(FromPyObject)]
pub enum PyInflightsMut<'p> {
    Owned(PyRefMut<'p, PyInflights>),
    RefMut(PyInflightsRef),
}

implement_type_conversion!(Inflights, PyInflightsMut);

#[pymethods]
impl PyInflights {
    #[new]
    pub fn new(cap: usize) -> Self {
        PyInflights {
            inner: RefMutOwner::new(Inflights::new(cap)),
        }
    }

    pub fn make_ref(&mut self) -> PyInflightsRef {
        PyInflightsRef {
            inner: RefMutContainer::new(&mut self.inner),
        }
    }

    pub fn __repr__(&self) -> String {
        format!("{:?}", self.inner.inner)
    }

    pub fn __richcmp__(&self, py: Python, rhs: PyInflightsMut, op: CompareOp) -> PyObject {
        let rhs: Inflights = rhs.into();

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
impl PyInflightsRef {
    pub fn __repr__(&self) -> PyResult<String> {
        self.inner.map_as_ref(|inner| format!("{:?}", inner))
    }

    pub fn __richcmp__(
        &self,
        py: Python,
        rhs: PyInflightsMut,
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

    pub fn clone(&self) -> PyResult<PyInflights> {
        Ok(PyInflights {
            inner: RefMutOwner::new(self.inner.map_as_ref(|inner| inner.clone())?),
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
