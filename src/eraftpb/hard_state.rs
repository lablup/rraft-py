use pyo3::{prelude::*, pyclass::CompareOp};

use raft::eraftpb::HardState;

use utils::reference::RustRef;

#[derive(Clone)]
#[pyclass(name = "HardState_Owner")]
pub struct Py_HardState_Owner {
    pub inner: HardState,
}

#[derive(Clone)]
#[pyclass(name = "HardState_Ref")]
pub struct Py_HardState_Ref {
    pub inner: RustRef<HardState>,
}

#[derive(FromPyObject)]
pub enum Py_HardState_Mut<'p> {
    Owned(PyRefMut<'p, Py_HardState_Owner>),
    RefMut(Py_HardState_Ref),
}

impl From<Py_HardState_Mut<'_>> for HardState {
    fn from(val: Py_HardState_Mut<'_>) -> Self {
        match val {
            Py_HardState_Mut::Owned(x) => x.inner.clone(),
            Py_HardState_Mut::RefMut(mut x) => x.inner.map_as_mut(|x| x.clone()).unwrap(),
        }
    }
}

impl From<&mut Py_HardState_Mut<'_>> for HardState {
    fn from(val: &mut Py_HardState_Mut<'_>) -> Self {
        match val {
            Py_HardState_Mut::Owned(x) => x.inner.clone(),
            Py_HardState_Mut::RefMut(x) => x.inner.map_as_mut(|x| x.clone()).unwrap(),
        }
    }
}

#[pymethods]
impl Py_HardState_Owner {
    #[new]
    pub fn new() -> Self {
        Py_HardState_Owner {
            inner: HardState::new_(),
        }
    }

    #[staticmethod]
    pub fn default() -> Self {
        Py_HardState_Owner {
            inner: HardState::default(),
        }
    }

    pub fn make_ref(&mut self) -> Py_HardState_Ref {
        Py_HardState_Ref {
            inner: RustRef::new(&mut self.inner),
        }
    }

    pub fn __repr__(&mut self) -> String {
        format!("{:?}", self.inner)
    }

    pub fn __richcmp__(&mut self, rhs: Py_HardState_Mut, op: CompareOp) -> bool {
        let rhs: HardState = rhs.into();

        match op {
            CompareOp::Eq => self.inner == rhs,
            CompareOp::Ne => self.inner != rhs,
            _ => panic!("Undefined operator"),
        }
    }

    fn __getattr__(this: PyObject, py: Python<'_>, attr: &str) -> PyResult<PyObject> {
        let reference = this.call_method0(py, "make_ref")?;
        reference.getattr(py, attr)
    }
}

#[pymethods]
impl Py_HardState_Ref {
    pub fn __repr__(&self) -> PyResult<String> {
        self.inner.map_as_ref(|inner| format!("{:?}", inner))
    }

    pub fn __richcmp__(&self, rhs: Py_HardState_Mut, op: CompareOp) -> PyResult<bool> {
        self.inner.map_as_ref(|inner| {
            let rhs: HardState = rhs.into();

            match op {
                CompareOp::Eq => inner == &rhs,
                CompareOp::Ne => inner != &rhs,
                _ => panic!("Undefined operator"),
            }
        })
    }

    pub fn clone(&self) -> PyResult<Py_HardState_Owner> {
        Ok(Py_HardState_Owner {
            inner: self.inner.map_as_ref(|x| x.clone())?,
        })
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
