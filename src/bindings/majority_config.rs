use pyo3::{intern, prelude::*, pyclass::CompareOp, types::PySet};

use fxhash::FxHasher;
use raft::MajorityConfig;
use std::{collections::HashSet, hash::BuildHasherDefault};

use utils::{implement_type_conversion, reference::RustRef};

#[derive(Clone)]
#[pyclass(name = "MajorityConfig")]
pub struct Py_MajorityConfig {
    pub inner: MajorityConfig,
}

#[derive(Clone)]
#[pyclass(name = "MajorityConfig_Ref")]
pub struct Py_MajorityConfig_Ref {
    pub inner: RustRef<MajorityConfig>,
}

#[derive(FromPyObject)]
pub enum Py_MajorityConfig_Mut<'p> {
    Owned(PyRefMut<'p, Py_MajorityConfig>),
    RefMut(Py_MajorityConfig_Ref),
}

implement_type_conversion!(MajorityConfig, Py_MajorityConfig_Mut);

#[pymethods]
impl Py_MajorityConfig {
    #[new]
    pub fn new(voters: &PySet) -> Self {
        Py_MajorityConfig {
            inner: MajorityConfig::new(
                voters
                    .extract::<HashSet<u64, BuildHasherDefault<FxHasher>>>()
                    .unwrap(),
            ),
        }
    }

    pub fn make_ref(&mut self) -> Py_MajorityConfig_Ref {
        Py_MajorityConfig_Ref {
            inner: RustRef::new(&mut self.inner),
        }
    }

    pub fn __repr__(&self) -> String {
        format!("{:?}", self.inner)
    }

    pub fn __richcmp__(&self, py: Python, rhs: Py_MajorityConfig_Mut, op: CompareOp) -> PyObject {
        let rhs: MajorityConfig = rhs.into();

        match op {
            CompareOp::Eq => (self.inner == rhs).into_py(py),
            CompareOp::Ne => (self.inner != rhs).into_py(py),
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
impl Py_MajorityConfig_Ref {
    pub fn __repr__(&self) -> PyResult<String> {
        self.inner.map_as_ref(|inner| format!("{:?}", inner))
    }

    pub fn __richcmp__(
        &self,
        py: Python,
        rhs: Py_MajorityConfig_Mut,
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

    pub fn clone(&self) -> PyResult<Py_MajorityConfig> {
        Ok(Py_MajorityConfig {
            inner: self.inner.map_as_ref(|inner| inner.clone())?,
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
            .map_as_mut(|inner| inner.try_reserve(additional).unwrap())
    }
}
