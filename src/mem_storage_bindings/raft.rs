use crate::utils::{
    reference::{RefMutContainer, RefMutOwner},
    unsafe_cast::make_mut,
};
use pyo3::{
    intern,
    prelude::*,
    types::{PyList, PyString},
};

use raft::{
    storage::MemStorage, Raft, CAMPAIGN_ELECTION, CAMPAIGN_PRE_ELECTION, CAMPAIGN_TRANSFER,
};

use crate::raftpb_bindings::{
    conf_change_v2::PyConfChangeV2Mut,
    conf_state::PyConfStateRef,
    entry::PyEntryMut,
    hard_state::{PyHardState, PyHardStateMut},
    message::{PyMessage, PyMessageMut, PyMessageRef},
    snapshot::{PySnapshotMut, PySnapshotRef},
};

use crate::bindings::{
    config::PyConfigMut,
    progress_tracker::PyProgressTrackerRef,
    read_state::{PyReadState, PyReadStateMut},
    readonly_option::PyReadOnlyOption,
    soft_state::PySoftState,
    state_role::PyStateRole,
};
use crate::external_bindings::slog::PyLoggerMut;

use super::raft_log::PyInMemoryRaftLogRef;
use crate::utils::errors::PyRaftError;

use super::mem_storage::{PyMemStorageMut, PyMemStorageRef};

#[pyclass(name = "InMemoryRaft")]
pub struct PyInMemoryRaft {
    pub inner: RefMutOwner<Raft<MemStorage>>,
}

#[pyclass(name = "InMemoryRaftRef")]
pub struct PyInMemoryRaftRef {
    pub inner: RefMutContainer<Raft<MemStorage>>,
}

#[pymethods]
impl PyInMemoryRaft {
    #[new]
    pub fn new(cfg: PyConfigMut, store: PyMemStorageMut, logger: PyLoggerMut) -> PyResult<Self> {
        Raft::new(&cfg.into(), store.into(), &logger.into())
            .map(|r| PyInMemoryRaft {
                inner: RefMutOwner::new(r),
            })
            .map_err(|e| PyRaftError(e).into())
    }

    pub fn make_ref(&mut self) -> PyInMemoryRaftRef {
        PyInMemoryRaftRef {
            inner: RefMutContainer::new(&mut self.inner),
        }
    }

    fn __getattr__(this: PyObject, py: Python, attr: &str) -> PyResult<PyObject> {
        let reference = this.call_method0(py, intern!(py, "make_ref"))?;
        reference.getattr(py, attr)
    }
}

#[pymethods]
impl PyInMemoryRaftRef {
    pub fn append_entry(&mut self, ents: &PyList) -> PyResult<bool> {
        let mut entries = ents.extract::<Vec<PyEntryMut>>()?;

        self.inner.map_as_mut(|inner| {
            inner.append_entry(
                entries
                    .iter_mut()
                    .map(|x| x.into())
                    .collect::<Vec<_>>()
                    .as_mut_slice(),
            )
        })
    }

    pub fn send_append(&mut self, to: u64) -> PyResult<()> {
        self.inner.map_as_mut(|inner| inner.send_append(to))
    }

    pub fn apply_to_current_term(&self) -> PyResult<bool> {
        self.inner.map_as_ref(|inner| inner.apply_to_current_term())
    }

    pub fn commit_to_current_term(&self) -> PyResult<bool> {
        self.inner
            .map_as_ref(|inner| inner.commit_to_current_term())
    }

    pub fn group_commit(&self) -> PyResult<bool> {
        self.inner.map_as_ref(|inner| inner.group_commit())
    }

    pub fn enable_group_commit(&mut self, enable: bool) -> PyResult<()> {
        self.inner
            .map_as_mut(|inner| inner.enable_group_commit(enable))
    }

    pub fn clear_commit_group(&mut self) -> PyResult<()> {
        self.inner.map_as_mut(|inner| inner.clear_commit_group())
    }

    pub fn check_group_commit_consistent(&mut self) -> PyResult<Option<bool>> {
        self.inner
            .map_as_mut(|inner| inner.check_group_commit_consistent())
    }

    pub fn assign_commit_groups(&mut self, ids: &PyList) -> PyResult<()> {
        let ids = ids.extract::<Vec<(u64, u64)>>()?;

        self.inner
            .map_as_mut(|inner| inner.assign_commit_groups(ids.as_slice()))
    }

    pub fn commit_apply(&mut self, applied: u64) -> PyResult<()> {
        self.inner.map_as_mut(|inner| inner.commit_apply(applied))
    }

