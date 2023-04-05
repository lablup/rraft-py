use pyo3::prelude::*;

use raft::default_logger as _default_logger;
use raft::majority as _majority;
use raft::vote_resp_msg_type as _vote_resp_msg_type;
use raft::{
    CAMPAIGN_ELECTION, CAMPAIGN_PRE_ELECTION, CAMPAIGN_TRANSFER, INVALID_ID, INVALID_INDEX,
    NO_LIMIT,
};
use raftpb_bindings::conf_change::new_conf_change_single as _new_conf_change_single;
use raftpb_bindings::conf_change_single::Py_ConfChangeSingle_Owner;
use raftpb_bindings::conf_change_type::Py_ConfChangeType;
use raftpb_bindings::message_type::{
    is_local_msg as _is_local_msg, is_response_msg as _is_response_msg,
};

use external_bindings::slog::Py_Logger_Owner;
use raftpb_bindings::message_type::Py_MessageType;

// Global scope functions
#[pyfunction]
pub fn majority(total: usize) -> usize {
    _majority(total)
}

#[pyfunction]
pub fn default_logger() -> Py_Logger_Owner {
    Py_Logger_Owner {
        inner: _default_logger(),
    }
}

#[pyfunction]
pub fn vote_resp_msg_type(typ: &Py_MessageType) -> Py_MessageType {
    Py_MessageType(_vote_resp_msg_type(typ.0))
}

#[pyfunction]
pub fn new_conf_change_single(node_id: u64, typ: &Py_ConfChangeType) -> Py_ConfChangeSingle_Owner {
    Py_ConfChangeSingle_Owner {
        inner: _new_conf_change_single(node_id, typ.0),
    }
}

#[pyfunction]
pub fn is_local_msg(typ: &Py_MessageType) -> bool {
    _is_local_msg(typ.0)
}

#[pyfunction]
pub fn is_response_msg(typ: &Py_MessageType) -> bool {
    _is_response_msg(typ.0)
}

// Global scope constant
pub fn add_constants(m: &PyModule) -> PyResult<()> {
    m.add("CAMPAIGN_ELECTION", CAMPAIGN_ELECTION)?;
    m.add("CAMPAIGN_PRE_ELECTION", CAMPAIGN_PRE_ELECTION)?;
    m.add("CAMPAIGN_TRANSFER", CAMPAIGN_TRANSFER)?;
    m.add("INVALID_ID", INVALID_ID)?;
    m.add("INVALID_INDEX", INVALID_INDEX)?;
    m.add("NO_LIMIT", NO_LIMIT)?;

    Ok(())
}
