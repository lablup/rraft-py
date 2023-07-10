use pyo3::{intern, prelude::*, pyclass::CompareOp, types::PySet};

use crate::implement_type_conversion;
use crate::utils::reference::{RefMutContainer, RefMutOwner};
use fxhash::FxHasher;
use raft::MajorityConfig;
use std::{collections::HashSet, hash::BuildHasherDefault};

#[derive(Clone)]
#[pyclass(name = "MajorityConfig")]
pub struct PyMajorityConfig {
    pub inner: RefMutOwner<MajorityConfig>,
}

#[derive(Clone)]
#[pyclass(name = "MajorityConfigRef")]
pub struct PyMajorityConfigRef {
    pub inner: RefMutContainer<MajorityConfig>,
}

#[derive(FromPyObject)]
pub enum PyMajorityConfigMut<'p> {
    Owned(PyRefMut<'p, PyMajorityConfig>),
    RefMut(PyMajorityConfigRef),
}

implement_type_conversion!(MajorityConfig, PyMajorityConfigMut);

#[pymethods]
impl PyMajorityConfig {
    #[new]
    pub fn new(voters: &PySet) -> PyResult<Self> {
        Ok(PyMajorityConfig {
            inner: RefMutOwner::new(MajorityConfig::new(
                voters.extract::<HashSet<u64, BuildHasherDefault<FxHasher>>>()?,
            )),
        })
    }

    pub fn make_ref(&mut self) -> PyMajorityConfigRef {
        PyMajorityConfigRef {
            inner: RefMutContainer::new(&mut self.inner),
        }
    }

    pub fn __repr__(&self) -> String {
        format!("{:?}", self.inner.inner)
    }

    pub fn __richcmp__(&self, py: Python, rhs: PyMajorityConfigMut, op: CompareOp) -> PyObject {
        let rhs: MajorityConfig = rhs.into();

        match op {
            CompareOp::Eq => (self.inner.inner == rhs).into_py(py),
            CompareOp::Ne => (self.inner.inner != rhs).into_py(py),
            _ => py.NotImplemented(),
        }
    }

    pub fn __bool__(&self) -> bool {
        !self.inner.is_empty()
    }

    fn __getattr__(this: PyObject, py: Python, attr: &str) -> PyResult<PyObject> {
        let reference = this.call_method0(py, intern!(py, "make_ref"))?;
        reference.getattr(py, attr)
    }
}

#[pymethods]
impl PyMajorityConfigRef {
    pub fn __repr__(&self) -> PyResult<String> {
        self.inner.map_as_ref(|inner| format!("{:?}", inner))
    }

    pub fn __richcmp__(
        &self,
        py: Python,
        rhs: PyMajorityConfigMut,
        op: CompareOp,
    ) -> PyResult<PyObject> {
        self.inner.map_as_ref(|inner| {
            let rhs: MajorityConfig = rhs.into();

            match op {
                CompareOp::Eq => (inner == &rhs).into_py(py),
                CompareOp::Ne => (inner != &rhs).into_py(py),
                _ => py.NotImplemented(),
            }
        })
    }

    pub fn __bool__(&self) -> PyResult<bool> {
        self.inner.map_as_ref(|inner| !inner.is_empty())
    }

    pub fn __len__(&self) -> PyResult<usize> {
        self.inner.map_as_ref(|inner| inner.len())
    }

    pub fn clone(&self) -> PyResult<PyMajorityConfig> {
        Ok(PyMajorityConfig {
            inner: RefMutOwner::new(self.inner.map_as_ref(|inner| inner.clone())?),
        })
    }

    pub fn capacity(&self) -> PyResult<usize> {
        self.inner.map_as_ref(|inner| inner.capacity())
    }

    pub fn extend(&mut self, other_set: &PySet) -> PyResult<()> {
        let other_set = other_set.extract::<HashSet<u64, BuildHasherDefault<FxHasher>>>()?;
        self.inner
            .map_as_mut(|inner| inner.extend(other_set.iter()))
    }

    pub fn get(&self, v: u64) -> PyResult<Option<u64>> {
        self.inner.map_as_ref(|inner| inner.get(&v).copied())
    }

    pub fn insert(&mut self, value: u64) -> PyResult<bool> {
        self.inner.map_as_mut(|inner| inner.insert(value))
    }

    pub fn replace(&mut self, value: u64) -> PyResult<Option<u64>> {
        self.inner.map_as_mut(|inner| inner.replace(value))
    }

    pub fn is_disjoint(&mut self, other: &PySet) -> PyResult<bool> {
        let other = other.extract::<HashSet<u64, BuildHasherDefault<FxHasher>>>()?;
        self.inner.map_as_mut(|inner| inner.is_disjoint(&other))
    }

    pub fn raw_slice(&self) -> PyResult<Vec<u64>> {
        self.inner.map_as_ref(|inner| inner.raw_slice())
    }

    pub fn is_superset(&self, other: &PySet) -> PyResult<bool> {
        let other = other.extract::<HashSet<u64, BuildHasherDefault<FxHasher>>>()?;
        self.inner.map_as_ref(|inner| inner.is_superset(&other))
    }

    pub fn is_subset(&self, other: &PySet) -> PyResult<bool> {
        let other = other.extract::<HashSet<u64, BuildHasherDefault<FxHasher>>>()?;
        self.inner.map_as_ref(|inner| inner.is_subset(&other))
    }

    pub fn reserve(&mut self, additional: usize) -> PyResult<()> {
        self.inner.map_as_mut(|inner| inner.reserve(additional))
    }

    pub fn remove(&mut self, v: u64) -> PyResult<bool> {
        self.inner.map_as_mut(|inner| inner.remove(&v))
    }

    pub fn shrink_to(&mut self, min_capacity: usize) -> PyResult<()> {
        self.inner.map_as_mut(|inner| inner.shrink_to(min_capacity))
    }

    pub fn shrink_to_fit(&mut self) -> PyResult<()> {
        self.inner.map_as_mut(|inner| inner.shrink_to_fit())
    }

    pub fn try_reserve(&mut self, additional: usize) -> PyResult<()> {
        self.inner
            .map_as_mut(|inner| inner.try_reserve(additional).expect("try_reserve failed!"))
    }
}
