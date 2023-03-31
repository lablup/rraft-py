use pyo3::prelude::*;

use raft::prelude::{ConfChange, ConfChangeV2};
use raft::storage::MemStorage;
use raft::Ready;

use raft::raw_node::RawNode;
use utils::errors::to_pyresult;
use utils::unsafe_cast::make_mut;

use super::raft::Py_Raft__MemStorage_Ref;
use bindings::config::Py_Config_Mut;
use bindings::light_ready::Py_LightReady_Owner;
use bindings::ready::{Py_Ready_Owner, Py_Ready_Ref};
use prost_bindings::conf_change::Py_ConfChange_Mut;
use prost_bindings::conf_change_v2::Py_ConfChangeV2_Mut;
use prost_bindings::conf_state::Py_ConfState_Owner;
use prost_bindings::message::Py_Message_Mut;
use prost_bindings::snapshot::Py_Snapshot_Ref;
use external::slog::Py_Logger_Mut;

use bindings::snapshot_status::Py_SnapshotStatus;
// use bindings::status::Py_Status__MemStorage_Owner;
use utils::reference::RustRef;

#[pyclass(name = "RawNode__MemStorage_Owner")]
pub struct Py_RawNode__MemStorage_Owner {
    pub inner: RawNode<MemStorage>,
}

#[pyclass(name = "RawNode__MemStorage_Ref")]
pub struct Py_RawNode__MemStorage_Ref {
    pub inner: RustRef<RawNode<MemStorage>>,
}

#[pymethods]
impl Py_RawNode__MemStorage_Owner {
    // #[new]
    // pub fn new(cfg: Py_Config_Mut, storage: Py_MemStorage_Mut, logger: Py_Logger_Mut) -> Self {
    //     Py_RawNode__MemStorage_Owner {
    //         inner: RawNode::new(&cfg.into(), storage.into(), &logger.into()).unwrap(),
    //     }
    // }

    pub fn make_ref(&mut self) -> Py_RawNode__MemStorage_Ref {
        Py_RawNode__MemStorage_Ref {
            inner: RustRef::new(&mut self.inner),
        }
    }

    fn __getattr__(this: PyObject, py: Python<'_>, attr: &str) -> PyResult<PyObject> {
        let reference = this.call_method0(py, "make_ref")?;
        reference.getattr(py, attr)
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
        self.inner.map_as_ref(|inner| {
            inner.snap().map(|snap| Py_Snapshot_Ref {
                inner: RustRef::new(unsafe { make_mut(snap) }),
            })
        })
    }

    // pub fn status(&self) -> Py_Status__MemStorage_Owner {
    //     todo!()
    // }

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

    pub fn propose(&mut self, context: &PyAny, data: &PyAny) -> PyResult<()> {
        let context = context.extract::<Vec<u8>>()?;
        let data = data.extract::<Vec<u8>>()?;

        self.inner
            .map_as_mut(|inner| inner.propose(context, data))
            .and_then(to_pyresult)
    }

    pub fn propose_conf_change(&mut self, context: &PyAny, cc: Py_ConfChange_Mut) -> PyResult<()> {
        let context = context.extract::<Vec<u8>>()?;
        let cc: ConfChange = cc.into();

        self.inner
            .map_as_mut(|inner| inner.propose_conf_change(context, cc))
            .and_then(to_pyresult)
    }

    pub fn propose_conf_change_v2(
        &mut self,
        context: &PyAny,
        cc: Py_ConfChangeV2_Mut,
    ) -> PyResult<()> {
        let context = context.extract::<Vec<u8>>()?;
        let cc: ConfChangeV2 = cc.into();

        self.inner
            .map_as_mut(|inner| inner.propose_conf_change(context, cc))
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
        self.inner
            .map_as_mut(|inner| {
                let cc: ConfChange = cc.into();

                inner
                    .apply_conf_change(&cc)
                    .map(|cs| Py_ConfState_Owner { inner: cs })
            })
            .and_then(to_pyresult)
    }

    pub fn apply_conf_change_v2(
        &mut self,
        cc: Py_ConfChangeV2_Mut,
    ) -> PyResult<Py_ConfState_Owner> {
        self.inner
            .map_as_mut(|inner| {
                let cc: ConfChangeV2 = cc.into();

                inner
                    .apply_conf_change(&cc)
                    .map(|cs| Py_ConfState_Owner { inner: cs })
            })
            .and_then(to_pyresult)
    }

    pub fn on_persist_ready(&mut self, number: u64) -> PyResult<()> {
        self.inner
            .map_as_mut(|inner| inner.on_persist_ready(number))
    }

    pub fn read_index(&mut self, rctx: &PyAny) -> PyResult<()> {
        let rctx = rctx.extract()?;
        self.inner.map_as_mut(|inner| inner.read_index(rctx))
    }

    pub fn get_raft(&mut self) -> PyResult<Py_Raft__MemStorage_Ref> {
        self.inner.map_as_mut(|inner| Py_Raft__MemStorage_Ref {
            inner: RustRef::new(&mut inner.raft),
        })
    }

    // pub fn store(&mut self) -> PyResult<Py_MemStorage_Ref> {
    //     self.inner.map_as_mut(|inner| Py_MemStorage_Ref {
    //         inner: RustRef::new(inner.mut_store()),
    //     })
    // }
}
