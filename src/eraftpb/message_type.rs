use pyo3::{prelude::*, pyclass::CompareOp};

use raft::eraftpb::MessageType;

#[derive(Clone)]
#[pyclass(name = "MessageType")]
pub struct Py_MessageType(pub MessageType);

impl Into<MessageType> for Py_MessageType {
    fn into(self) -> MessageType {
        match self.0 {
            MessageType::MsgHup => MessageType::MsgHup,
            MessageType::MsgBeat => MessageType::MsgBeat,
            MessageType::MsgPropose => MessageType::MsgPropose,
            MessageType::MsgAppend => MessageType::MsgAppend,
            MessageType::MsgAppendResponse => MessageType::MsgAppendResponse,
            MessageType::MsgRequestVote => MessageType::MsgRequestVote,
            MessageType::MsgRequestVoteResponse => MessageType::MsgRequestVoteResponse,
            MessageType::MsgSnapshot => MessageType::MsgSnapshot,
            MessageType::MsgHeartbeat => MessageType::MsgHeartbeat,
            MessageType::MsgHeartbeatResponse => MessageType::MsgHeartbeatResponse,
            MessageType::MsgUnreachable => MessageType::MsgUnreachable,
            MessageType::MsgSnapStatus => MessageType::MsgSnapStatus,
            MessageType::MsgCheckQuorum => MessageType::MsgCheckQuorum,
            MessageType::MsgTransferLeader => MessageType::MsgTransferLeader,
            MessageType::MsgTimeoutNow => MessageType::MsgTimeoutNow,
            MessageType::MsgReadIndex => MessageType::MsgReadIndex,
            MessageType::MsgReadIndexResp => MessageType::MsgReadIndexResp,
            MessageType::MsgRequestPreVote => MessageType::MsgRequestPreVote,
            MessageType::MsgRequestPreVoteResponse => MessageType::MsgRequestPreVoteResponse,
        }
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
    pub fn __richcmp__(&self, rhs: &Py_MessageType, op: CompareOp) -> PyResult<bool> {
        Ok(match op {
            CompareOp::Eq => self.0 == rhs.0,
            CompareOp::Ne => self.0 != rhs.0,
            _ => panic!("Undefined operator"),
        })
    }

    pub fn __hash__(&self) -> u64 {
        self.0 as u64
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
