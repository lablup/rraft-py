#![allow(non_snake_case)]
#![allow(clippy::module_inception)]
#![allow(clippy::new_without_default)]
#![allow(clippy::should_implement_trait)]
#![allow(clippy::wrong_self_convention)]

use pyo3::prelude::*;
use raft::derializer::set_custom_deserializer;
use utils::deserializer::MyDeserializer;

mod bindings;
mod external_bindings;
mod mem_storage_bindings;
mod py_storage_bindings;
mod raftpb_bindings;
mod utils;

#[pymodule]
fn rraft(py: Python, m: &PyModule) -> PyResult<()> {
    m.add_class::<bindings::config::PyConfig>()?;
    m.add_class::<bindings::config::PyConfigRef>()?;
    m.add_class::<bindings::inflights::PyInflights>()?;
    m.add_class::<bindings::inflights::PyInflightsRef>()?;
    m.add_class::<bindings::joint_config::PyJointConfig>()?;
    m.add_class::<bindings::joint_config::PyJointConfigRef>()?;
    m.add_class::<bindings::light_ready::PyLightReady>()?;
    m.add_class::<bindings::light_ready::PyLightReadyRef>()?;
    m.add_class::<bindings::majority_config::PyMajorityConfig>()?;
    m.add_class::<bindings::majority_config::PyMajorityConfigRef>()?;
    m.add_class::<bindings::peer::PyPeer>()?;
    m.add_class::<bindings::peer::PyPeerRef>()?;
    m.add_class::<bindings::progress_state::PyProgressState>()?;
    m.add_class::<bindings::progress_tracker::PyProgressTracker>()?;
    m.add_class::<bindings::progress_tracker::PyProgressTrackerRef>()?;
    m.add_class::<bindings::progress::PyProgress>()?;
    m.add_class::<bindings::progress::PyProgressRef>()?;
    m.add_class::<bindings::raft_state::PyRaftState>()?;
    m.add_class::<bindings::raft_state::PyRaftStateRef>()?;
    m.add_class::<bindings::read_state::PyReadState>()?;
    m.add_class::<bindings::read_state::PyReadStateRef>()?;
    m.add_class::<bindings::readonly_option::PyReadOnlyOption>()?;
    m.add_class::<bindings::ready::PyReady>()?;
    m.add_class::<bindings::ready::PyReadyRef>()?;
    m.add_class::<bindings::snapshot_status::PySnapshotStatus>()?;
    m.add_class::<bindings::soft_state::PySoftState>()?;
    m.add_class::<bindings::soft_state::PySoftStateRef>()?;
    m.add_class::<bindings::state_role::PyStateRole>()?;
    m.add_class::<bindings::unstable::PyUnstable>()?;
    m.add_class::<bindings::unstable::PyUnstableRef>()?;
    m.add_class::<bindings::get_entries_context::PyGetEntriesContext>()?;
    m.add_class::<bindings::get_entries_context::PyGetEntriesContextRef>()?;

    m.add_class::<raftpb_bindings::conf_change_single::PyConfChangeSingle>()?;
    m.add_class::<raftpb_bindings::conf_change_single::PyConfChangeSingleRef>()?;
    m.add_class::<raftpb_bindings::conf_change_transition::PyConfChangeTransition>()?;
    m.add_class::<raftpb_bindings::conf_change_type::PyConfChangeType>()?;
    m.add_class::<raftpb_bindings::conf_change_v2::PyConfChangeV2>()?;
    m.add_class::<raftpb_bindings::conf_change_v2::PyConfChangeV2Ref>()?;
    m.add_class::<raftpb_bindings::conf_change::PyConfChange>()?;
    m.add_class::<raftpb_bindings::conf_change::PyConfChangeRef>()?;
    m.add_class::<raftpb_bindings::conf_state::PyConfState>()?;
    m.add_class::<raftpb_bindings::conf_state::PyConfStateRef>()?;
    m.add_class::<raftpb_bindings::entry_type::PyEntryType>()?;
    m.add_class::<raftpb_bindings::entry::PyEntry>()?;
    m.add_class::<raftpb_bindings::entry::PyEntryRef>()?;
    m.add_class::<raftpb_bindings::hard_state::PyHardState>()?;
    m.add_class::<raftpb_bindings::hard_state::PyHardStateRef>()?;
    m.add_class::<raftpb_bindings::message_type::PyMessageType>()?;
    m.add_class::<raftpb_bindings::message::PyMessage>()?;
    m.add_class::<raftpb_bindings::message::PyMessageRef>()?;
    m.add_class::<raftpb_bindings::snapshot_metadata::PySnapshotMetadata>()?;
    m.add_class::<raftpb_bindings::snapshot_metadata::PySnapshotMetadataRef>()?;
    m.add_class::<raftpb_bindings::snapshot::PySnapshot>()?;
    m.add_class::<raftpb_bindings::snapshot::PySnapshotRef>()?;

    m.add_class::<mem_storage_bindings::mem_storage_core::PyMemStorageCore>()?;
    m.add_class::<mem_storage_bindings::mem_storage_core::PyMemStorageCoreRef>()?;
    m.add_class::<mem_storage_bindings::mem_storage::PyMemStorage>()?;
    m.add_class::<mem_storage_bindings::mem_storage::PyMemStorageRef>()?;
    m.add_class::<mem_storage_bindings::raft_log::PyInMemoryRaftLog>()?;
    m.add_class::<mem_storage_bindings::raft_log::PyInMemoryRaftLogRef>()?;
    m.add_class::<mem_storage_bindings::raft::PyInMemoryRaft>()?;
    m.add_class::<mem_storage_bindings::raft::PyInMemoryRaftRef>()?;
    m.add_class::<mem_storage_bindings::raw_node::PyInMemoryRawNode>()?;
    m.add_class::<mem_storage_bindings::raw_node::PyInMemoryRawNodeRef>()?;

    m.add_class::<py_storage_bindings::py_storage::PyStorage>()?;
    m.add_class::<py_storage_bindings::py_storage::PyStorageRef>()?;
    m.add_class::<py_storage_bindings::raft_log::PyRaftLog>()?;
    m.add_class::<py_storage_bindings::raft_log::PyRaftLogRef>()?;
    m.add_class::<py_storage_bindings::raft::PyRaft>()?;
    m.add_class::<py_storage_bindings::raft::PyRaftRef>()?;
    m.add_class::<py_storage_bindings::raw_node::PyRawNode>()?;
    m.add_class::<py_storage_bindings::raw_node::PyRawNodeRef>()?;

    m.add_class::<external_bindings::slog::PyLogger>()?;
    m.add_class::<external_bindings::slog::PyLoggerRef>()?;
    m.add_class::<external_bindings::slog::PyOverflowStrategy>()?;

    m.add_class::<utils::errors::PyRaftError>()?;
    m.add_class::<utils::errors::PyStorageError>()?;

    m.add_function(wrap_pyfunction!(bindings::global::majority, m)?)?;
    m.add_function(wrap_pyfunction!(bindings::global::default_logger, m)?)?;
    m.add_function(wrap_pyfunction!(bindings::global::vote_resp_msg_type, m)?)?;
    m.add_function(wrap_pyfunction!(bindings::global::is_local_msg, m)?)?;
    m.add_function(wrap_pyfunction!(bindings::global::is_response_msg, m)?)?;
    m.add_function(wrap_pyfunction!(
        bindings::global::new_conf_change_single,
        m
    )?)?;

    m.add_function(wrap_pyfunction!(
        utils::deserializer::set_confchange_context_deserializer,
        m
    )?)?;

    m.add_function(wrap_pyfunction!(
        utils::deserializer::set_confchangev2_context_deserializer,
        m
    )?)?;

    m.add_function(wrap_pyfunction!(
        utils::deserializer::set_entry_context_deserializer,
        m
    )?)?;

    m.add_function(wrap_pyfunction!(
        utils::deserializer::set_entry_data_deserializer,
        m
    )?)?;

    m.add_function(wrap_pyfunction!(
        utils::deserializer::set_message_context_deserializer,
        m
    )?)?;

    m.add_function(wrap_pyfunction!(
        utils::deserializer::set_snapshot_data_deserializer,
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

    // IMPORTANT: Uncomment below line when you want to use raft-rs's upstream repository.
    set_custom_deserializer(MyDeserializer);

    Ok(())
}
