use pyo3::exceptions::PyRuntimeError;
use pyo3::prelude::*;
use pyo3::types::PyList;

use raft::prelude::{ConfChange, ConfChangeV2};
use raft::storage::MemStorage;
use raft::Ready;

use raft::raw_node::RawNode;
use utils::errors::to_pyresult;
use utils::uncloneable_reference::{UncloneableRustRef, UncloneableRustRef_Default_Implementation};
use utils::unsafe_cast::make_mut;

use super::light_ready::Py_LightReady_Owner;
use super::ready::{Py_Ready_Owner, Py_Ready_Ref};
use crate::eraftpb::conf_change::Py_ConfChange_Mut;
use crate::eraftpb::conf_change_v2::Py_ConfChangeV2_Mut;
use crate::eraftpb::conf_state::Py_ConfState_Owner;
use crate::eraftpb::message::Py_Message_Mut;
use crate::eraftpb::snapshot::Py_Snapshot_Ref;
use crate::internal::slog::Py_Logger_Mut;
use crate::prelude::config::Py_Config_Mut;
use crate::prelude::raft::Py_Raft__MemStorage_Ref;
use crate::prelude::raft_log::Py_RaftLog__MemStorage_Ref;
use crate::prelude::snapshot_status::Py_SnapshotStatus;
use crate::prelude::status::Py_Status__MemStorage_Owner;
use crate::storage::mem_storage::{Py_MemStorage_Mut, Py_MemStorage_Ref};
use crate::storage::storage::Py_Storage;
use utils::reference::{RustRef, RustRef_Default_Implementation};

#[pyclass(name = "RawNode__MemStorage_Owner")]
pub struct Py_RawNode__MemStorage_Owner {
    pub inner: RawNode<MemStorage>,
}

#[pyclass(name = "RawNode__MemStorage_Ref")]
pub struct Py_RawNode__MemStorage_Ref {
    pub inner: UncloneableRustRef<RawNode<MemStorage>>,
}

#[pymethods]
impl Py_RawNode__MemStorage_Owner {
    #[new]
    pub fn new(cfg: Py_Config_Mut, storage: Py_MemStorage_Mut, logger: Py_Logger_Mut) -> Self {
        Py_RawNode__MemStorage_Owner {
            inner: RawNode::new(&cfg.into(), storage.into(), &logger.into()).unwrap(),
        }
    }

    pub fn make_ref(&mut self) -> Py_RawNode__MemStorage_Ref {
        Py_RawNode__MemStorage_Ref {
            inner: UncloneableRustRef::new(&mut self.inner),
        }
    }
}

#[pymethods]
impl Py_RawNode__MemStorage_Ref {
    pub fn advance_apply(&mut self) -> PyResult<()> {
        self.inner.map_as_mut(|inner| inner.advance_apply())
    }

    pub fn advance_apply_to(&mut self, applied: u64) -> PyResult<()> {
        self.inner
            .map_as_mut(|inner| inner.advance_apply_to(applied))
    }

    /// WARNING: This function replace rd with default Ready.
    pub fn advance(&mut self, rd: &mut Py_Ready_Ref) -> PyResult<Py_LightReady_Owner> {
        let rd = rd
            .inner
            .map_as_mut(|rd| unsafe { std::ptr::replace(rd, Ready::default()) })?;

        self.inner.map_as_mut(|inner| Py_LightReady_Owner {
            inner: inner.advance(rd),
        })
    }

    /// WARNING: This function replace rd with default Ready.
    pub fn advance_append(&mut self, rd: &mut Py_Ready_Ref) -> PyResult<Py_LightReady_Owner> {
        let rd = rd
            .inner
            .map_as_mut(|rd| unsafe { std::ptr::replace(rd, Ready::default()) })?;

        self.inner.map_as_mut(|inner| Py_LightReady_Owner {
            inner: inner.advance_append(rd),
        })
    }

    /// WARNING: This function replace rd with default Ready.
    pub fn advance_append_async(&mut self, rd: &mut Py_Ready_Ref) -> PyResult<()> {
        let rd = rd
            .inner
            .map_as_mut(|rd| unsafe { std::ptr::replace(rd, Ready::default()) })?;

        self.inner
            .map_as_mut(|inner| inner.advance_append_async(rd))
    }

    pub fn has_ready(&self) -> PyResult<bool> {
        self.inner.map_as_ref(|inner| inner.has_ready())
    }

    pub fn tick(&mut self) -> PyResult<bool> {
        self.inner.map_as_mut(|inner| inner.tick())
    }

    pub fn set_batch_append(&mut self, batch_append: bool) -> PyResult<()> {
        self.inner
            .map_as_mut(|inner| inner.set_batch_append(batch_append))
    }

    pub fn set_priority(&mut self, priority: u64) -> PyResult<()> {
        self.inner.map_as_mut(|inner| inner.set_priority(priority))
    }

    pub fn report_snapshot(&mut self, id: u64, status: &Py_SnapshotStatus) -> PyResult<()> {
        self.inner
            .map_as_mut(|inner| inner.report_snapshot(id, status.0))
    }

    pub fn report_unreachable(&mut self, id: u64) -> PyResult<()> {
        self.inner.map_as_mut(|inner| inner.report_unreachable(id))
    }

