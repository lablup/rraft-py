use pyo3::{prelude::*, types::PyList};
use utils::{
    errors::{runtime_error, to_pyresult},
    reference::RustRef,
    unsafe_cast::make_mut,
};

use raft::{prelude::Message, storage::MemStorage, Raft};

use crate::{
    eraftpb::{
        conf_change_v2::Py_ConfChangeV2_Mut,
        conf_state::Py_ConfState_Ref,
        entry::Py_Entry_Mut,
        hard_state::Py_HardState_Mut,
        message::{Py_Message_Mut, Py_Message_Owner, Py_Message_Ref},
        snapshot::{Py_Snapshot_Mut, Py_Snapshot_Ref},
    },
    internal::slog::Py_Logger_Mut,
    storage::{
        mem_storage::{Py_MemStorage_Mut, Py_MemStorage_Ref},
        storage::Py_Storage,
    },
};

use super::{
    config::Py_Config_Mut, progress_tracker::Py_ProgressTracker_Ref,
    raft_log::Py_RaftLog__MemStorage_Ref, soft_state::Py_SoftState_Ref, state_role::Py_StateRole,
};

#[pyclass(name = "Raft__MemStorage_Owner")]
pub struct Py_Raft__MemStorage_Owner {
    pub inner: Raft<MemStorage>,
}

#[pyclass(name = "Raft__MemStorage_Ref")]
pub struct Py_Raft__MemStorage_Ref {
    pub inner: RustRef<Raft<MemStorage>>,
}

#[pymethods]
impl Py_Raft__MemStorage_Owner {
    #[new]
    pub fn new(
        cfg: Py_Config_Mut,
        store: Py_MemStorage_Mut,
        logger: Py_Logger_Mut,
    ) -> PyResult<Self> {
        Raft::new(&cfg.into(), store.into(), &logger.into())
            .and_then(|r| Ok(Py_Raft__MemStorage_Owner { inner: r }))
            .map_err(|e| runtime_error(&e.to_string()))
    }

    pub fn make_ref(&mut self) -> Py_Raft__MemStorage_Ref {
        Py_Raft__MemStorage_Ref {
            inner: RustRef::new(&mut self.inner),
        }
    }

    fn __getattr__(this: PyObject, py: Python<'_>, attr: &str) -> PyResult<PyObject> {
        let reference = this.call_method0(py, "make_ref")?;
        reference.getattr(py, attr)
    }
}

#[pymethods]
impl Py_Raft__MemStorage_Ref {
    pub fn __repr__(&mut self) -> PyResult<String> {
        self.inner.map_as_mut(|inner| {
            format!(
                "Raft {{ \
                    msgs: {:?} \
                }}",
                inner.msgs,
            )
        })
    }

