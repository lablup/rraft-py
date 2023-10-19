use prost::Message as ProstMessage;
use protobuf::Message as PbMessage;
use pyo3::types::PyDict;
use pyo3::{intern, prelude::*, pyclass::CompareOp, types::PyBytes};

use raft::eraftpb::SnapshotMetadata;

use crate::implement_type_conversion;
use crate::utils::{
    errors::to_pyresult,
    reference::{RefMutContainer, RefMutOwner},
};

use super::conf_state::{PyConfStateMut, PyConfStateRef};

#[derive(Clone)]
#[pyclass(name = "SnapshotMetadata")]
pub struct PySnapshotMetadata {
    pub inner: RefMutOwner<SnapshotMetadata>,
}

#[derive(Clone)]
#[pyclass(name = "SnapshotMetadataRef")]
pub struct PySnapshotMetadataRef {
    pub inner: RefMutContainer<SnapshotMetadata>,
}

#[derive(FromPyObject)]
pub enum PySnapshotMetadataMut<'p> {
    Owned(PyRefMut<'p, PySnapshotMetadata>),
    RefMut(PySnapshotMetadataRef),
}

implement_type_conversion!(SnapshotMetadata, PySnapshotMetadataMut);

#[pymethods]
impl PySnapshotMetadata {
    #[new]
    pub fn new() -> Self {
        PySnapshotMetadata {
            inner: RefMutOwner::new(SnapshotMetadata::new()),
        }
    }

    #[staticmethod]
    pub fn default() -> PySnapshotMetadata {
        PySnapshotMetadata {
            inner: RefMutOwner::new(SnapshotMetadata::default()),
        }
    }

    #[staticmethod]
    pub fn decode(v: &[u8]) -> PyResult<PySnapshotMetadata> {
        Ok(PySnapshotMetadata {
            inner: RefMutOwner::new(to_pyresult(ProstMessage::decode(v))?),
        })
    }

    pub fn make_ref(&mut self) -> PySnapshotMetadataRef {
        PySnapshotMetadataRef {
            inner: RefMutContainer::new(&mut self.inner),
        }
    }

    pub fn __repr__(&self) -> String {
        format!("{:?}", self.inner.inner)
    }

    pub fn __richcmp__(&self, py: Python, rhs: PySnapshotMetadataMut, op: CompareOp) -> PyObject {
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
impl PySnapshotMetadataRef {
    pub fn __repr__(&self) -> PyResult<String> {
        self.inner.map_as_ref(|inner| format!("{:?}", inner))
    }

    pub fn __richcmp__(
        &self,
        py: Python,
        rhs: PySnapshotMetadataMut,
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

    pub fn to_dict(&mut self, py: Python) -> PyResult<PyObject> {
        let index = self.get_index()?;
        let term = self.get_term()?;
        let conf_state = self.get_conf_state()?;
        let conf_state = conf_state.to_dict(py)?;

        self.inner.map_as_ref(|_inner| {
            let res = PyDict::new(py);
            res.set_item("index", index).unwrap();
            res.set_item("term", term).unwrap();
            res.set_item("conf_state", conf_state).unwrap();
            res.into_py(py)
        })
    }

    pub fn clone(&self) -> PyResult<PySnapshotMetadata> {
        Ok(PySnapshotMetadata {
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

    // TODO: Make &mut self to &self
    pub fn get_conf_state(&mut self) -> PyResult<PyConfStateRef> {
        self.inner.map_as_mut(|inner| PyConfStateRef {
            inner: RefMutContainer::new_raw(inner.mut_conf_state()),
        })
    }

    pub fn set_conf_state(&mut self, cs: PyConfStateMut) -> PyResult<()> {
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
