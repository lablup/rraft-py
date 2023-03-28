use pyo3::{prelude::*, pyclass::CompareOp};
use utils::reference::RustRef;

use super::conf_change_type::Py_ConfChangeType;

use raft::eraftpb::ConfChangeSingle;

#[derive(Clone)]
#[pyclass(name = "ConfChangeSingle_Owner")]
pub struct Py_ConfChangeSingle_Owner {
    pub inner: ConfChangeSingle,
}

#[derive(Clone)]
#[pyclass(name = "ConfChangeSingle_Ref")]
pub struct Py_ConfChangeSingle_Ref {
    pub inner: RustRef<ConfChangeSingle>,
}

#[derive(FromPyObject)]
pub enum Py_ConfChangeSingle_Mut<'p> {
    Owned(PyRefMut<'p, Py_ConfChangeSingle_Owner>),
    RefMut(Py_ConfChangeSingle_Ref),
}

impl From<Py_ConfChangeSingle_Mut<'_>> for ConfChangeSingle {
    fn from(val: Py_ConfChangeSingle_Mut<'_>) -> Self {
        match val {
            Py_ConfChangeSingle_Mut::Owned(x) => x.inner.clone(),
            Py_ConfChangeSingle_Mut::RefMut(mut x) => x.inner.map_as_mut(|x| x.clone()).unwrap(),
        }
    }
}

impl From<&mut Py_ConfChangeSingle_Mut<'_>> for ConfChangeSingle {
    fn from(val: &mut Py_ConfChangeSingle_Mut<'_>) -> Self {
        match val {
            Py_ConfChangeSingle_Mut::Owned(x) => x.inner.clone(),
            Py_ConfChangeSingle_Mut::RefMut(x) => x.inner.map_as_mut(|x| x.clone()).unwrap(),
        }
    }
}

#[pymethods]
impl Py_ConfChangeSingle_Owner {
    #[new]
    pub fn new() -> Self {
        Py_ConfChangeSingle_Owner {
            inner: ConfChangeSingle::new_(),
        }
    }

    #[staticmethod]
    pub fn default() -> Self {
        Py_ConfChangeSingle_Owner {
            inner: ConfChangeSingle::default(),
        }
    }

    pub fn make_ref(&mut self) -> Py_ConfChangeSingle_Ref {
        Py_ConfChangeSingle_Ref {
            inner: RustRef::new(&mut self.inner),
        }
    }

    pub fn __repr__(&self) -> String {
        format!("{:?}", self.inner)
    }

    pub fn __richcmp__(
        &self,
        py: Python<'_>,
        rhs: Py_ConfChangeSingle_Mut,
        op: CompareOp,
    ) -> PyObject {
        let rhs: ConfChangeSingle = rhs.into();

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
impl Py_ConfChangeSingle_Ref {
    pub fn __repr__(&self) -> PyResult<String> {
        self.inner.map_as_ref(|inner| format!("{:?}", inner))
    }

    pub fn __richcmp__(
        &self,
        py: Python<'_>,
        rhs: Py_ConfChangeSingle_Mut,
        op: CompareOp,
    ) -> PyResult<PyObject> {
        self.inner.map_as_ref(|inner| {
            let rhs: ConfChangeSingle = rhs.into();

            match op {
                CompareOp::Eq => (inner == &rhs).into_py(py),
                CompareOp::Ne => (inner != &rhs).into_py(py),
                _ => py.NotImplemented(),
            }
        })
    }

    pub fn clone(&self) -> PyResult<Py_ConfChangeSingle_Owner> {
        Ok(Py_ConfChangeSingle_Owner {
            inner: self.inner.map_as_ref(|x| x.clone())?,
        })
    }

    pub fn get_node_id(&self) -> PyResult<u64> {
        self.inner.map_as_ref(|inner| inner.get_node_id())
    }

    pub fn set_node_id(&mut self, v: u64) -> PyResult<()> {
        self.inner.map_as_mut(|inner| inner.set_node_id(v))
    }

    pub fn clear_node_id(&mut self) -> PyResult<()> {
        self.inner.map_as_mut(|inner| inner.clear_node_id())
    }

    pub fn get_change_type(&self) -> PyResult<Py_ConfChangeType> {
        self.inner
            .map_as_ref(|inner| Py_ConfChangeType(inner.get_change_type()))
    }

    pub fn set_change_type(&mut self, v: &Py_ConfChangeType) -> PyResult<()> {
        self.inner.map_as_mut(|inner| inner.set_change_type(v.0))
    }

    pub fn clear_change_type(&mut self) -> PyResult<()> {
        self.inner.map_as_mut(|inner| inner.clear_change_type())
    }
}
