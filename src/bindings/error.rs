use pyo3::{create_exception, exceptions::PyException, prelude::*, pyclass::CompareOp};

use raft::{Error, StorageError};

#[pyclass(name = "RaftError")]
pub struct Py_RaftError(pub Error);

#[pymethods]
impl Py_RaftError {
    pub fn __richcmp__(&self, py: Python, rhs: &Py_RaftError, op: CompareOp) -> PyObject {
        match op {
            CompareOp::Eq => (self.0 == rhs.0).into_py(py),
            CompareOp::Ne => (self.0 != rhs.0).into_py(py),
            _ => py.NotImplemented(),
        }
    }

    pub fn __repr__(&self) -> String {
        match self.0 {
            Error::Exists { id, set } => format!("Exists {{ id: {}, set: {} }}", id, set),
            Error::NotExists { id, set } => format!("NotExists {{ id: {}, set: {} }}", id, set),
            Error::ConfChangeError(ref str) => format!("ConfChangeError {{ str: {} }}", str),
            Error::ConfigInvalid(ref str) => format!("ConfigInvalid {{ str: {} }}", str),
            Error::Io(ref err) => format!("Io {{ err: {} }}", err),
            Error::CodecError(ref err) => format!("CodecError {{ err: {} }}", err),
            Error::Store(ref err) => format!("Store {{ err: {} }}", err),
            Error::StepLocalMsg => "StepLocalMsg".to_string(),
            Error::StepPeerNotFound => "StepPeerNotFound".to_string(),
            Error::ProposalDropped => "ProposalDropped".to_string(),
            Error::RequestSnapshotDropped => "RequestSnapshotDropped".to_string(),
        }
    }
}

#[pyclass(name = "StorageError")]
pub struct Py_StorageError(pub StorageError);

#[pymethods]
impl Py_StorageError {
    pub fn __richcmp__(&self, py: Python, rhs: &Py_StorageError, op: CompareOp) -> PyObject {
        match op {
            CompareOp::Eq => (self.0 == rhs.0).into_py(py),
            CompareOp::Ne => (self.0 != rhs.0).into_py(py),
            _ => py.NotImplemented(),
        }
    }

    pub fn __repr__(&self) -> String {
        match self.0 {
            StorageError::Compacted => "Compacted".to_string(),
            StorageError::SnapshotOutOfDate => "SnapshotOutOfDate".to_string(),
            StorageError::SnapshotTemporarilyUnavailable => {
                "SnapshotTemporarilyUnavailable".to_string()
            }
            StorageError::Unavailable => "Unavailable".to_string(),
            StorageError::LogTemporarilyUnavailable => "LogTemporarilyUnavailable".to_string(),
            StorageError::Other(ref err) => format!("Other {{ err: {} }}", err),
        }
    }
}

impl From<Py_RaftError> for PyErr {
    fn from(err: Py_RaftError) -> PyErr {
        match err.0 {
            Error::Exists { id, set } => ExistsError::new_err(format!("id: {}, set: {}", id, set)),
            Error::NotExists { id, set } => {
                NotExistsError::new_err(format!("id: {}, set: {}", id, set))
            }
            Error::ConfChangeError(str) => ConfChangeError::new_err(str),
            Error::ConfigInvalid(str) => ConfigInvalidError::new_err(str),
            Error::Io(err) => IoError::new_err(err.to_string()),
            Error::CodecError(err) => CodecError::new_err(err.to_string()),
            Error::Store(err) => StoreError::new_err(err.to_string()),
            Error::StepLocalMsg => StepLocalMsgError::new_err(err.0.to_string()),
            Error::StepPeerNotFound => StepPeerNotFoundError::new_err(err.0.to_string()),
            Error::ProposalDropped => ProposalDroppedError::new_err(err.0.to_string()),
            Error::RequestSnapshotDropped => {
                RequestSnapshotDroppedError::new_err(err.0.to_string())
            }
        }
    }
}

impl From<Py_StorageError> for PyErr {
    fn from(err: Py_StorageError) -> PyErr {
        match err.0 {
            StorageError::Compacted => CompactedError::new_err(err.0.to_string()),
            StorageError::SnapshotOutOfDate => SnapshotOutOfDateError::new_err(err.0.to_string()),
            StorageError::SnapshotTemporarilyUnavailable => {
                SnapshotTemporarilyUnavailableError::new_err(err.0.to_string())
            }
            StorageError::Unavailable => UnavailableError::new_err(err.0.to_string()),
            StorageError::LogTemporarilyUnavailable => {
                LogTemporarilyUnavailableError::new_err(err.0.to_string())
            }
            StorageError::Other(_) => OtherError::new_err(err.0.to_string()),
        }
    }
}

create_exception!(rraft, RaftError, PyException);
create_exception!(rraft, RaftStorageError, PyException);

create_exception!(rraft, ExistsError, RaftError);
create_exception!(rraft, NotExistsError, RaftError);
create_exception!(rraft, ConfChangeError, RaftError);
create_exception!(rraft, ConfigInvalidError, RaftError);
create_exception!(rraft, IoError, RaftError);
create_exception!(rraft, CodecError, RaftError);
create_exception!(rraft, StoreError, RaftError);
create_exception!(rraft, StepLocalMsgError, RaftError);
create_exception!(rraft, StepPeerNotFoundError, RaftError);
create_exception!(rraft, ProposalDroppedError, RaftError);
create_exception!(rraft, RequestSnapshotDroppedError, RaftError);

create_exception!(rraft, CompactedError, RaftStorageError);
create_exception!(rraft, SnapshotOutOfDateError, RaftStorageError);
create_exception!(rraft, SnapshotTemporarilyUnavailableError, RaftStorageError);
create_exception!(rraft, UnavailableError, RaftStorageError);
create_exception!(rraft, LogTemporarilyUnavailableError, RaftStorageError);
create_exception!(rraft, OtherError, RaftStorageError);
