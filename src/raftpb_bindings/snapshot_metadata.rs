use prost::Message as ProstMessage;
use protobuf::Message as PbMessage;
use pyo3::{intern, prelude::*, pyclass::CompareOp, types::PyBytes};

use raft::eraftpb::SnapshotMetadata;

use utils::{
    errors::to_pyresult,
    implement_type_conversion,
    reference::{RefMutOwner, RustRef},
};

use super::conf_state::{Py_ConfState_Mut, Py_ConfState_Ref};

#[derive(Clone)]
#[pyclass(name = "SnapshotMetadata")]
pub struct Py_SnapshotMetadata {
    pub inner: RefMutOwner<SnapshotMetadata>,
}

#[derive(Clone)]
#[pyclass(name = "SnapshotMetadata_Ref")]
pub struct Py_SnapshotMetadata_Ref {
    pub inner: RustRef<SnapshotMetadata>,
}

#[derive(FromPyObject)]
pub enum Py_SnapshotMetadata_Mut<'p> {
    Owned(PyRefMut<'p, Py_SnapshotMetadata>),
    RefMut(Py_SnapshotMetadata_Ref),
}

implement_type_conversion!(SnapshotMetadata, Py_SnapshotMetadata_Mut);

#[pymethods]
impl Py_SnapshotMetadata {
    #[new]
    pub fn new() -> Self {
        Py_SnapshotMetadata {
            inner: RefMutOwner::new(SnapshotMetadata::new()),
        }
    }

    #[staticmethod]
    pub fn default() -> Py_SnapshotMetadata {
        Py_SnapshotMetadata {
            inner: RefMutOwner::new(SnapshotMetadata::default()),
        }
    }

    #[staticmethod]
    pub fn decode(v: &[u8]) -> PyResult<Py_SnapshotMetadata> {
        Ok(Py_SnapshotMetadata {
            inner: RefMutOwner::new(to_pyresult(ProstMessage::decode(v))?),
        })
    }

    pub fn make_ref(&mut self) -> Py_SnapshotMetadata_Ref {
        Py_SnapshotMetadata_Ref {
            inner: RustRef::new(&mut self.inner),
        }
    }

    pub fn __repr__(&self) -> String {
        format!("{:?}", self.inner.inner)
    }

    pub fn __richcmp__(&self, py: Python, rhs: Py_SnapshotMetadata_Mut, op: CompareOp) -> PyObject {
        let rhs: SnapshotMetadata = rhs.into();

        match op {
            CompareOp::Eq => (self.inner.inner == rhs).into_py(py),
            CompareOp::Ne => (self.inner.inner != rhs).into_py(py),
            _ => py.NotImplemented(),
        }
    }

    fn __getattr__(this: PyObject, py: Python, attr: &str) -> PyResult<PyObject> {
        let reference = this.call_method0(py, intern!(py, "make_ref"))?;
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
        py: Python,
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

    pub fn clone(&self) -> PyResult<Py_SnapshotMetadata> {
        Ok(Py_SnapshotMetadata {
            inner: RefMutOwner::new(self.inner.map_as_ref(|inner| inner.clone())?),
        })
    }

    pub fn encode(&self, py: Python) -> PyResult<PyObject> {
        self.inner
            .map_as_ref(|inner| PyBytes::new(py, inner.encode_to_vec().as_slice()).into_py(py))
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
            inner: RustRef::new_raw(inner.mut_conf_state()),
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
