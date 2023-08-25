use std::sync::{Arc, Mutex};

use pyo3::prelude::*;

use crate::raftpb_bindings::conf_change::new_conf_change_single as _new_conf_change_single;
use crate::raftpb_bindings::conf_change_single::PyConfChangeSingle;
use crate::raftpb_bindings::conf_change_type::PyConfChangeType;
use crate::raftpb_bindings::message_type::{
    is_local_msg as _is_local_msg, is_response_msg as _is_response_msg,
};
use raft::default_logger as _default_logger;
use raft::majority as _majority;
use raft::vote_resp_msg_type as _vote_resp_msg_type;
use raft::{
    CAMPAIGN_ELECTION, CAMPAIGN_PRE_ELECTION, CAMPAIGN_TRANSFER, INVALID_ID, INVALID_INDEX,
    NO_LIMIT,
};

use crate::external_bindings::slog::{LoggerMode, PyLogger};
use crate::raftpb_bindings::message_type::PyMessageType;
use crate::utils::reference::RefMutOwner;

// Global scope functions
#[pyfunction]
pub fn majority(total: usize) -> usize {
    _majority(total)
}

#[pyfunction]
pub fn default_logger() -> PyLogger {
    PyLogger {
        inner: RefMutOwner::new(_default_logger()),
        mutex: Arc::new(Mutex::new(())),
        mode: LoggerMode::Stdout,
    }
}

#[pyfunction]
pub fn vote_resp_msg_type(typ: &PyMessageType) -> PyMessageType {
    PyMessageType(_vote_resp_msg_type(typ.0))
}

#[pyfunction]
pub fn new_conf_change_single(node_id: u64, typ: &PyConfChangeType) -> PyConfChangeSingle {
    PyConfChangeSingle {
        inner: RefMutOwner::new(_new_conf_change_single(node_id, typ.0)),
    }
}

#[pyfunction]
pub fn is_local_msg(typ: &PyMessageType) -> bool {
    _is_local_msg(typ.0)
}

#[pyfunction]
pub fn is_response_msg(typ: &PyMessageType) -> bool {
    _is_response_msg(typ.0)
}

// Global scope constants
pub fn add_constants(m: &PyModule) -> PyResult<()> {
    m.add("CAMPAIGN_ELECTION", CAMPAIGN_ELECTION)?;
    m.add("CAMPAIGN_PRE_ELECTION", CAMPAIGN_PRE_ELECTION)?;
    m.add("CAMPAIGN_TRANSFER", CAMPAIGN_TRANSFER)?;
    m.add("INVALID_ID", INVALID_ID)?;
    m.add("INVALID_INDEX", INVALID_INDEX)?;
    m.add("NO_LIMIT", NO_LIMIT)?;

    Ok(())
}
