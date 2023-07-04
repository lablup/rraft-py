use prost::Message as ProstMessage;
use protobuf::Message as PbMessage;
use pyo3::{intern, prelude::*, pyclass::CompareOp, types::PyBytes};

use crate::implement_type_conversion;
use crate::utils::{
    errors::to_pyresult,
    reference::{RefMutContainer, RefMutOwner},
};
use raft::eraftpb::Snapshot;

use super::snapshot_metadata::{Py_SnapshotMetadata_Mut, Py_SnapshotMetadata_Ref};

#[derive(Clone)]
#[pyclass(name = "Snapshot")]
pub struct Py_Snapshot {
    pub inner: RefMutOwner<Snapshot>,
}

#[derive(Clone)]
#[pyclass(name = "Snapshot_Ref")]
pub struct Py_Snapshot_Ref {
    pub inner: RefMutContainer<Snapshot>,
}

#[derive(FromPyObject)]
pub enum Py_Snapshot_Mut<'p> {
    Owned(PyRefMut<'p, Py_Snapshot>),
    RefMut(Py_Snapshot_Ref),
}

implement_type_conversion!(Snapshot, Py_Snapshot_Mut);

#[pymethods]
impl Py_Snapshot {
    #[new]
    pub fn new() -> Self {
        Py_Snapshot {
            inner: RefMutOwner::new(Snapshot::new()),
        }
    }

    #[staticmethod]
    pub fn default() -> Py_Snapshot {
        Py_Snapshot {
            inner: RefMutOwner::new(Snapshot::default()),
        }
    }

    #[staticmethod]
    pub fn decode(v: &[u8]) -> PyResult<Py_Snapshot> {
        Ok(Py_Snapshot {
            inner: RefMutOwner::new(to_pyresult(ProstMessage::decode(v))?),
        })
    }

    pub fn make_ref(&mut self) -> Py_Snapshot_Ref {
        Py_Snapshot_Ref {
            inner: RefMutContainer::new(&mut self.inner),
        }
    }

    pub fn __repr__(&self) -> String {
        format!("{:?}", self.inner.inner)
    }

    pub fn __bool__(&self) -> bool {
        !self.inner.is_empty()
    }

    pub fn __richcmp__(&self, py: Python, rhs: Py_Snapshot_Mut, op: CompareOp) -> PyObject {
        let rhs: Snapshot = rhs.into();

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
impl Py_Snapshot_Ref {
    pub fn __repr__(&self) -> PyResult<String> {
        self.inner.map_as_ref(|inner| format!("{:?}", inner))
    }

    pub fn __richcmp__(
        &self,
        py: Python,
        rhs: Py_Snapshot_Mut,
        op: CompareOp,
    ) -> PyResult<PyObject> {
        self.inner.map_as_ref(|inner| {
            let rhs: Snapshot = rhs.into();

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

    pub fn clone(&self) -> PyResult<Py_Snapshot> {
        Ok(Py_Snapshot {
            inner: RefMutOwner::new(self.inner.map_as_ref(|inner| inner.clone())?),
        })
    }

    pub fn encode(&self, py: Python) -> PyResult<PyObject> {
        self.inner
            .map_as_ref(|inner| PyBytes::new(py, inner.encode_to_vec().as_slice()).into_py(py))
    }

    pub fn get_data(&self, py: Python) -> PyResult<Py<PyBytes>> {
        self.inner
            .map_as_ref(|inner| PyBytes::new(py, inner.get_data()).into())
    }

    pub fn set_data(&mut self, bytes: &PyAny) -> PyResult<()> {
        let bytes = bytes.extract::<Vec<u8>>()?;
        self.inner.map_as_mut(|inner| inner.set_data(bytes))
    }

    pub fn clear_data(&mut self) -> PyResult<()> {
        self.inner.map_as_mut(|inner| inner.clear_data())
    }

    pub fn get_metadata(&mut self) -> PyResult<Py_SnapshotMetadata_Ref> {
        self.inner.map_as_mut(|inner| Py_SnapshotMetadata_Ref {
            inner: RefMutContainer::new_raw(inner.mut_metadata()),
        })
    }

    pub fn set_metadata(&mut self, snapshot_meta_data: Py_SnapshotMetadata_Mut) -> PyResult<()> {
        self.inner
            .map_as_mut(|inner| inner.set_metadata(snapshot_meta_data.into()))
    }

    pub fn clear_metadata(&mut self) -> PyResult<()> {
        self.inner.map_as_mut(|inner| inner.clear_metadata())
    }

    pub fn has_metadata(&self) -> PyResult<bool> {
        self.inner.map_as_ref(|inner| inner.has_metadata())
    }
}
