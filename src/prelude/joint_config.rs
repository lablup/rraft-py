use std::{collections::HashSet, hash::BuildHasherDefault};

use pyo3::{prelude::*, pyclass::CompareOp, types::PySet};

use fxhash::FxHasher;
use raft::JointConfig;

use utils::reference::RustRef;

#[derive(Clone)]
#[pyclass(name = "JointConfig_Owner")]
pub struct Py_JointConfig_Owner {
    pub inner: JointConfig,
}

#[derive(Clone)]
#[pyclass(name = "JointConfig_Ref")]
pub struct Py_JointConfig_Ref {
    pub inner: RustRef<JointConfig>,
}

#[derive(FromPyObject)]
pub enum Py_JointConfig_Mut<'p> {
    Owned(PyRefMut<'p, Py_JointConfig_Owner>),
    RefMut(Py_JointConfig_Ref),
}

impl Into<JointConfig> for Py_JointConfig_Mut<'_> {
    fn into(self) -> JointConfig {
        match self {
            Py_JointConfig_Mut::Owned(x) => x.inner.clone(),
            Py_JointConfig_Mut::RefMut(mut x) => x.inner.map_as_mut(|x| x.clone()).unwrap(),
        }
    }
}

impl Into<JointConfig> for &mut Py_JointConfig_Mut<'_> {
    fn into(self) -> JointConfig {
        match self {
            Py_JointConfig_Mut::Owned(x) => x.inner.clone(),
            Py_JointConfig_Mut::RefMut(x) => x.inner.map_as_mut(|x| x.clone()).unwrap(),
        }
    }
}

#[pymethods]
impl Py_JointConfig_Owner {
    #[new]
    pub fn new(voters: &PySet) -> Self {
        Py_JointConfig_Owner {
            inner: JointConfig::new(
                voters
                    .extract::<HashSet<u64, BuildHasherDefault<FxHasher>>>()
                    .unwrap(),
            ),
        }
    }

    pub fn make_ref(&mut self) -> Py_JointConfig_Ref {
        Py_JointConfig_Ref {
            inner: RustRef::new(&mut self.inner),
        }
    }

    pub fn clone(&self) -> Py_JointConfig_Owner {
        Py_JointConfig_Owner {
            inner: self.inner.clone(),
        }
    }

    pub fn __repr__(&self) -> String {
        format!("{:?}", self.inner)
    }

    pub fn __richcmp__(&self, rhs: Py_JointConfig_Mut, op: CompareOp) -> bool {
        let rhs: JointConfig = rhs.into();

        match op {
            CompareOp::Eq => self.inner == rhs,
            CompareOp::Ne => self.inner != rhs,
            _ => panic!("Undefined operator"),
        }
    }

    pub fn __contains__(&self, id: u64) -> bool {
        self.inner.contains(id)
    }
}

#[pymethods]
impl Py_JointConfig_Ref {
    pub fn __repr__(&self) -> PyResult<String> {
        self.inner.map_as_ref(|inner| format!("{:?}", inner))
    }

    pub fn __richcmp__(&self, rhs: Py_JointConfig_Mut, op: CompareOp) -> PyResult<bool> {
        self.inner.map_as_ref(|inner| {
            let rhs: JointConfig = rhs.into();

            match op {
                CompareOp::Eq => inner == &rhs,
                CompareOp::Ne => inner != &rhs,
                _ => panic!("Undefined operator"),
            }
        })
    }

    pub fn __contains__(&self, id: u64) -> PyResult<bool> {
        self.inner.map_as_ref(|inner| inner.contains(id))
    }

    pub fn clone(&self) -> Py_JointConfig_Owner {
        Py_JointConfig_Owner {
            inner: self.inner.map_as_ref(|inner| inner.clone()).unwrap(),
        }
    }

    pub fn clear(&mut self) -> PyResult<()> {
        self.inner.map_as_mut(|inner| inner.clear())
    }

    pub fn contains(&self, id: u64) -> PyResult<bool> {
        self.inner.map_as_ref(|inner| inner.contains(id))
    }

    pub fn is_singleton(&self) -> PyResult<bool> {
        self.inner.map_as_ref(|inner| inner.is_singleton())
    }

    // TODO: AckedIndexer Trait is not public, so cannot write below function signature. Write below function when it will be possible.
    // pub fn committed_index(&mut self, use_group_commit: bool, acked_indexer: &Py_AckedIndexer) {
    //     self.inner.committed_index(use_group_commit, l)
    // }

    // pub fn vote_result(&self) -> bool {
    //     self.inner.vote_result(check)
    // }
}