    pub fn maybe_commit(&mut self) -> PyResult<bool> {
        self.inner.map_as_mut(|inner| inner.maybe_commit())
    }

    pub fn uncommitted_size(&self) -> PyResult<usize> {
        self.inner.map_as_ref(|inner| inner.uncommitted_size())
    }

    pub fn maybe_increase_uncommitted_size(&mut self, ents: &PyList) -> PyResult<bool> {
        let mut entries = ents.extract::<Vec<PyEntryMut>>()?;

        self.inner.map_as_mut(|inner| {
            inner.maybe_increase_uncommitted_size(
                entries
                    .iter_mut()
                    .map(|x| x.into())
                    .collect::<Vec<_>>()
                    .as_slice(),
            )
        })
    }

    pub fn reduce_uncommitted_size(&mut self, ents: &PyList) -> PyResult<()> {
        let mut entries = ents.extract::<Vec<PyEntryMut>>()?;

        self.inner.map_as_mut(|inner| {
            inner.reduce_uncommitted_size(
                entries
                    .iter_mut()
                    .map(|x| x.into())
                    .collect::<Vec<_>>()
                    .as_slice(),
            )
        })
    }

    pub fn restore(&mut self, snap: PySnapshotMut) -> PyResult<bool> {
        self.inner.map_as_mut(|inner| inner.restore(snap.into()))
    }

    pub fn bcast_append(&mut self) -> PyResult<()> {
        self.inner.map_as_mut(|inner| inner.bcast_append())
    }

    pub fn bcast_heartbeat(&mut self) -> PyResult<()> {
        self.inner.map_as_mut(|inner| inner.bcast_heartbeat())
    }

    pub fn should_bcast_commit(&mut self) -> PyResult<bool> {
        self.inner.map_as_mut(|inner| inner.should_bcast_commit())
    }

    pub fn skip_bcast_commit(&mut self, skip: bool) -> PyResult<()> {
        self.inner.map_as_mut(|inner| inner.skip_bcast_commit(skip))
    }

    pub fn become_leader(&mut self) -> PyResult<()> {
        self.inner.map_as_mut(|inner| inner.become_leader())
    }

    pub fn become_follower(&mut self, term: u64, leader_id: u64) -> PyResult<()> {
        self.inner
            .map_as_mut(|inner| inner.become_follower(term, leader_id))
    }

    pub fn become_pre_candidate(&mut self) -> PyResult<()> {
        self.inner.map_as_mut(|inner| inner.become_pre_candidate())
    }

    pub fn become_candidate(&mut self) -> PyResult<()> {
        self.inner.map_as_mut(|inner| inner.become_candidate())
    }

    pub fn heartbeat_timeout(&self) -> PyResult<usize> {
        self.inner.map_as_ref(|inner| inner.heartbeat_timeout())
    }

    pub fn heartbeat_elapsed(&self) -> PyResult<usize> {
        self.inner.map_as_ref(|inner| inner.heartbeat_elapsed())
    }

    pub fn election_timeout(&self) -> PyResult<usize> {
        self.inner.map_as_ref(|inner| inner.election_timeout())
    }

    pub fn randomized_election_timeout(&self) -> PyResult<usize> {
        self.inner
            .map_as_ref(|inner| inner.randomized_election_timeout())
    }

    pub fn set_randomized_election_timeout(&mut self, t: usize) -> PyResult<()> {
        self.inner
            .map_as_mut(|inner| inner.set_randomized_election_timeout(t))
    }

    pub fn reset_randomized_election_timeout(&mut self) -> PyResult<()> {
        self.inner
            .map_as_mut(|inner| inner.reset_randomized_election_timeout())
    }

    pub fn pass_election_timeout(&self) -> PyResult<bool> {
        self.inner.map_as_ref(|inner| inner.pass_election_timeout())
    }

    pub fn send_timeout_now(&mut self, to: u64) -> PyResult<()> {
        self.inner.map_as_mut(|inner| inner.send_timeout_now(to))
    }

    pub fn ready_read_count(&self) -> PyResult<usize> {
        self.inner.map_as_ref(|inner| inner.ready_read_count())
    }

    pub fn pending_read_count(&self) -> PyResult<usize> {
        self.inner.map_as_ref(|inner| inner.pending_read_count())
    }

    pub fn load_state(&mut self, hs: PyHardStateMut) -> PyResult<()> {
        self.inner.map_as_mut(|inner| inner.load_state(&hs.into()))
    }

