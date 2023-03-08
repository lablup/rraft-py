use pyo3::{prelude::*, pyclass::CompareOp};

use raft::eraftpb::SnapshotMetadata;

use utils::{
    reference::RustRef,
    unsafe_cast::make_mut,
};

use super::conf_state::{Py_ConfState_Mut, Py_ConfState_Ref};

#[derive(Clone)]
#[pyclass(name = "SnapshotMetadata_Owner")]
pub struct Py_SnapshotMetadata_Owner {
    pub inner: SnapshotMetadata,
}

#[derive(Clone)]
#[pyclass(name = "SnapshotMetadata_Ref")]
pub struct Py_SnapshotMetadata_Ref {
    pub inner: RustRef<SnapshotMetadata>,
}

#[derive(FromPyObject)]
pub enum Py_SnapshotMetadata_Mut<'p> {
    Owned(PyRefMut<'p, Py_SnapshotMetadata_Owner>),
    RefMut(Py_SnapshotMetadata_Ref),
}

impl Into<SnapshotMetadata> for Py_SnapshotMetadata_Mut<'_> {
    fn into(self) -> SnapshotMetadata {
        match self {
            Py_SnapshotMetadata_Mut::Owned(x) => x.inner.clone(),
            Py_SnapshotMetadata_Mut::RefMut(mut x) => x.inner.map_as_mut(|x| x.clone()).unwrap(),
        }
    }
}

impl Into<SnapshotMetadata> for &mut Py_SnapshotMetadata_Mut<'_> {
    fn into(self) -> SnapshotMetadata {
        match self {
            Py_SnapshotMetadata_Mut::Owned(x) => x.inner.clone(),
            Py_SnapshotMetadata_Mut::RefMut(x) => x.inner.map_as_mut(|x| x.clone()).unwrap(),
        }
    }
}

#[pymethods]
impl Py_SnapshotMetadata_Owner {
    #[new]
    pub fn new() -> Self {
        Py_SnapshotMetadata_Owner {
            inner: SnapshotMetadata::new_(),
        }
    }

    pub fn make_ref(&mut self) -> Py_SnapshotMetadata_Ref {
        Py_SnapshotMetadata_Ref {
            inner: RustRef::new(&mut self.inner),
        }
    }

    pub fn clone(&self) -> Py_SnapshotMetadata_Owner {
        Py_SnapshotMetadata_Owner {
            inner: self.inner.clone(),
        }
    }

    pub fn __repr__(&self) -> String {
        format!("{:?}", self.inner)
    }

    pub fn __richcmp__(&self, rhs: Py_SnapshotMetadata_Mut, op: CompareOp) -> bool {
        let rhs: SnapshotMetadata = rhs.into();

        match op {
            CompareOp::Eq => self.inner == rhs,
            CompareOp::Ne => self.inner != rhs,
            _ => panic!("Undefined operator"),
        }
    }
}

#[pymethods]
impl Py_SnapshotMetadata_Ref {
    pub fn __repr__(&self) -> PyResult<String> {
        self.inner.map_as_ref(|inner| format!("{:?}", inner))
    }

    pub fn __richcmp__(&self, rhs: Py_SnapshotMetadata_Mut, op: CompareOp) -> PyResult<bool> {
        self.inner.map_as_ref(|inner| {
            let rhs: SnapshotMetadata = rhs.into();

            match op {
                CompareOp::Eq => inner == &rhs,
                CompareOp::Ne => inner != &rhs,
                _ => panic!("Undefined operator"),
            }
        })
    }

    pub fn clone(&self) -> Py_SnapshotMetadata_Owner {
        Py_SnapshotMetadata_Owner {
            inner: self.inner.map_as_ref(|inner| inner.clone()).unwrap(),
        }
    }

    pub fn get_index(&self) -> PyResult<u64> {
        self.inner.map_as_ref(|inner| inner.get_index())
    }

    pub fn set_index(&mut self, v: u64) -> PyResult<()> {
        self.inner.map_as_mut(|inner| inner.set_index(v))
    }

    pub fn clear_index(&mut self) -> PyResult<()> {
        self.inner.map_as_mut(|inner| inner.clear_index())
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

    pub fn get_conf_state(&self) -> PyResult<Py_ConfState_Ref> {
        self.inner.map_as_ref(|inner| Py_ConfState_Ref {
            inner: RustRef::new(unsafe { make_mut(inner.get_conf_state()) }),
        })
    }

    pub fn set_conf_state(&mut self, cs: Py_ConfState_Mut) -> PyResult<()> {
        self.inner
            .map_as_mut(|inner| inner.set_conf_state(cs.into()))
    }

    pub fn clear_conf_state(&mut self) -> PyResult<()> {
        self.inner.map_as_mut(|inner| inner.clear_conf_state())
    }

    pub fn has_conf_state(&self) -> PyResult<bool> {
        self.inner.map_as_ref(|inner| inner.has_conf_state())
    }
}
