use std::{collections::HashSet, hash::BuildHasherDefault};

use pyo3::{intern, prelude::*, pyclass::CompareOp, types::PySet};

use crate::implement_type_conversion;
use crate::utils::reference::{RefMutContainer, RefMutOwner};
use fxhash::FxHasher;
use raft::JointConfig;

#[derive(Clone)]
#[pyclass(name = "JointConfig")]
pub struct PyJointConfig {
    pub inner: RefMutOwner<JointConfig>,
}

#[derive(Clone)]
#[pyclass(name = "JointConfigRef")]
pub struct PyJointConfigRef {
    pub inner: RefMutContainer<JointConfig>,
}

#[derive(FromPyObject)]
pub enum PyJointConfigMut<'p> {
    Owned(PyRefMut<'p, PyJointConfig>),
    RefMut(PyJointConfigRef),
}

implement_type_conversion!(JointConfig, PyJointConfigMut);

#[pymethods]
impl PyJointConfig {
    #[new]
    pub fn new(voters: &PySet) -> PyResult<Self> {
        Ok(PyJointConfig {
            inner: RefMutOwner::new(JointConfig::new(
                voters.extract::<HashSet<u64, BuildHasherDefault<FxHasher>>>()?,
            )),
        })
    }

    pub fn make_ref(&mut self) -> PyJointConfigRef {
        PyJointConfigRef {
            inner: RefMutContainer::new(&mut self.inner),
        }
    }

    pub fn __repr__(&self) -> String {
        format!("{:?}", self.inner.inner)
    }

    pub fn __richcmp__(&self, py: Python, rhs: PyJointConfigMut, op: CompareOp) -> PyObject {
        let rhs: JointConfig = rhs.into();

        match op {
            CompareOp::Eq => (self.inner.inner == rhs).into_py(py),
            CompareOp::Ne => (self.inner.inner != rhs).into_py(py),
            _ => py.NotImplemented(),
        }
    }

    pub fn __contains__(&self, id: u64) -> bool {
        self.inner.contains(id)
    }

    fn __getattr__(this: PyObject, py: Python, attr: &str) -> PyResult<PyObject> {
        let reference = this.call_method0(py, intern!(py, "make_ref"))?;
        reference.getattr(py, attr)
    }
}

#[pymethods]
impl PyJointConfigRef {
    pub fn __repr__(&self) -> PyResult<String> {
        self.inner.map_as_ref(|inner| format!("{:?}", inner))
    }

    pub fn __richcmp__(
        &self,
        py: Python,
        rhs: PyJointConfigMut,
        op: CompareOp,
    ) -> PyResult<PyObject> {
        self.inner.map_as_ref(|inner| {
            let rhs: JointConfig = rhs.into();

            match op {
                CompareOp::Eq => (inner == &rhs).into_py(py),
                CompareOp::Ne => (inner != &rhs).into_py(py),
                _ => py.NotImplemented(),
            }
        })
    }

    pub fn __contains__(&self, id: u64) -> PyResult<bool> {
        self.inner.map_as_ref(|inner| inner.contains(id))
    }

    pub fn clone(&self) -> PyResult<PyJointConfig> {
        Ok(PyJointConfig {
            inner: RefMutOwner::new(self.inner.map_as_ref(|inner| inner.clone())?),
        })
    }

    pub fn clear(&mut self) -> PyResult<()> {
        self.inner.map_as_mut(|inner| inner.clear())
    }

    pub fn contains(&self, id: u64) -> PyResult<bool> {
        self.inner.map_as_ref(|inner| inner.contains(id))
    }

    pub fn ids(&self, py: Python) -> PyResult<PyObject> {
        self.inner
            .map_as_ref(|inner| inner.ids().iter().collect::<HashSet<_>>().into_py(py))
    }

    pub fn is_singleton(&self) -> PyResult<bool> {
        self.inner.map_as_ref(|inner| inner.is_singleton())
    }

    // TODO: AckedIndexer Trait is not public, so cannot write below function signature. Write below function when it will be possible.
    // pub fn committed_index(&mut self, use_group_commit: bool, acked_indexer: &PyAckedIndexer) {
    //     self.inner.committed_index(use_group_commit, l)
    // }

    // pub fn vote_result(&self) -> bool {
    //     self.inner.vote_result(check)
    // }
}