    pub fn append_entry(&mut self, ents: &PyList) -> PyResult<bool> {
        let mut entries = ents.extract::<Vec<Py_Entry_Mut>>()?;

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
        let mut entries = ents.extract::<Vec<Py_Entry_Mut>>()?;

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
        let mut entries = ents.extract::<Vec<Py_Entry_Mut>>()?;

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

    pub fn restore(&mut self, snap: Py_Snapshot_Mut) -> PyResult<bool> {
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

    pub fn load_state(&mut self, hs: Py_HardState_Mut) -> PyResult<()> {
        self.inner
            .map_as_mut(|inner| inner.load_state(&mut hs.into()))
    }

    pub fn soft_state(&self) -> PyResult<Py_SoftState_Ref> {
        self.inner.map_as_ref(|inner| Py_SoftState_Ref {
            inner: RustRef::new(unsafe { make_mut(&inner.soft_state()) }),
        })
    }

    pub fn ping(&mut self) -> PyResult<()> {
        self.inner.map_as_mut(|inner| inner.ping())
    }

    pub fn apply_conf_change(&mut self, cc: Py_ConfChangeV2_Mut) -> PyResult<Py_ConfState_Ref> {
        self.inner
            .map_as_mut(|inner| {
                inner
                    .apply_conf_change(&cc.into())
                    .map(|cs| Py_ConfState_Ref {
                        inner: RustRef::new(unsafe { make_mut(&cs) }),
                    })
            })
            .and_then(to_pyresult)
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

    pub fn step(&mut self, msg: Py_Message_Mut) -> PyResult<()> {
        self.inner
            .map_as_mut(|inner| inner.step(msg.into()))
            .and_then(to_pyresult)
    }

    pub fn has_pending_conf(&self) -> PyResult<bool> {
        self.inner.map_as_ref(|inner| inner.has_pending_conf())
    }

    pub fn post_conf_change(&mut self) -> PyResult<Py_ConfState_Ref> {
        self.inner.map_as_mut(|inner| Py_ConfState_Ref {
            inner: RustRef::new(&mut inner.post_conf_change()),
        })
    }

    pub fn in_lease(&self) -> PyResult<bool> {
        self.inner.map_as_ref(|inner| inner.in_lease())
    }

    pub fn handle_heartbeat(&mut self, msg: Py_Message_Mut) -> PyResult<()> {
        self.inner
            .map_as_mut(|inner| inner.handle_heartbeat(msg.into()))
    }

    pub fn handle_append_entries(&mut self, msg: Py_Message_Mut) -> PyResult<()> {
        self.inner
            .map_as_mut(|inner| inner.handle_append_entries(&msg.into()))
    }

    pub fn request_snapshot(&mut self, request_index: u64) -> PyResult<()> {
        self.inner
            .map_as_mut(|inner| inner.request_snapshot(request_index))
            .and_then(to_pyresult)
    }

    pub fn prs(&mut self) -> PyResult<Py_ProgressTracker_Ref> {
        self.inner.map_as_mut(|inner| Py_ProgressTracker_Ref {
            inner: RustRef::new(inner.mut_prs()),
        })
    }

    pub fn reset(&mut self, term: u64) -> PyResult<()> {
        self.inner.map_as_mut(|inner| inner.reset(term))
    }

    pub fn snap(&self) -> PyResult<Option<Py_Snapshot_Ref>> {
        self.inner.map_as_ref(|inner| {
            inner.snap().and_then(|snapshot| {
                Some(Py_Snapshot_Ref {
                    inner: RustRef::new(unsafe { make_mut(snapshot) }),
                })
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

    pub fn get_priority(&self) -> PyResult<u64> {
        self.inner.map_as_ref(|inner| inner.priority)
    }

    pub fn set_priority(&mut self, priority: u64) -> PyResult<()> {
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
                .map(|msg| Py_Message_Ref {
                    inner: RustRef::new(msg),
                })
                .collect::<Vec<_>>()
                .into_py(py)
        })
    }

    pub fn set_msgs(&mut self, msgs: &PyList) -> PyResult<()> {
        let mut msgs = msgs.extract::<Vec<Py_Message_Mut>>()?;

        self.inner.map_as_mut(|inner| {
            inner.msgs = msgs.iter_mut().map(|msg| msg.into()).collect::<Vec<_>>()
        })
    }

    pub fn take_msgs(&mut self, py: Python) -> PyResult<PyObject> {
        self.inner.map_as_mut(|inner| {
            let msgs = inner.msgs.drain(..).collect::<Vec<_>>();

            msgs.into_iter()
                .map(|msg| Py_Message_Owner { inner: msg })
                .collect::<Vec<_>>()
                .into_py(py)
        })
    }

    pub fn get_raft_log(&mut self) -> PyResult<Py_RaftLog__MemStorage_Ref> {
        self.inner.map_as_mut(|inner| Py_RaftLog__MemStorage_Ref {
            inner: RustRef::new(&mut inner.raft_log),
        })
    }

    pub fn set_raft_log(&mut self) -> PyResult<()> {
        todo!()
    }

    pub fn get_state(&self) -> PyResult<Py_StateRole> {
        self.inner.map_as_ref(|inner| Py_StateRole(inner.state))
    }

    pub fn set_state(&mut self, v: &Py_StateRole) -> PyResult<()> {
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

    pub fn store(&mut self) -> PyResult<Py_MemStorage_Ref> {
        self.inner.map_as_mut(|inner| Py_MemStorage_Ref {
            inner: RustRef::new(inner.mut_store()),
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
    pub fn get_read_only_pending_read_index(&self, py: Python) -> PyResult<PyObject> {
        todo!()
        // self.inner.map_as_ref(|inner| {
        //     let dict = PyDict::new(py);
        //     let pending_read_index = inner.read_only.pending_read_index.clone();

        //     dict.into_py(py)
        // })
    }
}

#[pyclass(name = "Raft")]
pub struct Py_Raft__PyStorage_Owner {
    pub inner: Raft<Py_Storage>,
}

#[pymethods]
impl Py_Raft__PyStorage_Owner {}

#[pyclass(name = "Raft_Ref")]
pub struct Py_Raft__PyStorage_Ref {
    pub inner: RustRef<Raft<Py_Storage>>,
}

#[pymethods]
impl Py_Raft__PyStorage_Ref {}
