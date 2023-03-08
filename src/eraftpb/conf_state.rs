use pyo3::pyclass::CompareOp;
use pyo3::{prelude::*, types::PyList};

use raft::eraftpb::ConfState;

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

impl Into<ConfState> for Py_ConfState_Mut<'_> {
    fn into(self) -> ConfState {
        match self {
            Py_ConfState_Mut::Owned(x) => x.inner.clone(),
            Py_ConfState_Mut::RefMut(mut x) => x.inner.map_as_mut(|x| x.clone()).unwrap(),
        }
    }
}

impl Into<ConfState> for &mut Py_ConfState_Mut<'_> {
    fn into(self) -> ConfState {
        match self {
            Py_ConfState_Mut::Owned(x) => x.inner.clone(),
            Py_ConfState_Mut::RefMut(x) => x.inner.map_as_mut(|x| x.clone()).unwrap(),
        }
    }
}

#[pymethods]
impl Py_ConfState_Owner {
    #[new]
    pub fn new(voters: Option<&PyList>, learners: Option<&PyList>) -> Self {
        if voters.and(learners).is_none() {
            Py_ConfState_Owner {
                inner: ConfState::default(),
            }
        } else if voters.or(learners).is_none() {
            // TODO: Improve below logic through throwing PyErr if possible
            panic!("voters and learners both values should or should not be given.")
        } else {
            let voters = voters.unwrap().extract::<Vec<u64>>().unwrap();
            let learners = learners.unwrap().extract::<Vec<u64>>().unwrap();
            Py_ConfState_Owner {
                inner: ConfState::from((voters, learners)),
            }
        }
    }

    pub fn make_ref(&mut self) -> Py_ConfState_Ref {
        Py_ConfState_Ref {
            inner: RustRef::new(&mut self.inner),
        }
    }

    pub fn clone(&self) -> Py_ConfState_Owner {
        Py_ConfState_Owner {
            inner: self.inner.clone(),
        }
    }

    pub fn __repr__(&self) -> String {
        format!("{:?}", self.inner)
    }

    pub fn __richcmp__(&self, rhs: Py_ConfState_Mut, op: CompareOp) -> bool {
        let rhs: ConfState = rhs.into();

        match op {
            CompareOp::Eq => self.inner == rhs,
            CompareOp::Ne => self.inner != rhs,
            _ => panic!("Undefined operator"),
        }
    }
}

#[pymethods]
impl Py_ConfState_Ref {
    pub fn __repr__(&self) -> PyResult<String> {
        self.inner.map_as_ref(|inner| format!("{:?}", inner))
    }

    pub fn __richcmp__(&self, rhs: Py_ConfState_Mut, op: CompareOp) -> PyResult<bool> {
        self.inner.map_as_ref(|inner| {
            let rhs: ConfState = rhs.into();

            match op {
                CompareOp::Eq => inner == &rhs,
                CompareOp::Ne => inner != &rhs,
                _ => panic!("Undefined operator"),
            }
        })
    }

    pub fn clone(&self) -> Py_ConfState_Owner {
        Py_ConfState_Owner {
            inner: self.inner.map_as_ref(|inner| inner.clone()).unwrap(),
        }
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
        self.inner
            .map_as_mut(|inner| inner.set_voters(list.extract::<Vec<u64>>().unwrap()))
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
        self.inner
            .map_as_mut(|inner| inner.set_voters_outgoing(list.extract::<Vec<u64>>().unwrap()))
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
        self.inner
            .map_as_mut(|inner| inner.set_learners(list.extract::<Vec<u64>>().unwrap()))
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
        self.inner
            .map_as_mut(|inner| inner.set_learners_next(list.extract::<Vec<u64>>().unwrap()))
    }

    pub fn clear_learners_next(&mut self) -> PyResult<()> {
        self.inner.map_as_mut(|inner| inner.clear_learners_next())
    }
}