    pub fn soft_state(&self) -> PyResult<PySoftState> {
        self.inner.map_as_ref(|inner| PySoftState {
            inner: RefMutOwner::new(inner.soft_state()),
        })
    }

    pub fn hard_state(&self) -> PyResult<PyHardState> {
        self.inner.map_as_ref(|inner| PyHardState {
            inner: RefMutOwner::new(inner.hard_state()),
        })
    }

    pub fn ping(&mut self) -> PyResult<()> {
        self.inner.map_as_mut(|inner| inner.ping())
    }

    pub fn apply_conf_change(&mut self, cc: PyConfChangeV2Mut) -> PyResult<PyConfStateRef> {
        self.inner.map_as_mut(|inner| {
            inner
                .apply_conf_change(&cc.into())
                .map(|cs| PyConfStateRef {
                    inner: RefMutContainer::new_raw(unsafe { make_mut(&cs) }),
                })
                .map_err(|e| PyRaftError(e).into())
        })?
    }

    pub fn tick(&mut self) -> PyResult<bool> {
        self.inner.map_as_mut(|inner| inner.tick())
    }

    pub fn tick_election(&mut self) -> PyResult<bool> {
        self.inner.map_as_mut(|inner| inner.tick_election())
    }

    pub fn promotable(&mut self) -> PyResult<bool> {
        self.inner.map_as_mut(|inner| inner.promotable())
    }

    pub fn step(&mut self, msg: PyMessageMut) -> PyResult<()> {
        self.inner
            .map_as_mut(|inner| inner.step(msg.into()).map_err(|e| PyRaftError(e).into()))?
    }

    pub fn has_pending_conf(&self) -> PyResult<bool> {
        self.inner.map_as_ref(|inner| inner.has_pending_conf())
    }

    pub fn post_conf_change(&mut self) -> PyResult<PyConfStateRef> {
        self.inner.map_as_mut(|inner| PyConfStateRef {
            inner: RefMutContainer::new_raw(&mut inner.post_conf_change()),
        })
    }

    pub fn in_lease(&self) -> PyResult<bool> {
        self.inner.map_as_ref(|inner| inner.in_lease())
    }

    pub fn handle_heartbeat(&mut self, msg: PyMessageMut) -> PyResult<()> {
        self.inner
            .map_as_mut(|inner| inner.handle_heartbeat(msg.into()))
    }

    pub fn handle_append_entries(&mut self, msg: PyMessageMut) -> PyResult<()> {
        self.inner
            .map_as_mut(|inner| inner.handle_append_entries(&msg.into()))
    }

    pub fn request_snapshot(&mut self) -> PyResult<()> {
        self.inner
            .map_as_mut(|inner| inner.request_snapshot().map_err(|e| PyRaftError(e).into()))?
    }

    pub fn prs(&mut self) -> PyResult<PyProgressTrackerRef> {
        self.inner.map_as_mut(|inner| PyProgressTrackerRef {
            inner: RefMutContainer::new_raw(inner.mut_prs()),
        })
    }

    pub fn reset(&mut self, term: u64) -> PyResult<()> {
        self.inner.map_as_mut(|inner| inner.reset(term))
    }

    pub fn snap(&self) -> PyResult<Option<PySnapshotRef>> {
        self.inner.map_as_ref(|inner| {
            inner.snap().map(|snapshot| PySnapshotRef {
                inner: RefMutContainer::new_raw(unsafe { make_mut(snapshot) }),
            })
        })
    }

    pub fn on_persist_snap(&mut self, index: u64) -> PyResult<()> {
        self.inner.map_as_mut(|inner| inner.on_persist_snap(index))
    }

    pub fn on_persist_entries(&mut self, index: u64, term: u64) -> PyResult<()> {
        self.inner
            .map_as_mut(|inner| inner.on_persist_entries(index, term))
    }

    pub fn abort_leader_transfer(&mut self) -> PyResult<()> {
        self.inner.map_as_mut(|inner| inner.abort_leader_transfer())
    }

    pub fn get_lead_transferee(&self) -> PyResult<Option<u64>> {
        self.inner.map_as_ref(|inner| inner.lead_transferee)
    }

    pub fn set_lead_transferee(&mut self, v: Option<u64>) -> PyResult<()> {
        self.inner.map_as_mut(|inner| inner.lead_transferee = v)
    }

    pub fn get_term(&self) -> PyResult<u64> {
        self.inner.map_as_ref(|inner| inner.term)
    }

