use prost::Message as ProstMessage;
use protobuf::Message as PbMessage;
use pyo3::types::PyDict;
use pyo3::{intern, prelude::*, pyclass::CompareOp, types::PyBytes};

use crate::implement_type_conversion;
use crate::utils::{
    errors::to_pyresult,
    reference::{RefMutContainer, RefMutOwner},
};
use raft::derializer::format_snapshot;
use raft::eraftpb::Snapshot;

use super::snapshot_metadata::{PySnapshotMetadataMut, PySnapshotMetadataRef};

#[derive(Clone)]
#[pyclass(name = "Snapshot")]
pub struct PySnapshot {
    pub inner: RefMutOwner<Snapshot>,
}

#[derive(Clone)]
#[pyclass(name = "SnapshotRef")]
pub struct PySnapshotRef {
    pub inner: RefMutContainer<Snapshot>,
}

#[derive(FromPyObject)]
pub enum PySnapshotMut<'p> {
    Owned(PyRefMut<'p, PySnapshot>),
    RefMut(PySnapshotRef),
}

implement_type_conversion!(Snapshot, PySnapshotMut);

#[pymethods]
impl PySnapshot {
    #[new]
    pub fn new() -> Self {
        PySnapshot {
            inner: RefMutOwner::new(Snapshot::new()),
        }
    }

    #[staticmethod]
    pub fn default() -> PySnapshot {
        PySnapshot {
            inner: RefMutOwner::new(Snapshot::default()),
        }
    }

    #[staticmethod]
    pub fn decode(v: &[u8]) -> PyResult<PySnapshot> {
        Ok(PySnapshot {
            inner: RefMutOwner::new(to_pyresult(ProstMessage::decode(v))?),
        })
    }

    pub fn make_ref(&mut self) -> PySnapshotRef {
        PySnapshotRef {
            inner: RefMutContainer::new(&mut self.inner),
        }
    }

    pub fn __repr__(&self) -> String {
        format_snapshot(&self.inner.inner)
    }

    pub fn __bool__(&self) -> bool {
        !self.inner.is_empty()
    }

    pub fn __richcmp__(&self, py: Python, rhs: PySnapshotMut, op: CompareOp) -> PyObject {
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
impl PySnapshotRef {
    pub fn __repr__(&self) -> PyResult<String> {
        self.inner
            .map_as_ref(|inner: &Snapshot| format_snapshot(inner))
    }

    pub fn __richcmp__(&self, py: Python, rhs: PySnapshotMut, op: CompareOp) -> PyResult<PyObject> {
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

    pub fn to_dict(&mut self, py: Python) -> PyResult<PyObject> {
        let data = self.get_data(py)?;
        let mut metadata = self.get_metadata()?;
        let metadata = metadata.to_dict(py)?;

        self.inner.map_as_ref(|_inner| {
            let res = PyDict::new(py);
            res.set_item("data", data).unwrap();
            res.set_item("metadata", metadata).unwrap();

            res.into_py(py)
        })
    }

    pub fn clone(&self) -> PyResult<PySnapshot> {
        Ok(PySnapshot {
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

    // TODO: Make &mut self to &self
    pub fn get_metadata(&mut self) -> PyResult<PySnapshotMetadataRef> {
        self.inner.map_as_mut(|inner| PySnapshotMetadataRef {
            inner: RefMutContainer::new_raw(inner.mut_metadata()),
        })
    }

    pub fn set_metadata(&mut self, snapshot_meta_data: PySnapshotMetadataMut) -> PyResult<()> {
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
