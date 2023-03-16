use pyo3::{prelude::*, pyclass::CompareOp, types::PyList};
use raft::{eraftpb::ConfChangeV2, prelude::ConfChangeSingle};
use utils::{reference::RustRef, unsafe_cast::make_mut};

use super::{
    conf_change_single::{Py_ConfChangeSingle_Mut, Py_ConfChangeSingle_Ref},
    conf_change_transition::Py_ConfChangeTransition,
};

#[derive(Clone)]
#[pyclass(name = "ConfChangeV2_Owner")]
pub struct Py_ConfChangeV2_Owner {
    pub inner: ConfChangeV2,
}

#[derive(Clone)]
#[pyclass(name = "ConfChangeV2_Ref")]
pub struct Py_ConfChangeV2_Ref {
    pub inner: RustRef<ConfChangeV2>,
}

#[derive(FromPyObject)]
pub enum Py_ConfChangeV2_Mut<'p> {
    Owned(PyRefMut<'p, Py_ConfChangeV2_Owner>),
    RefMut(Py_ConfChangeV2_Ref),
}

impl Into<ConfChangeV2> for Py_ConfChangeV2_Mut<'_> {
    fn into(self) -> ConfChangeV2 {
        match self {
            Py_ConfChangeV2_Mut::Owned(x) => x.inner.clone(),
            Py_ConfChangeV2_Mut::RefMut(mut x) => x.inner.map_as_mut(|x| x.clone()).unwrap(),
        }
    }
}

impl Into<ConfChangeV2> for &mut Py_ConfChangeV2_Mut<'_> {
    fn into(self) -> ConfChangeV2 {
        match self {
            Py_ConfChangeV2_Mut::Owned(x) => x.inner.clone(),
            Py_ConfChangeV2_Mut::RefMut(x) => x.inner.map_as_mut(|x| x.clone()).unwrap(),
        }
    }
}

#[pymethods]
impl Py_ConfChangeV2_Owner {
    #[new]
    pub fn new() -> Self {
        Py_ConfChangeV2_Owner {
            inner: ConfChangeV2::new_(),
        }
    }

    #[staticmethod]
    pub fn default() -> Self {
        Py_ConfChangeV2_Owner {
            inner: ConfChangeV2::default(),
        }
    }

    pub fn make_ref(&mut self) -> Py_ConfChangeV2_Ref {
        Py_ConfChangeV2_Ref {
            inner: RustRef::new(&mut self.inner),
        }
    }

    pub fn clone(&self) -> Py_ConfChangeV2_Owner {
        Py_ConfChangeV2_Owner {
            inner: self.inner.clone(),
        }
    }

    pub fn __repr__(&self) -> String {
        format!("{:?}", self.inner)
    }

    pub fn __richcmp__(&self, rhs: Py_ConfChangeV2_Mut, op: CompareOp) -> bool {
        let rhs: ConfChangeV2 = rhs.into();

        match op {
            CompareOp::Eq => self.inner == rhs,
            CompareOp::Ne => self.inner != rhs,
            _ => panic!("Undefined operator"),
        }
    }
}

#[pymethods]
impl Py_ConfChangeV2_Ref {
    pub fn __repr__(&self) -> PyResult<String> {
        self.inner.map_as_ref(|inner| format!("{:?}", inner))
    }

    pub fn __richcmp__(&self, rhs: Py_ConfChangeV2_Mut, op: CompareOp) -> PyResult<bool> {
        self.inner.map_as_ref(|inner| {
            let rhs: ConfChangeV2 = rhs.into();

            match op {
                CompareOp::Eq => inner == &rhs,
                CompareOp::Ne => inner != &rhs,
                _ => panic!("Undefined operator"),
            }
        })
    }

    pub fn clone(&self) -> Py_ConfChangeV2_Owner {
        Py_ConfChangeV2_Owner {
            inner: self.inner.map_as_ref(|x| x.clone()).unwrap(),
        }
    }

    pub fn get_changes(&self, py: Python) -> PyResult<PyObject> {
        self.inner.map_as_ref(|inner| {
            inner
                .get_changes()
                .iter()
                .map(|cs| Py_ConfChangeSingle_Ref {
                    inner: RustRef::new(unsafe { make_mut(cs) }),
                })
                .collect::<Vec<_>>()
                .into_py(py)
        })
    }

    pub fn set_changes(&mut self, v: &PyList) -> PyResult<()> {
        self.inner.map_as_mut(|inner| {
            inner.set_changes(
                v.iter()
                    .map(|cs| cs.extract::<Py_ConfChangeSingle_Mut>().unwrap().into())
                    .collect::<Vec<_>>(),
            )
        })
    }

    pub fn clear_changes(&mut self) -> PyResult<()> {
        self.inner.map_as_mut(|inner| inner.clear_changes())
    }

    pub fn get_context(&self, py: Python) -> PyResult<Py<PyList>> {
        self.inner
            .map_as_ref(|inner| PyList::new(py, inner.get_context()).into())
    }

    pub fn set_context(&mut self, v: &PyList) -> PyResult<()> {
        let context = v.extract::<Vec<u8>>()?;
        self.inner.map_as_mut(|inner| inner.set_context(context))
    }

    pub fn clear_context(&mut self) -> PyResult<()> {
        self.inner.map_as_mut(|inner| inner.clear_context())
    }

    pub fn get_transition(&self) -> PyResult<Py_ConfChangeTransition> {
        self.inner
            .map_as_ref(|inner| Py_ConfChangeTransition(inner.get_transition()))
    }

    pub fn set_transition(&mut self, v: &Py_ConfChangeTransition) -> PyResult<()> {
        self.inner.map_as_mut(|inner| inner.set_transition(v.0))
    }

    pub fn clear_transition(&mut self) -> PyResult<()> {
        self.inner.map_as_mut(|inner| inner.clear_transition())
    }

    pub fn enter_joint(&self) -> PyResult<Option<bool>> {
        self.inner.map_as_ref(|inner| inner.enter_joint())
    }

    pub fn leave_joint(&self) -> PyResult<bool> {
        self.inner.map_as_ref(|inner| inner.leave_joint())
    }
}