    pub fn set_term(&mut self, v: u64) -> PyResult<()> {
        self.inner.map_as_mut(|inner| inner.term = v)
    }

    pub fn get_vote(&self) -> PyResult<u64> {
        self.inner.map_as_ref(|inner| inner.vote)
    }

    pub fn set_vote(&mut self, v: u64) -> PyResult<()> {
        self.inner.map_as_mut(|inner| inner.vote = v)
    }

    pub fn get_priority(&self) -> PyResult<i64> {
        self.inner.map_as_ref(|inner| inner.priority)
    }

    pub fn set_priority(&mut self, priority: i64) -> PyResult<()> {
        self.inner.map_as_mut(|inner| {
            inner.set_priority(priority);
        })
    }

    pub fn get_leader_id(&self) -> PyResult<u64> {
        self.inner.map_as_ref(|inner| inner.leader_id)
    }

    pub fn set_leader_id(&mut self, v: u64) -> PyResult<()> {
        self.inner.map_as_mut(|inner| inner.leader_id = v)
    }

    pub fn get_read_states(&self, py: Python) -> PyResult<PyObject> {
        self.inner.map_as_ref(|inner| {
            inner
                .read_states
                .iter()
                .map(|rs| PyReadState {
                    inner: RefMutOwner::new(rs.clone()),
                })
                .collect::<Vec<_>>()
                .into_py(py)
        })
    }

    pub fn set_read_states(&mut self, v: &PyList) -> PyResult<()> {
        let mut read_states = v.extract::<Vec<PyReadStateMut>>()?;

        self.inner.map_as_mut(|inner| {
            inner.read_states = read_states
                .iter_mut()
                .map(|rs| rs.into())
                .collect::<Vec<_>>()
        })
    }

    pub fn get_id(&self) -> PyResult<u64> {
        self.inner.map_as_ref(|inner| inner.id)
    }

    pub fn set_id(&mut self, v: u64) -> PyResult<()> {
        self.inner.map_as_mut(|inner| inner.id = v)
    }

    pub fn get_max_inflight(&self) -> PyResult<usize> {
        self.inner.map_as_ref(|inner| inner.max_inflight)
    }

    pub fn set_max_inflight(&mut self, v: usize) -> PyResult<()> {
        self.inner.map_as_mut(|inner| inner.max_inflight = v)
    }

    pub fn get_max_msg_size(&self) -> PyResult<u64> {
        self.inner.map_as_ref(|inner| inner.max_msg_size)
    }

    pub fn set_max_msg_size(&mut self, v: u64) -> PyResult<()> {
        self.inner.map_as_mut(|inner| inner.max_msg_size = v)
    }

    pub fn get_pending_conf_index(&self) -> PyResult<u64> {
        self.inner.map_as_ref(|inner| inner.pending_conf_index)
    }

    pub fn set_pending_conf_index(&mut self, v: u64) -> PyResult<()> {
        self.inner.map_as_mut(|inner| inner.pending_conf_index = v)
    }

    pub fn get_pending_request_snapshot(&self) -> PyResult<u64> {
        self.inner
            .map_as_ref(|inner| inner.pending_request_snapshot)
    }

    pub fn set_pending_request_snapshot(&mut self, v: u64) -> PyResult<()> {
        self.inner
            .map_as_mut(|inner| inner.pending_request_snapshot = v)
    }

    pub fn get_msgs(&mut self, py: Python) -> PyResult<PyObject> {
        self.inner.map_as_mut(|inner| {
            inner
                .msgs
                .iter_mut()
                .map(|msg| PyMessageRef {
                    inner: RefMutContainer::new_raw(msg),
                })
                .collect::<Vec<_>>()
                .into_py(py)
        })
    }

    pub fn set_msgs(&mut self, msgs: &PyList) -> PyResult<()> {
        let mut msgs = msgs.extract::<Vec<PyMessageMut>>()?;

        self.inner.map_as_mut(|inner| {
            inner.msgs = msgs.iter_mut().map(|msg| msg.into()).collect::<Vec<_>>()
        })
    }

    pub fn take_msgs(&mut self, py: Python) -> PyResult<PyObject> {
        self.inner.map_as_mut(|inner| {
            let msgs = inner.msgs.drain(..).collect::<Vec<_>>();

            msgs.into_iter()
                .map(|msg| PyMessage {
                    inner: RefMutOwner::new(msg),
                })
                .collect::<Vec<_>>()
                .into_py(py)
        })
    }

