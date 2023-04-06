use prost::Message as ProstMessage;
use protobuf::Message as PbMessage;
use pyo3::{prelude::*, pyclass::CompareOp};

use raft::eraftpb::SnapshotMetadata;

use utils::{errors::to_pyresult, reference::RustRef};

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

impl From<Py_SnapshotMetadata_Mut<'_>> for SnapshotMetadata {
    fn from(val: Py_SnapshotMetadata_Mut<'_>) -> Self {
        match val {
            Py_SnapshotMetadata_Mut::Owned(x) => x.inner.clone(),
            Py_SnapshotMetadata_Mut::RefMut(mut x) => x.inner.map_as_mut(|x| x.clone()).unwrap(),
        }
    }
}

impl From<&mut Py_SnapshotMetadata_Mut<'_>> for SnapshotMetadata {
    fn from(val: &mut Py_SnapshotMetadata_Mut<'_>) -> Self {
        match val {
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
            inner: SnapshotMetadata::new(),
        }
    }

    #[staticmethod]
    pub fn default() -> Py_SnapshotMetadata_Owner {
        Py_SnapshotMetadata_Owner {
            inner: SnapshotMetadata::default(),
        }
    }

    #[staticmethod]
    pub fn decode(v: &[u8]) -> PyResult<Py_SnapshotMetadata_Owner> {
        Ok(Py_SnapshotMetadata_Owner {
            inner: to_pyresult(ProstMessage::decode(v))?,
        })
    }

    pub fn make_ref(&mut self) -> Py_SnapshotMetadata_Ref {
        Py_SnapshotMetadata_Ref {
            inner: RustRef::new(&mut self.inner),
        }
    }

    pub fn __repr__(&self) -> String {
        format!("{:?}", self.inner)
    }

    pub fn __richcmp__(
        &self,
        py: Python<'_>,
        rhs: Py_SnapshotMetadata_Mut,
        op: CompareOp,
    ) -> PyObject {
        let rhs: SnapshotMetadata = rhs.into();

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
impl Py_SnapshotMetadata_Ref {
    pub fn __repr__(&self) -> PyResult<String> {
        self.inner.map_as_ref(|inner| format!("{:?}", inner))
    }

    pub fn __richcmp__(
        &self,
        py: Python<'_>,
        rhs: Py_SnapshotMetadata_Mut,
        op: CompareOp,
    ) -> PyResult<PyObject> {
        self.inner.map_as_ref(|inner| {
            let rhs: SnapshotMetadata = rhs.into();

            match op {
                CompareOp::Eq => (inner == &rhs).into_py(py),
                CompareOp::Ne => (inner != &rhs).into_py(py),
                _ => py.NotImplemented(),
            }
        })
    }

    pub fn clone(&self) -> PyResult<Py_SnapshotMetadata_Owner> {
        Ok(Py_SnapshotMetadata_Owner {
            inner: self.inner.map_as_ref(|inner| inner.clone())?,
        })
    }

    pub fn encode(&self, py: Python) -> PyResult<PyObject> {
        self.inner
            .map_as_ref(|inner| inner.encode_to_vec().into_py(py))
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

    pub fn get_conf_state(&mut self) -> PyResult<Py_ConfState_Ref> {
        self.inner.map_as_mut(|inner| Py_ConfState_Ref {
            inner: RustRef::new(inner.mut_conf_state()),
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