    pub fn request_snapshot(&mut self, request_index: u64) -> PyResult<()> {
        self.inner
            .map_as_mut(|inner| inner.request_snapshot(request_index))
            .and_then(to_pyresult)
    }

    pub fn transfer_leader(&mut self, transferee: u64) -> PyResult<()> {
        self.inner
            .map_as_mut(|inner| inner.transfer_leader(transferee))
    }

    pub fn snap(&self) -> PyResult<Option<Py_Snapshot_Ref>> {
        self.inner.map_as_ref(|inner| match inner.snap() {
            Some(snap) => Some(Py_Snapshot_Ref {
                inner: RustRef::new(unsafe { make_mut(snap) }),
            }),
            None => None,
        })
    }

    pub fn status(&self) -> Py_Status__MemStorage_Owner {
        todo!()
    }

    pub fn step(&mut self, msg: Py_Message_Mut) -> PyResult<()> {
        self.inner
            .map_as_mut(|inner| inner.step(msg.into()))
            .and_then(to_pyresult)
    }

    pub fn skip_bcast_commit(&mut self, skip: bool) -> PyResult<()> {
        self.inner.map_as_mut(|inner| inner.skip_bcast_commit(skip))
    }

    pub fn campaign(&mut self) -> PyResult<()> {
        self.inner
            .map_as_mut(|inner| inner.campaign())
            .and_then(to_pyresult)
    }

    pub fn propose(&mut self, context: &PyList, data: &PyList) -> PyResult<()> {
        self.inner
            .map_as_mut(|inner| {
                let context = context.extract::<Vec<u8>>().unwrap();
                let data = data.extract::<Vec<u8>>().unwrap();

                inner.propose(context, data)
            })
            .and_then(to_pyresult)
    }

    pub fn propose_conf_change(&mut self, context: &PyList, cc: Py_ConfChange_Mut) -> PyResult<()> {
        self.inner
            .map_as_mut(|inner| {
                let context = context.extract::<Vec<u8>>().unwrap();
                let cc: ConfChange = cc.into();

                inner.propose_conf_change(context, cc)
            })
            .and_then(to_pyresult)
    }

    pub fn propose_conf_change_v2(
        &mut self,
        context: &PyList,
        cc: Py_ConfChangeV2_Mut,
    ) -> PyResult<()> {
        self.inner
            .map_as_mut(|inner| {
                let context = context.extract::<Vec<u8>>().unwrap();
                let cc: ConfChangeV2 = cc.into();

                inner.propose_conf_change(context, cc)
            })
            .and_then(to_pyresult)
    }

    pub fn ping(&mut self) -> PyResult<()> {
        self.inner.map_as_mut(|inner| inner.ping())
    }

    pub fn ready(&mut self) -> PyResult<Py_Ready_Owner> {
        self.inner.map_as_mut(|inner| Py_Ready_Owner {
            inner: inner.ready(),
        })
    }

    pub fn apply_conf_change(&mut self, cc: Py_ConfChange_Mut) -> PyResult<Py_ConfState_Owner> {
        let result = self
            .inner
            .map_as_mut(|inner| {
                let cc: ConfChange = cc.into();
                let cs = inner.apply_conf_change(&cc);
                match cs {
                    Ok(cs) => Ok(Py_ConfState_Owner { inner: cs }),
                    Err(e) => Err(e),
                }
            })
            .unwrap();

        match result {
            Ok(result) => Ok(result),
            Err(_e) => Err(PyRuntimeError::new_err("unexpected error")),
        }
    }

    pub fn apply_conf_change_v2(
        &mut self,
        cc: Py_ConfChangeV2_Mut,
    ) -> PyResult<Py_ConfState_Owner> {
        let result = self
            .inner
            .map_as_mut(|inner| {
                let cc: ConfChangeV2 = cc.into();
                let cs = inner.apply_conf_change(&cc);
                match cs {
                    Ok(cs) => Ok(Py_ConfState_Owner { inner: cs }),
                    Err(e) => Err(e),
                }
            })
            .unwrap();

        match result {
            Ok(result) => Ok(result),
            Err(_e) => Err(PyRuntimeError::new_err("unexpected error")),
        }
    }

    pub fn on_persist_ready(&mut self, number: u64) -> PyResult<()> {
        self.inner
            .map_as_mut(|inner| inner.on_persist_ready(number))
    }

    pub fn read_index(&mut self, rctx: &PyList) -> PyResult<()> {
        self.inner.map_as_mut(|inner| {
            let rctx = rctx.extract().unwrap();
            inner.read_index(rctx)
        })
    }

    pub fn get_raft(&mut self) -> PyResult<Py_Raft__MemStorage_Ref> {
        self.inner.map_as_mut(|inner| Py_Raft__MemStorage_Ref {
            inner: UncloneableRustRef::new(&mut inner.raft),
        })
    }
}

#[pyclass(name = "RawNode")]
pub struct Py_RawNode__PyStorage_Owner {
    pub inner: RawNode<Py_Storage>,
}

#[pymethods]
impl Py_RawNode__PyStorage_Owner {}

#[pyclass(name = "RawNode_Ref")]
pub struct Py_RawNode__PyStorage_Ref {
    pub inner: UncloneableRustRef<RawNode<Py_Storage>>,
}

#[pymethods]
impl Py_RawNode__PyStorage_Ref {}
