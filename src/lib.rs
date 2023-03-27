use prelude::global::add_constants;
use pyo3::prelude::*;

pub mod eraftpb;
pub mod internal;
pub mod prelude;
pub mod raw_node;
pub mod storage;

#[pymodule]
fn rraft(_py: Python, m: &PyModule) -> PyResult<()> {
    m.add_class::<eraftpb::conf_change_single::Py_ConfChangeSingle_Owner>()?;
    m.add_class::<eraftpb::conf_change_single::Py_ConfChangeSingle_Ref>()?;
    m.add_class::<eraftpb::conf_change_transition::Py_ConfChangeTransition>()?;
    m.add_class::<eraftpb::conf_change_type::Py_ConfChangeType>()?;
    m.add_class::<eraftpb::conf_change_v2::Py_ConfChangeV2_Owner>()?;
    m.add_class::<eraftpb::conf_change_v2::Py_ConfChangeV2_Ref>()?;
    m.add_class::<eraftpb::conf_change::Py_ConfChange_Owner>()?;
    m.add_class::<eraftpb::conf_change::Py_ConfChange_Ref>()?;
    m.add_class::<eraftpb::conf_state::Py_ConfState_Owner>()?;
    m.add_class::<eraftpb::conf_state::Py_ConfState_Ref>()?;
    m.add_class::<eraftpb::entry_type::Py_EntryType>()?;
    m.add_class::<eraftpb::entry::Py_Entry_Owner>()?;
    m.add_class::<eraftpb::entry::Py_Entry_Ref>()?;
    m.add_class::<eraftpb::hard_state::Py_HardState_Owner>()?;
    m.add_class::<eraftpb::hard_state::Py_HardState_Ref>()?;
    m.add_class::<eraftpb::message_type::Py_MessageType>()?;
    m.add_class::<eraftpb::message::Py_Message_Owner>()?;
    m.add_class::<eraftpb::message::Py_Message_Ref>()?;
    m.add_class::<eraftpb::snapshot_metadata::Py_SnapshotMetadata_Owner>()?;
    m.add_class::<eraftpb::snapshot_metadata::Py_SnapshotMetadata_Ref>()?;
    m.add_class::<eraftpb::snapshot::Py_Snapshot_Owner>()?;
    m.add_class::<eraftpb::snapshot::Py_Snapshot_Ref>()?;
    m.add_class::<internal::slog::Py_Logger_Owner>()?;
    m.add_class::<internal::slog::Py_Logger_Ref>()?;
    m.add_class::<internal::slog::Py_OverflowStrategy>()?;
    m.add_class::<prelude::config::Py_Config_Owner>()?;
    m.add_class::<prelude::config::Py_Config_Ref>()?;
    m.add_class::<prelude::error::Py_RaftError>()?;
    m.add_class::<prelude::error::Py_StorageError>()?;
    m.add_class::<prelude::inflights::Py_Inflights_Owner>()?;
    m.add_class::<prelude::inflights::Py_Inflights_Ref>()?;
    m.add_class::<prelude::joint_config::Py_JointConfig_Owner>()?;
    m.add_class::<prelude::joint_config::Py_JointConfig_Ref>()?;
    m.add_class::<prelude::majority_config::Py_MajorityConfig_Owner>()?;
    m.add_class::<prelude::majority_config::Py_MajorityConfig_Ref>()?;
    m.add_class::<prelude::progress_state::Py_ProgressState>()?;
    m.add_class::<prelude::progress_tracker::Py_ProgressTracker_Owner>()?;
    m.add_class::<prelude::progress_tracker::Py_ProgressTracker_Ref>()?;
    m.add_class::<prelude::progress::Py_Progress_Owner>()?;
    m.add_class::<prelude::progress::Py_Progress_Ref>()?;
    m.add_class::<prelude::raft_log::Py_RaftLog__MemStorage_Owner>()?;
    m.add_class::<prelude::raft_log::Py_RaftLog__MemStorage_Ref>()?;
    m.add_class::<prelude::raft_log::Py_RaftLog__PyStorage_Owner>()?;
    m.add_class::<prelude::raft_log::Py_RaftLog__PyStorage_Ref>()?;
    m.add_class::<prelude::raft::Py_Raft__MemStorage_Owner>()?;
    m.add_class::<prelude::raft::Py_Raft__MemStorage_Ref>()?;
    m.add_class::<prelude::raft::Py_Raft__PyStorage_Owner>()?;
    m.add_class::<prelude::raft::Py_Raft__PyStorage_Ref>()?;
    m.add_class::<prelude::read_state::Py_ReadState_Owner>()?;
    m.add_class::<prelude::read_state::Py_ReadState_Ref>()?;
    m.add_class::<prelude::readonly_option::Py_ReadOnlyOption>()?;
    m.add_class::<prelude::snapshot_status::Py_SnapshotStatus>()?;
    m.add_class::<prelude::soft_state::Py_SoftState_Owner>()?;
    m.add_class::<prelude::soft_state::Py_SoftState_Ref>()?;
    m.add_class::<prelude::state_role::Py_StateRole>()?;
    m.add_class::<prelude::status::Py_Status__MemStorage_Owner>()?;
    m.add_class::<prelude::status::Py_Status__MemStorage_Ref>()?;
    m.add_class::<prelude::unstable::Py_Unstable_Owner>()?;
    m.add_class::<prelude::unstable::Py_Unstable_Ref>()?;
    m.add_class::<raw_node::light_ready::Py_LightReady_Owner>()?;
    m.add_class::<raw_node::light_ready::Py_LightReady_Ref>()?;
    m.add_class::<raw_node::peer::Py_Peer_Owner>()?;
    m.add_class::<raw_node::peer::Py_Peer_Ref>()?;
    m.add_class::<raw_node::raw_node::Py_RawNode__MemStorage_Owner>()?;
    m.add_class::<raw_node::raw_node::Py_RawNode__MemStorage_Ref>()?;
    m.add_class::<raw_node::ready::Py_Ready_Owner>()?;
    m.add_class::<raw_node::ready::Py_Ready_Ref>()?;
    m.add_class::<storage::mem_storage_core::Py_MemStorageCore_Owner>()?;
    m.add_class::<storage::mem_storage_core::Py_MemStorageCore_Ref>()?;
    m.add_class::<storage::mem_storage::Py_MemStorage_Owner>()?;
    m.add_class::<storage::mem_storage::Py_MemStorage_Ref>()?;
    m.add_class::<storage::raft_state::Py_RaftState_Owner>()?;
    m.add_class::<storage::raft_state::Py_RaftState_Ref>()?;
    m.add_class::<storage::py_storage::Py_Storage>()?;

    m.add_function(wrap_pyfunction!(prelude::global::majority, m)?)?;
    m.add_function(wrap_pyfunction!(prelude::global::default_logger, m)?)?;
    m.add_function(wrap_pyfunction!(prelude::global::vote_resp_msg_type, m)?)?;
    m.add_function(wrap_pyfunction!(prelude::global::is_local_msg, m)?)?;
    m.add_function(wrap_pyfunction!(prelude::global::is_response_msg, m)?)?;
    m.add_function(wrap_pyfunction!(
        prelude::global::new_conf_change_single,
        m
    )?)?;

    add_constants(m)?;

    Ok(())
}
