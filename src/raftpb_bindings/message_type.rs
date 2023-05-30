use pyo3::{prelude::*, pyclass::CompareOp};

use raft::eraftpb::MessageType;
use utils::errors::runtime_error;

#[derive(Clone)]
#[pyclass(name = "MessageType")]
pub struct Py_MessageType(pub MessageType);

impl From<Py_MessageType> for MessageType {
    fn from(val: Py_MessageType) -> Self {
        val.0
    }
}

impl From<MessageType> for Py_MessageType {
    fn from(x: MessageType) -> Self {
        match x {
            MessageType::MsgHup => Py_MessageType(MessageType::MsgHup),
            MessageType::MsgBeat => Py_MessageType(MessageType::MsgBeat),
            MessageType::MsgPropose => Py_MessageType(MessageType::MsgPropose),
            MessageType::MsgAppend => Py_MessageType(MessageType::MsgAppend),
            MessageType::MsgAppendResponse => Py_MessageType(MessageType::MsgAppendResponse),
            MessageType::MsgRequestVote => Py_MessageType(MessageType::MsgRequestVote),
            MessageType::MsgRequestVoteResponse => {
                Py_MessageType(MessageType::MsgRequestVoteResponse)
            }
            MessageType::MsgSnapshot => Py_MessageType(MessageType::MsgSnapshot),
            MessageType::MsgHeartbeat => Py_MessageType(MessageType::MsgHeartbeat),
            MessageType::MsgHeartbeatResponse => Py_MessageType(MessageType::MsgHeartbeatResponse),
            MessageType::MsgUnreachable => Py_MessageType(MessageType::MsgUnreachable),
            MessageType::MsgSnapStatus => Py_MessageType(MessageType::MsgSnapStatus),
            MessageType::MsgCheckQuorum => Py_MessageType(MessageType::MsgCheckQuorum),
            MessageType::MsgTransferLeader => Py_MessageType(MessageType::MsgTransferLeader),
            MessageType::MsgTimeoutNow => Py_MessageType(MessageType::MsgTimeoutNow),
            MessageType::MsgReadIndex => Py_MessageType(MessageType::MsgReadIndex),
            MessageType::MsgReadIndexResp => Py_MessageType(MessageType::MsgReadIndexResp),
            MessageType::MsgRequestPreVote => Py_MessageType(MessageType::MsgRequestPreVote),
            MessageType::MsgRequestPreVoteResponse => {
                Py_MessageType(MessageType::MsgRequestPreVoteResponse)
            }
        }
    }
}

#[pymethods]
impl Py_MessageType {
    pub fn __richcmp__(&self, py: Python<'_>, rhs: &Py_MessageType, op: CompareOp) -> PyObject {
        match op {
            CompareOp::Eq => (self.0 == rhs.0).into_py(py),
            CompareOp::Ne => (self.0 != rhs.0).into_py(py),
            _ => py.NotImplemented(),
        }
    }

    pub fn __hash__(&self) -> u64 {
        self.0 as u64
    }

    pub fn __repr__(&self) -> String {
        match self.0 {
            MessageType::MsgHup => "MsgHup".to_string(),
            MessageType::MsgBeat => "MsgBeat".to_string(),
            MessageType::MsgPropose => "MsgPropose".to_string(),
            MessageType::MsgAppend => "MsgAppend".to_string(),
            MessageType::MsgAppendResponse => "MsgAppendResponse".to_string(),
            MessageType::MsgRequestVote => "MsgRequestVote".to_string(),
            MessageType::MsgRequestVoteResponse => "MsgRequestVoteResponse".to_string(),
            MessageType::MsgSnapshot => "MsgSnapshot".to_string(),
            MessageType::MsgHeartbeat => "MsgHeartbeat".to_string(),
            MessageType::MsgHeartbeatResponse => "MsgHeartbeatResponse".to_string(),
            MessageType::MsgUnreachable => "MsgUnreachable".to_string(),
            MessageType::MsgSnapStatus => "MsgSnapStatus".to_string(),
            MessageType::MsgCheckQuorum => "MsgCheckQuorum".to_string(),
            MessageType::MsgTransferLeader => "MsgTransferLeader".to_string(),
            MessageType::MsgTimeoutNow => "MsgTimeoutNow".to_string(),
            MessageType::MsgReadIndex => "MsgReadIndex".to_string(),
            MessageType::MsgReadIndexResp => "MsgReadIndexResp".to_string(),
            MessageType::MsgRequestPreVote => "MsgRequestPreVote".to_string(),
            MessageType::MsgRequestPreVoteResponse => "MsgRequestPreVoteResponse".to_string(),
        }
    }

