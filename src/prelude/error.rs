use pyo3::{exceptions::PyIOError, prelude::*, pyclass::CompareOp, types::PyString};

use raft::{Error, StorageError};
use utils::{errors::runtime_error, unsafe_cast::make_static};

#[pyclass(name = "StorageError")]
pub struct Py_StorageError(pub StorageError);

#[pymethods]
impl Py_StorageError {
    pub fn __richcmp__(&mut self, rhs: &Py_StorageError, op: CompareOp) -> PyResult<bool> {
        Ok(match op {
            CompareOp::Eq => self.0 == rhs.0,
            CompareOp::Ne => self.0 != rhs.0,
            _ => panic!("Undefined operator"),
        })
    }

    pub fn __repr__(&self) -> String {
        match self.0 {
            StorageError::Compacted => "Compacted".to_string(),
            StorageError::SnapshotOutOfDate => "SnapshotOutOfDate".to_string(),
            StorageError::SnapshotTemporarilyUnavailable => {
                "SnapshotTemporarilyUnavailable".to_string()
            }
            StorageError::Unavailable => "Unavailable".to_string(),
            // StorageError::Other() => "Other".to_string(),
            _ => todo!(),
        }
    }

    #[classattr]
    pub fn Compacted() -> Self {
        Py_StorageError(StorageError::Compacted)
    }

    #[classattr]
    pub fn SnapshotOutOfDate() -> Self {
        Py_StorageError(StorageError::SnapshotOutOfDate)
    }

    #[classattr]
    pub fn SnapshotTemporarilyUnavailable() -> Self {
        Py_StorageError(StorageError::SnapshotTemporarilyUnavailable)
    }

    #[classattr]
    pub fn Unavailable() -> Self {
        Py_StorageError(StorageError::Unavailable)
    }

    // #[classattr]
    // pub fn Other() -> Self {
    //     // Py_StorageError(StorageError::Other())
    //     todo!()
    // }
}

#[pyclass(name = "RaftError")]
pub struct Py_RaftError(pub Error);

#[pymethods]
impl Py_RaftError {
    pub fn __richcmp__(&mut self, rhs: &Py_RaftError, op: CompareOp) -> PyResult<bool> {
        Ok(match op {
            CompareOp::Eq => self.0 == rhs.0,
            CompareOp::Ne => self.0 != rhs.0,
            _ => panic!("Undefined operator"),
        })
    }

    pub fn __repr__(&self) -> String {
        match self.0 {
            Error::Exists { id, set } => format!("Exists {{ id: {}, set: {} }}", id, set),
            Error::NotExists { id, set } => format!("NotExists {{ id: {}, set: {} }}", id, set),
            Error::ConfChangeError(ref str) => format!("ConfChangeError {{ str: {} }}", str),
            Error::ConfigInvalid(ref str) => format!("ConfigInvalid {{ str: {} }}", str),
            Error::Io(ref err) => format!("Io {{ err: {} }}", err),
            // Error::CodecError() => format!("CodecError"),
            Error::Store(ref err) => format!("Store {{ err: {} }}", err),
            Error::StepLocalMsg => "StepLocalMsg".to_string(),
            Error::StepPeerNotFound => "StepPeerNotFound".to_string(),
            Error::ProposalDropped => "ProposalDropped".to_string(),
            Error::RequestSnapshotDropped => "RequestSnapshotDropped".to_string(),
            _ => todo!(),
        }
    }

    #[staticmethod]
    pub fn Exists(id: u64, str: &PyString) -> Self {
        let str = unsafe { make_static(str).to_str() }.unwrap();
        Py_RaftError(Error::Exists { id, set: str })
    }

    #[staticmethod]
    pub fn NotExists(id: u64, str: &PyString) -> Self {
        let str = unsafe { make_static(str).to_str() }.unwrap();
        Py_RaftError(Error::NotExists { id, set: str })
    }

    #[staticmethod]
    pub fn ConfChangeError(str: &PyString) -> Self {
        Py_RaftError(Error::ConfChangeError(str.to_string()))
    }

    #[staticmethod]
    pub fn ConfigInvalid(str: &PyString) -> Self {
        Py_RaftError(Error::ConfigInvalid(str.to_string()))
    }

    #[staticmethod]
    pub fn Io(str: &PyString) -> Self {
        let str = unsafe { make_static(str).to_str() }.unwrap();
        Py_RaftError(Error::Io(PyIOError::new_err(str).into()))
    }

    // #[staticmethod]
    // pub fn CodecError() -> Self {
    //     Py_RaftError(Error::CodecError())
    // }

    #[staticmethod]
    pub fn Store(err: &Py_StorageError) -> Self {
        match err.0 {
            StorageError::Compacted => Py_RaftError(Error::Store(StorageError::Compacted)),
            StorageError::SnapshotOutOfDate => {
                Py_RaftError(Error::Store(StorageError::SnapshotOutOfDate))
            }
            StorageError::SnapshotTemporarilyUnavailable => {
                Py_RaftError(Error::Store(StorageError::SnapshotTemporarilyUnavailable))
            }
            StorageError::Unavailable => Py_RaftError(Error::Store(StorageError::Unavailable)),
            StorageError::Other(_) => panic!("Undefined"),
        }
    }

    #[classattr]
    pub fn StepLocalMsg() -> Self {
        Py_RaftError(Error::StepLocalMsg)
    }

    #[classattr]
    pub fn StepPeerNotFound() -> Self {
        Py_RaftError(Error::StepPeerNotFound)
    }

    #[classattr]
    pub fn ProposalDropped() -> Self {
        Py_RaftError(Error::ProposalDropped)
    }

    #[classattr]
    pub fn RequestSnapshotDropped() -> Self {
        Py_RaftError(Error::RequestSnapshotDropped)
    }
}

impl From<Py_RaftError> for PyErr {
    fn from(err: Py_RaftError) -> PyErr {
        runtime_error(&err.0.to_string())
    }
}