    pub fn get_raft_log(&mut self) -> PyResult<PyInMemoryRaftLogRef> {
        self.inner.map_as_mut(|inner| PyInMemoryRaftLogRef {
            inner: RefMutContainer::new_raw(&mut inner.raft_log),
        })
    }

    pub fn set_raft_log(&mut self) -> PyResult<()> {
        todo!()
    }

    pub fn get_state(&self) -> PyResult<PyStateRole> {
        self.inner.map_as_ref(|inner| PyStateRole(inner.state))
    }

    pub fn set_state(&mut self, v: &PyStateRole) -> PyResult<()> {
        self.inner.map_as_mut(|inner| inner.state = v.0)
    }

    pub fn get_election_elapsed(&self) -> PyResult<usize> {
        self.inner.map_as_ref(|inner| inner.election_elapsed)
    }

    pub fn set_election_elapsed(&mut self, v: usize) -> PyResult<()> {
        self.inner.map_as_mut(|inner| inner.election_elapsed = v)
    }

    pub fn get_check_quorum(&self) -> PyResult<bool> {
        self.inner.map_as_ref(|inner| inner.check_quorum)
    }

    pub fn set_check_quorum(&mut self, v: bool) -> PyResult<()> {
        self.inner.map_as_mut(|inner| inner.check_quorum = v)
    }

    pub fn get_pre_vote(&mut self) -> PyResult<bool> {
        self.inner.map_as_mut(|inner| inner.pre_vote)
    }

    pub fn store(&mut self) -> PyResult<PyMemStorageRef> {
        self.inner.map_as_mut(|inner| PyMemStorageRef {
            inner: RefMutContainer::new_raw(inner.mut_store()),
        })
    }

    pub fn set_pre_vote(&mut self, v: bool) -> PyResult<()> {
        self.inner.map_as_mut(|inner| inner.pre_vote = v)
    }

    pub fn set_batch_append(&mut self, v: bool) -> PyResult<()> {
        self.inner.map_as_mut(|inner| inner.set_batch_append(v))
    }

    // Below function is exposed here because "ReadOnly" struct is not exposed in raft-rs.
    pub fn get_readonly_read_index_queue(&self, py: Python) -> PyResult<PyObject> {
        self.inner
            .map_as_ref(|inner| PyList::new(py, inner.read_only.read_index_queue.clone()).into())
    }

    // Below function is exposed here because "ReadOnly" struct is not exposed in raft-rs.
    pub fn get_read_only_pending_read_index(&self, _py: Python) -> PyResult<PyObject> {
        todo!()
        // self.inner.map_as_ref(|inner| {
        //     let dict = PyDict::new(py);
        //     let pending_read_index = inner.read_only.pending_read_index.clone();

        //     dict.into_py(py)
        // })
    }

    pub fn set_max_committed_size_per_ready(&mut self, v: u64) -> PyResult<()> {
        self.inner
            .map_as_mut(|inner| inner.set_max_committed_size_per_ready(v))
    }

    pub fn get_read_only_option(&self) -> PyResult<PyReadOnlyOption> {
        self.inner
            .map_as_ref(|inner| PyReadOnlyOption(inner.read_only.option))
    }

    pub fn set_read_only_option(&mut self, option: &PyReadOnlyOption) -> PyResult<()> {
        self.inner
            .map_as_mut(|inner| inner.read_only.option = option.0)
    }

    pub fn campaign(&mut self, campaign_type: &PyString) -> PyResult<()> {
        let campaign_type = campaign_type.to_str()?;
        self.inner.map_as_mut(|inner| match campaign_type {
            "CampaignElection" => inner.campaign(CAMPAIGN_ELECTION),
            "CampaignPreElection" => inner.campaign(CAMPAIGN_PRE_ELECTION),
            "CampaignTransfer" => inner.campaign(CAMPAIGN_TRANSFER),
            // TODO: Improve below error handling.
            _ => panic!("Invalid campaign type"),
        })
    }

    pub fn inflight_buffers_size(&self) -> PyResult<usize> {
        self.inner.map_as_ref(|inner| inner.inflight_buffers_size())
    }

    pub fn maybe_free_inflight_buffers(&mut self) -> PyResult<()> {
        self.inner
            .map_as_mut(|inner| inner.maybe_free_inflight_buffers())
    }

    pub fn adjust_max_inflight_msgs(&mut self, target: u64, cap: usize) -> PyResult<()> {
        self.inner
            .map_as_mut(|inner| inner.adjust_max_inflight_msgs(target, cap))
    }
}