    #[staticmethod]
    pub fn from_int(v: i32, py: Python) -> PyResult<PyObject> {
        MessageType::from_i32(v)
            .map(|x| Py_MessageType(x).into_py(py))
            .ok_or_else(|| runtime_error("Invalid value"))
    }

    #[classattr]
    pub fn MsgHup() -> Self {
        Py_MessageType(MessageType::MsgHup)
    }

    #[classattr]
    pub fn MsgBeat() -> Self {
        Py_MessageType(MessageType::MsgBeat)
    }

    #[classattr]
    pub fn MsgPropose() -> Self {
        Py_MessageType(MessageType::MsgPropose)
    }

    #[classattr]
    pub fn MsgAppend() -> Self {
        Py_MessageType(MessageType::MsgAppend)
    }

    #[classattr]
    pub fn MsgAppendResponse() -> Self {
        Py_MessageType(MessageType::MsgAppendResponse)
    }

    #[classattr]
    pub fn MsgRequestVote() -> Self {
        Py_MessageType(MessageType::MsgRequestVote)
    }

    #[classattr]
    pub fn MsgRequestVoteResponse() -> Self {
        Py_MessageType(MessageType::MsgRequestVoteResponse)
    }

    #[classattr]
    pub fn MsgSnapshot() -> Self {
        Py_MessageType(MessageType::MsgSnapshot)
    }

    #[classattr]
    pub fn MsgHeartbeat() -> Self {
        Py_MessageType(MessageType::MsgHeartbeat)
    }

    #[classattr]
    pub fn MsgHeartbeatResponse() -> Self {
        Py_MessageType(MessageType::MsgHeartbeatResponse)
    }

    #[classattr]
    pub fn MsgUnreachable() -> Self {
        Py_MessageType(MessageType::MsgUnreachable)
    }

    #[classattr]
    pub fn MsgSnapStatus() -> Self {
        Py_MessageType(MessageType::MsgSnapStatus)
    }

    #[classattr]
    pub fn MsgCheckQuorum() -> Self {
        Py_MessageType(MessageType::MsgCheckQuorum)
    }

    #[classattr]
    pub fn MsgTransferLeader() -> Self {
        Py_MessageType(MessageType::MsgTransferLeader)
    }

    #[classattr]
    pub fn MsgTimeoutNow() -> Self {
        Py_MessageType(MessageType::MsgTimeoutNow)
    }

    #[classattr]
    pub fn MsgReadIndex() -> Self {
        Py_MessageType(MessageType::MsgReadIndex)
    }

    #[classattr]
    pub fn MsgReadIndexResp() -> Self {
        Py_MessageType(MessageType::MsgReadIndexResp)
    }

    #[classattr]
    pub fn MsgRequestPreVote() -> Self {
        Py_MessageType(MessageType::MsgRequestPreVote)
    }

    #[classattr]
    pub fn MsgRequestPreVoteResponse() -> Self {
        Py_MessageType(MessageType::MsgRequestPreVoteResponse)
    }
}

// Checks if certain message type should be used internally.
pub fn is_local_msg(t: MessageType) -> bool {
    matches!(
        t,
        MessageType::MsgHup
            | MessageType::MsgBeat
            | MessageType::MsgUnreachable
            | MessageType::MsgSnapStatus
            | MessageType::MsgCheckQuorum,
    )
}

pub fn is_response_msg(t: MessageType) -> bool {
    matches!(
        t,
        MessageType::MsgAppendResponse
            | MessageType::MsgRequestVoteResponse
            | MessageType::MsgHeartbeatResponse
            | MessageType::MsgUnreachable
            | MessageType::MsgRequestPreVoteResponse,
    )
}
