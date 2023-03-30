use bindings::global::add_constants;
use pyo3::prelude::*;

#[pymodule]
fn rraft(_py: Python, m: &PyModule) -> PyResult<()> {
    m.add_class::<bindings::config::Py_Config_Owner>()?;
    m.add_class::<bindings::config::Py_Config_Ref>()?;
    m.add_class::<bindings::error::Py_RaftError>()?;
    m.add_class::<bindings::error::Py_StorageError>()?;
    m.add_class::<bindings::inflights::Py_Inflights_Owner>()?;
    m.add_class::<bindings::inflights::Py_Inflights_Ref>()?;
    m.add_class::<bindings::joint_config::Py_JointConfig_Owner>()?;
    m.add_class::<bindings::joint_config::Py_JointConfig_Ref>()?;
    m.add_class::<bindings::light_ready::Py_LightReady_Owner>()?;
    m.add_class::<bindings::light_ready::Py_LightReady_Ref>()?;
    m.add_class::<bindings::majority_config::Py_MajorityConfig_Owner>()?;
    m.add_class::<bindings::majority_config::Py_MajorityConfig_Ref>()?;
    m.add_class::<bindings::peer::Py_Peer_Owner>()?;
    m.add_class::<bindings::peer::Py_Peer_Ref>()?;
    m.add_class::<bindings::progress_state::Py_ProgressState>()?;
    m.add_class::<bindings::progress_tracker::Py_ProgressTracker_Owner>()?;
    m.add_class::<bindings::progress_tracker::Py_ProgressTracker_Ref>()?;
    m.add_class::<bindings::progress::Py_Progress_Owner>()?;
    m.add_class::<bindings::progress::Py_Progress_Ref>()?;
    m.add_class::<bindings::raft_state::Py_RaftState_Owner>()?;
    m.add_class::<bindings::raft_state::Py_RaftState_Ref>()?;
    m.add_class::<bindings::read_state::Py_ReadState_Owner>()?;
    m.add_class::<bindings::read_state::Py_ReadState_Ref>()?;
    m.add_class::<bindings::readonly_option::Py_ReadOnlyOption>()?;
    m.add_class::<bindings::ready::Py_Ready_Owner>()?;
    m.add_class::<bindings::ready::Py_Ready_Ref>()?;
    m.add_class::<bindings::snapshot_status::Py_SnapshotStatus>()?;
    m.add_class::<bindings::soft_state::Py_SoftState_Owner>()?;
    m.add_class::<bindings::soft_state::Py_SoftState_Ref>()?;
    m.add_class::<bindings::state_role::Py_StateRole>()?;
    m.add_class::<bindings::unstable::Py_Unstable_Owner>()?;
    m.add_class::<bindings::unstable::Py_Unstable_Ref>()?;

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

    m.add_class::<mem_storage::raft_log::Py_RaftLog__MemStorage_Owner>()?;
    m.add_class::<mem_storage::raft_log::Py_RaftLog__MemStorage_Ref>()?;
    m.add_class::<mem_storage::raft::Py_Raft__MemStorage_Owner>()?;
    m.add_class::<mem_storage::raft::Py_Raft__MemStorage_Ref>()?;
    m.add_class::<mem_storage::raw_node::Py_RawNode__MemStorage_Owner>()?;
    m.add_class::<mem_storage::raw_node::Py_RawNode__MemStorage_Ref>()?;
    m.add_class::<mem_storage::mem_storage_core::Py_MemStorageCore_Owner>()?;
    m.add_class::<mem_storage::mem_storage_core::Py_MemStorageCore_Ref>()?;
    m.add_class::<mem_storage::mem_storage::Py_MemStorage_Owner>()?;
    m.add_class::<mem_storage::mem_storage::Py_MemStorage_Ref>()?;

    // m.add_class::<py_storage::raft::Py_Raft__PyStorage_Owner>()?;
    // m.add_class::<py_storage::raft::Py_Raft__PyStorage_Ref>()?;
    // m.add_class::<py_storage::raft_log::Py_RaftLog__PyStorage_Owner>()?;
    // m.add_class::<py_storage::raft_log::Py_RaftLog__PyStorage_Ref>()?;
    // m.add_class::<py_storage::py_storage::Py_Storage>()?;

    m.add_class::<external::slog::Py_Logger_Owner>()?;
    m.add_class::<external::slog::Py_Logger_Ref>()?;
    m.add_class::<external::slog::Py_OverflowStrategy>()?;

    m.add_function(wrap_pyfunction!(bindings::global::majority, m)?)?;
    m.add_function(wrap_pyfunction!(bindings::global::default_logger, m)?)?;
    m.add_function(wrap_pyfunction!(bindings::global::vote_resp_msg_type, m)?)?;
    m.add_function(wrap_pyfunction!(bindings::global::is_local_msg, m)?)?;
    m.add_function(wrap_pyfunction!(bindings::global::is_response_msg, m)?)?;
    m.add_function(wrap_pyfunction!(
        bindings::global::new_conf_change_single,
        m
    )?)?;

    add_constants(m)?;

    Ok(())
}
