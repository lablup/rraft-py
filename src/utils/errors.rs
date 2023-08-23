use core::panic;
use std::fmt::Display;

use pyo3::{
    create_exception,
    exceptions::{PyException, PyRuntimeError},
    prelude::*,
    pyclass::CompareOp,
    types::PyTuple,
};

use super::unsafe_cast::make_static;
use raft::{Error, StorageError};

#[pyclass(name = "RaftError")]
pub struct PyRaftError(pub Error);

#[pymethods]
impl PyRaftError {
    pub fn __richcmp__(&self, py: Python, rhs: &PyRaftError, op: CompareOp) -> PyObject {
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
pub struct PyStorageError(pub StorageError);

#[pymethods]
impl PyStorageError {
    pub fn __richcmp__(&self, py: Python, rhs: &PyStorageError, op: CompareOp) -> PyObject {
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

impl From<PyRaftError> for PyErr {
    fn from(err: PyRaftError) -> PyErr {
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

impl From<PyStorageError> for PyErr {
    fn from(err: PyStorageError) -> PyErr {
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

// Convert 'PyErr' to 'raft::Error' for passing the error to raft-rs
// TODO: Complete below error handling logics.
pub fn make_native_raft_error(py: Python, py_err: PyErr) -> raft::Error {
    let args = py_err.to_object(py).getattr(py, "args").unwrap();
    let args = args.downcast::<PyTuple>(py).unwrap();

    if py_err.is_instance_of::<ExistsError>(py) {
        let id = args.get_item(0).unwrap().extract::<u64>().unwrap();
        let set = args.get_item(1).unwrap().extract::<String>().unwrap();

        return raft::Error::Exists {
            id,
            set: unsafe { make_static(set.as_str()) },
        };
    }

    if py_err.is_instance_of::<NotExistsError>(py) {
        let id = args.get_item(0).unwrap().extract::<u64>().unwrap();
        let set = args.get_item(1).unwrap().extract::<String>().unwrap();

        return raft::Error::NotExists {
            id,
            set: unsafe { make_static(set.as_str()) },
        };
    }

    if py_err.is_instance_of::<ConfChangeError>(py) {
        let err_msg = args.get_item(0).unwrap().extract::<String>().unwrap();
        return raft::Error::ConfChangeError(err_msg);
    }

    if py_err.is_instance_of::<ConfigInvalidError>(py) {
        let err_msg = args.get_item(0).unwrap().extract::<String>().unwrap();
        return raft::Error::ConfigInvalid(err_msg);
    }

    if py_err.is_instance_of::<IoError>(py) {
        return raft::Error::Io(std::io::Error::new(std::io::ErrorKind::Other, py_err));
    }

    if py_err.is_instance_of::<StepLocalMsgError>(py) {
        return raft::Error::StepLocalMsg;
    }

    if py_err.is_instance_of::<StepPeerNotFoundError>(py) {
        return raft::Error::StepPeerNotFound;
    }

    if py_err.is_instance_of::<ProposalDroppedError>(py) {
        return raft::Error::ProposalDropped;
    }

    if py_err.is_instance_of::<RequestSnapshotDroppedError>(py) {
        return raft::Error::RequestSnapshotDropped;
    }

    if py_err.is_instance_of::<StoreError>(py) {
        let err_kind = args.get_item(0).unwrap();
        return make_native_storage_error(py_err, err_kind);
    }

    if py_err.is_instance_of::<CodecError>(py) {
        unimplemented!()
    }

    panic!("Unreachable {:?}", py_err);
}

fn make_native_storage_error(py_err: PyErr, err_kind: &PyAny) -> raft::Error {
    if err_kind.is_instance_of::<CompactedError>() {
        return raft::Error::Store(raft::StorageError::Compacted);
    }

    if err_kind.is_instance_of::<SnapshotOutOfDateError>() {
        return raft::Error::Store(raft::StorageError::SnapshotOutOfDate);
    }

    if err_kind.is_instance_of::<SnapshotTemporarilyUnavailableError>() {
        return raft::Error::Store(raft::StorageError::SnapshotTemporarilyUnavailable);
    }

    if err_kind.is_instance_of::<UnavailableError>() {
        return raft::Error::Store(raft::StorageError::Unavailable);
    }

    if err_kind.is_instance_of::<LogTemporarilyUnavailableError>() {
        return raft::Error::Store(raft::StorageError::LogTemporarilyUnavailable);
    }

    if err_kind.is_instance_of::<OtherError>() {
        return raft::Error::Store(raft::StorageError::Other(Box::new(py_err)));
    }

    panic!("Unreachable, Invalid StoreError type occurred.")
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

create_exception!(rraft, DestroyedRefUsedError, PyException);

#[inline]
pub fn runtime_error(msg: &str) -> PyErr {
    PyException::new_err(msg.to_string())
}

#[inline]
pub fn to_pyresult<T, E: Display>(res: Result<T, E>) -> PyResult<T> {
    res.map_err(|err| PyRuntimeError::new_err(err.to_string()))
}

pub static DESTROYED_ERR_MSG: &str = "Cannot use a destroyed object's reference!";
