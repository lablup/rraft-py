#![allow(non_camel_case_types)]
#![allow(non_snake_case)]
#![allow(non_upper_case_globals)]
#![allow(clippy::module_inception)]
#![allow(clippy::new_without_default)]
#![allow(clippy::should_implement_trait)]

use pyo3::prelude::*;

mod bindings;
mod external_bindings;
mod mem_storage_bindings;
mod py_storage_bindings;
mod raftpb_bindings;
mod utils;

#[pymodule]
fn rraft(py: Python, m: &PyModule) -> PyResult<()> {
    m.add_class::<bindings::config::Py_Config>()?;
    m.add_class::<bindings::config::Py_Config_Ref>()?;
    m.add_class::<bindings::inflights::Py_Inflights>()?;
    m.add_class::<bindings::inflights::Py_Inflights_Ref>()?;
    m.add_class::<bindings::joint_config::Py_JointConfig>()?;
    m.add_class::<bindings::joint_config::Py_JointConfig_Ref>()?;
    m.add_class::<bindings::light_ready::Py_LightReady>()?;
    m.add_class::<bindings::light_ready::Py_LightReady_Ref>()?;
    m.add_class::<bindings::majority_config::Py_MajorityConfig>()?;
    m.add_class::<bindings::majority_config::Py_MajorityConfig_Ref>()?;
    m.add_class::<bindings::peer::Py_Peer>()?;
    m.add_class::<bindings::peer::Py_Peer_Ref>()?;
    m.add_class::<bindings::progress_state::Py_ProgressState>()?;
    m.add_class::<bindings::progress_tracker::Py_ProgressTracker>()?;
    m.add_class::<bindings::progress_tracker::Py_ProgressTracker_Ref>()?;
    m.add_class::<bindings::progress::Py_Progress>()?;
    m.add_class::<bindings::progress::Py_Progress_Ref>()?;
    m.add_class::<bindings::raft_state::Py_RaftState>()?;
    m.add_class::<bindings::raft_state::Py_RaftState_Ref>()?;
    m.add_class::<bindings::read_state::Py_ReadState>()?;
    m.add_class::<bindings::read_state::Py_ReadState_Ref>()?;
    m.add_class::<bindings::readonly_option::Py_ReadOnlyOption>()?;
    m.add_class::<bindings::ready::Py_Ready>()?;
    m.add_class::<bindings::ready::Py_Ready_Ref>()?;
    m.add_class::<bindings::snapshot_status::Py_SnapshotStatus>()?;
    m.add_class::<bindings::soft_state::Py_SoftState>()?;
    m.add_class::<bindings::soft_state::Py_SoftState_Ref>()?;
    m.add_class::<bindings::state_role::Py_StateRole>()?;
    m.add_class::<bindings::unstable::Py_Unstable>()?;
    m.add_class::<bindings::unstable::Py_Unstable_Ref>()?;
    m.add_class::<bindings::get_entries_context::Py_GetEntriesContext>()?;
    m.add_class::<bindings::get_entries_context::Py_GetEntriesContext_Ref>()?;

    m.add_class::<raftpb_bindings::conf_change_single::Py_ConfChangeSingle>()?;
    m.add_class::<raftpb_bindings::conf_change_single::Py_ConfChangeSingle_Ref>()?;
    m.add_class::<raftpb_bindings::conf_change_transition::Py_ConfChangeTransition>()?;
    m.add_class::<raftpb_bindings::conf_change_type::Py_ConfChangeType>()?;
    m.add_class::<raftpb_bindings::conf_change_v2::Py_ConfChangeV2>()?;
    m.add_class::<raftpb_bindings::conf_change_v2::Py_ConfChangeV2_Ref>()?;
    m.add_class::<raftpb_bindings::conf_change::Py_ConfChange>()?;
    m.add_class::<raftpb_bindings::conf_change::Py_ConfChange_Ref>()?;
    m.add_class::<raftpb_bindings::conf_state::Py_ConfState>()?;
    m.add_class::<raftpb_bindings::conf_state::Py_ConfState_Ref>()?;
    m.add_class::<raftpb_bindings::entry_type::Py_EntryType>()?;
    m.add_class::<raftpb_bindings::entry::Py_Entry>()?;
    m.add_class::<raftpb_bindings::entry::Py_Entry_Ref>()?;
    m.add_class::<raftpb_bindings::hard_state::Py_HardState>()?;
    m.add_class::<raftpb_bindings::hard_state::Py_HardState_Ref>()?;
    m.add_class::<raftpb_bindings::message_type::Py_MessageType>()?;
    m.add_class::<raftpb_bindings::message::Py_Message>()?;
    m.add_class::<raftpb_bindings::message::Py_Message_Ref>()?;
    m.add_class::<raftpb_bindings::snapshot_metadata::Py_SnapshotMetadata>()?;
    m.add_class::<raftpb_bindings::snapshot_metadata::Py_SnapshotMetadata_Ref>()?;
    m.add_class::<raftpb_bindings::snapshot::Py_Snapshot>()?;
    m.add_class::<raftpb_bindings::snapshot::Py_Snapshot_Ref>()?;

    m.add_class::<mem_storage_bindings::mem_storage_core::Py_MemStorageCore>()?;
    m.add_class::<mem_storage_bindings::mem_storage_core::Py_MemStorageCore_Ref>()?;
    m.add_class::<mem_storage_bindings::mem_storage::Py_MemStorage>()?;
    m.add_class::<mem_storage_bindings::mem_storage::Py_MemStorage_Ref>()?;
    m.add_class::<mem_storage_bindings::raft_log::Py_InMemoryRaftLog>()?;
    m.add_class::<mem_storage_bindings::raft_log::Py_InMemoryRaftLog_Ref>()?;
    m.add_class::<mem_storage_bindings::raft::Py_InMemoryRaft>()?;
    m.add_class::<mem_storage_bindings::raft::Py_InMemoryRaft_Ref>()?;
    m.add_class::<mem_storage_bindings::raw_node::Py_InMemoryRawNode>()?;
    m.add_class::<mem_storage_bindings::raw_node::Py_InMemoryRawNode_Ref>()?;

    m.add_class::<py_storage_bindings::py_storage::Py_Storage>()?;
    m.add_class::<py_storage_bindings::py_storage::Py_Storage_Ref>()?;
    m.add_class::<py_storage_bindings::raft_log::Py_RaftLog>()?;
    m.add_class::<py_storage_bindings::raft_log::Py_RaftLog_Ref>()?;
    m.add_class::<py_storage_bindings::raft::Py_Raft>()?;
    m.add_class::<py_storage_bindings::raft::Py_Raft_Ref>()?;
    m.add_class::<py_storage_bindings::raw_node::Py_RawNode>()?;
    m.add_class::<py_storage_bindings::raw_node::Py_RawNode_Ref>()?;

    m.add_class::<external_bindings::slog::Py_Logger>()?;
    m.add_class::<external_bindings::slog::Py_Logger_Ref>()?;
    m.add_class::<external_bindings::slog::Py_OverflowStrategy>()?;

    m.add_class::<utils::errors::Py_RaftError>()?;
    m.add_class::<utils::errors::Py_StorageError>()?;

    m.add_function(wrap_pyfunction!(bindings::global::majority, m)?)?;
    m.add_function(wrap_pyfunction!(bindings::global::default_logger, m)?)?;
    m.add_function(wrap_pyfunction!(bindings::global::vote_resp_msg_type, m)?)?;
    m.add_function(wrap_pyfunction!(bindings::global::is_local_msg, m)?)?;
    m.add_function(wrap_pyfunction!(bindings::global::is_response_msg, m)?)?;
    m.add_function(wrap_pyfunction!(
        bindings::global::new_conf_change_single,
        m
    )?)?;

    m.add(
        "DestroyedRefUsedError",
        py.get_type::<utils::errors::DestroyedRefUsedError>(),
    )?;

    m.add("RaftError", py.get_type::<utils::errors::RaftError>())?;
    m.add(
        "RaftStorageError",
        py.get_type::<utils::errors::RaftStorageError>(),
    )?;
    m.add(
        "CompactedError",
        py.get_type::<utils::errors::CompactedError>(),
    )?;
    m.add(
        "SnapshotOutOfDateError",
        py.get_type::<utils::errors::SnapshotOutOfDateError>(),
    )?;
    m.add(
        "SnapshotTemporarilyUnavailableError",
        py.get_type::<utils::errors::SnapshotTemporarilyUnavailableError>(),
    )?;
    m.add(
        "UnavailableError",
        py.get_type::<utils::errors::UnavailableError>(),
    )?;
    m.add(
        "LogTemporarilyUnavailableError",
        py.get_type::<utils::errors::LogTemporarilyUnavailableError>(),
    )?;
    m.add("OtherError", py.get_type::<utils::errors::OtherError>())?;

    m.add("ExistsError", py.get_type::<utils::errors::ExistsError>())?;
    m.add(
        "NotExistsError",
        py.get_type::<utils::errors::NotExistsError>(),
    )?;
    m.add(
        "ConfChangeError",
        py.get_type::<utils::errors::ConfChangeError>(),
    )?;
    m.add(
        "ConfigInvalidError",
        py.get_type::<utils::errors::ConfigInvalidError>(),
    )?;
    m.add("IoError", py.get_type::<utils::errors::IoError>())?;
    m.add("CodecError", py.get_type::<utils::errors::CodecError>())?;
    m.add("StoreError", py.get_type::<utils::errors::StoreError>())?;
    m.add(
        "StepLocalMsgError",
        py.get_type::<utils::errors::StepLocalMsgError>(),
    )?;
    m.add(
        "StepPeerNotFoundError",
        py.get_type::<utils::errors::StepPeerNotFoundError>(),
    )?;
    m.add(
        "ProposalDroppedError",
        py.get_type::<utils::errors::ProposalDroppedError>(),
    )?;
    m.add(
        "RequestSnapshotDroppedError",
        py.get_type::<utils::errors::RequestSnapshotDroppedError>(),
    )?;

    bindings::global::add_constants(m)?;

    Ok(())
}
