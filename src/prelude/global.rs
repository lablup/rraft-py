use pyo3::prelude::*;

use raft::default_logger as _default_logger;
use raft::majority as _majority;
use raft::vote_resp_msg_type as _vote_resp_msg_type;
use raft::{
    CAMPAIGN_ELECTION, CAMPAIGN_PRE_ELECTION, CAMPAIGN_TRANSFER, INVALID_ID, INVALID_INDEX,
    NO_LIMIT,
};

use crate::eraftpb::message_type::Py_MessageType;
use crate::internal::slog::Py_Logger_Owner;

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
