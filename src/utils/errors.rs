use core::panic;

use pyo3::{
    create_exception,
    exceptions::{PyException, PyRuntimeError},
    prelude::*,
    pyclass::CompareOp,
    types::PyTuple,
};

use crate::unsafe_cast::make_static;
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

// Convert 'PyErr' to 'raft::Error' for passing the error to raft-rs
// TODO: Complete below error handling logics.
pub fn makeNativeRaftError(py: Python, py_err: PyErr) -> raft::Error {
    let args = py_err.to_object(py).getattr(py, "args").unwrap();
    let args = args.downcast::<PyTuple>(py).unwrap();

    if py_err.is_instance_of::<ExistsError>(py) {
        let id = args.get_item(0).unwrap().extract::<u64>().unwrap();
        let set = args.get_item(1).unwrap().extract::<String>().unwrap();

        return raft::Error::Exists {
            id,
            set: unsafe { make_static(set.clone().as_str()) },
        };
    } else if py_err.is_instance_of::<NotExistsError>(py) {
        let id = args.get_item(0).unwrap().extract::<u64>().unwrap();
        let set = args.get_item(1).unwrap().extract::<String>().unwrap();

        return raft::Error::NotExists {
            id,
            set: unsafe { make_static(set.clone().as_str()) },
        };
    } else if py_err.is_instance_of::<ConfChangeError>(py) {
        let err_msg = args.get_item(0).unwrap().extract::<String>().unwrap();
        return raft::Error::ConfChangeError(err_msg);
    } else if py_err.is_instance_of::<ConfigInvalidError>(py) {
        let err_msg = args.get_item(0).unwrap().extract::<String>().unwrap();
        return raft::Error::ConfigInvalid(err_msg);
    } else if py_err.is_instance_of::<IoError>(py) {
        return raft::Error::Io(std::io::Error::new(std::io::ErrorKind::Other, py_err));
    } else if py_err.is_instance_of::<StepLocalMsgError>(py) {
        return raft::Error::StepLocalMsg;
    } else if py_err.is_instance_of::<StepPeerNotFoundError>(py) {
        return raft::Error::StepPeerNotFound;
    } else if py_err.is_instance_of::<ProposalDroppedError>(py) {
        return raft::Error::ProposalDropped;
    } else if py_err.is_instance_of::<RequestSnapshotDroppedError>(py) {
        return raft::Error::RequestSnapshotDropped;
    } else if py_err.is_instance_of::<StoreError>(py) {
        let error_kind = args.get_item(0).unwrap();
        return makeNativeStorageError(py_err, error_kind);
    } else if py_err.is_instance_of::<CodecError>(py) {
        unimplemented!()
    }

    // println!("Unreachable: {:?}", e);
    panic!("Unreachable")
}

fn makeNativeStorageError(py_err: PyErr, error_kind: &PyAny) -> raft::Error {
    if error_kind.is_instance_of::<CompactedError>().unwrap() {
        return raft::Error::Store(raft::StorageError::Compacted);
    } else if error_kind
        .is_instance_of::<SnapshotOutOfDateError>()
        .unwrap()
    {
        return raft::Error::Store(raft::StorageError::SnapshotOutOfDate);
    } else if error_kind
        .is_instance_of::<SnapshotTemporarilyUnavailableError>()
        .unwrap()
    {
        return raft::Error::Store(raft::StorageError::SnapshotTemporarilyUnavailable);
    } else if error_kind.is_instance_of::<UnavailableError>().unwrap() {
        return raft::Error::Store(raft::StorageError::Unavailable);
    } else if error_kind
        .is_instance_of::<LogTemporarilyUnavailableError>()
        .unwrap()
    {
        return raft::Error::Store(raft::StorageError::LogTemporarilyUnavailable);
    } else if error_kind.is_instance_of::<OtherError>().unwrap() {
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

#[inline]
pub fn runtime_error(msg: &str) -> PyErr {
    PyException::new_err(msg.to_string())
}

#[inline]
pub fn to_pyresult<T, E: std::fmt::Display>(res: Result<T, E>) -> PyResult<T> {
    match res {
        Ok(x) => Ok(x),
        Err(err) => Err(PyRuntimeError::new_err(err.to_string())),
    }
}

#[inline]
pub fn destroyed_error() -> PyErr {
    runtime_error("Cannot use a destroyed object's reference!")
}
