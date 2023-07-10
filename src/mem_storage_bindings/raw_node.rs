use crate::bindings::get_entries_context::PyGetEntriesContextRef;
use pyo3::{intern, prelude::*};

use raft::prelude::{ConfChange, ConfChangeV2};
use raft::storage::MemStorage;
use raft::GetEntriesContext;

use crate::utils::reference::{RefMutContainer, RefMutOwner};
use crate::utils::unsafe_cast::make_mut;
use raft::raw_node::RawNode;

use super::raft::PyInMemoryRaftRef;
use crate::bindings::config::PyConfigMut;
use crate::bindings::light_ready::PyLightReady;
use crate::bindings::ready::{PyReady, PyReadyRef};
use crate::external_bindings::slog::PyLoggerMut;
use crate::raftpb_bindings::conf_change::PyConfChangeMut;
use crate::raftpb_bindings::conf_change_v2::PyConfChangeV2Mut;
use crate::raftpb_bindings::conf_state::PyConfState;
use crate::raftpb_bindings::message::PyMessageMut;
use crate::raftpb_bindings::snapshot::PySnapshotRef;

use super::mem_storage::{PyMemStorageMut, PyMemStorageRef};
use crate::bindings::snapshot_status::PySnapshotStatus;
use crate::utils::errors::PyRaftError;

#[pyclass(name = "InMemoryRawNode")]
pub struct PyInMemoryRawNode {
    pub inner: RefMutOwner<RawNode<MemStorage>>,
}

#[pyclass(name = "InMemoryRawNodeRef")]
pub struct PyInMemoryRawNodeRef {
    pub inner: RefMutContainer<RawNode<MemStorage>>,
}

#[pymethods]
impl PyInMemoryRawNode {
    #[new]
    pub fn new(cfg: PyConfigMut, storage: PyMemStorageMut, logger: PyLoggerMut) -> PyResult<Self> {
        Ok(PyInMemoryRawNode {
            inner: RefMutOwner::new(
                RawNode::new(&cfg.into(), storage.into(), &logger.into()).map_err(PyRaftError)?,
            ),
        })
    }

    pub fn make_ref(&mut self) -> PyInMemoryRawNodeRef {
        PyInMemoryRawNodeRef {
            inner: RefMutContainer::new(&mut self.inner),
        }
    }

    fn __getattr__(this: PyObject, py: Python, attr: &str) -> PyResult<PyObject> {
        let reference = this.call_method0(py, intern!(py, "make_ref"))?;
        reference.getattr(py, attr)
    }
}

#[pymethods]
impl PyInMemoryRawNodeRef {
    pub fn advance_apply(&mut self) -> PyResult<()> {
        self.inner.map_as_mut(|inner| inner.advance_apply())
    }

    pub fn advance_apply_to(&mut self, applied: u64) -> PyResult<()> {
        self.inner
            .map_as_mut(|inner| inner.advance_apply_to(applied))
    }

    pub fn advance(&mut self, rd: &mut PyReadyRef) -> PyResult<PyLightReady> {
        let rd = rd.inner.map_as_mut(|rd| std::mem::take(rd))?;

        self.inner.map_as_mut(|inner| PyLightReady {
            inner: RefMutOwner::new(inner.advance(rd)),
        })
    }

    pub fn advance_append(&mut self, rd: &mut PyReadyRef) -> PyResult<PyLightReady> {
        let rd = rd.inner.map_as_mut(|rd| std::mem::take(rd))?;

        self.inner.map_as_mut(|inner| PyLightReady {
            inner: RefMutOwner::new(inner.advance_append(rd)),
        })
    }

    pub fn advance_append_async(&mut self, rd: &mut PyReadyRef) -> PyResult<()> {
        let rd = rd.inner.map_as_mut(|rd| std::mem::take(rd))?;

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

    pub fn set_priority(&mut self, priority: i64) -> PyResult<()> {
        self.inner.map_as_mut(|inner| inner.set_priority(priority))
    }

    pub fn report_snapshot(&mut self, id: u64, status: &PySnapshotStatus) -> PyResult<()> {
        self.inner
            .map_as_mut(|inner| inner.report_snapshot(id, status.0))
    }

    pub fn report_unreachable(&mut self, id: u64) -> PyResult<()> {
        self.inner.map_as_mut(|inner| inner.report_unreachable(id))
    }

    pub fn request_snapshot(&mut self) -> PyResult<()> {
        self.inner
            .map_as_mut(|inner| inner.request_snapshot().map_err(|e| PyRaftError(e).into()))?
    }

    pub fn transfer_leader(&mut self, transferee: u64) -> PyResult<()> {
        self.inner
            .map_as_mut(|inner| inner.transfer_leader(transferee))
    }

    pub fn snap(&self) -> PyResult<Option<PySnapshotRef>> {
        self.inner.map_as_ref(|inner| {
            inner.snap().map(|snap| PySnapshotRef {
                inner: RefMutContainer::new_raw(unsafe { make_mut(snap) }),
            })
        })
    }

    // pub fn status(&self) -> PyStatus_MemStorage {
    //     todo!()
    // }

    pub fn step(&mut self, msg: PyMessageMut) -> PyResult<()> {
        self.inner
            .map_as_mut(|inner| inner.step(msg.into()).map_err(|e| PyRaftError(e).into()))?
    }

    pub fn skip_bcast_commit(&mut self, skip: bool) -> PyResult<()> {
        self.inner.map_as_mut(|inner| inner.skip_bcast_commit(skip))
    }

    pub fn campaign(&mut self) -> PyResult<()> {
        self.inner
            .map_as_mut(|inner| inner.campaign().map_err(|e| PyRaftError(e).into()))?
    }

    pub fn propose(&mut self, context: &PyAny, data: &PyAny) -> PyResult<()> {
        let context = context.extract::<Vec<u8>>()?;
        let data = data.extract::<Vec<u8>>()?;

        self.inner.map_as_mut(|inner| {
            inner
                .propose(context, data)
                .map_err(|e| PyRaftError(e).into())
        })?
    }

    pub fn propose_conf_change(&mut self, context: &PyAny, cc: PyConfChangeMut) -> PyResult<()> {
        let context = context.extract::<Vec<u8>>()?;
        let cc: ConfChange = cc.into();

        self.inner.map_as_mut(|inner| {
            inner
                .propose_conf_change(context, cc)
                .map_err(|e| PyRaftError(e).into())
        })?
    }

    pub fn propose_conf_change_v2(
        &mut self,
        context: &PyAny,
        cc: PyConfChangeV2Mut,
    ) -> PyResult<()> {
        let context = context.extract::<Vec<u8>>()?;
        let cc: ConfChangeV2 = cc.into();

        self.inner.map_as_mut(|inner| {
            inner
                .propose_conf_change(context, cc)
                .map_err(|e| PyRaftError(e).into())
        })?
    }

    pub fn ping(&mut self) -> PyResult<()> {
        self.inner.map_as_mut(|inner| inner.ping())
    }

    pub fn ready(&mut self) -> PyResult<PyReady> {
        self.inner.map_as_mut(|inner| PyReady {
            inner: RefMutOwner::new(inner.ready()),
        })
    }

    pub fn apply_conf_change(&mut self, cc: PyConfChangeMut) -> PyResult<PyConfState> {
        self.inner.map_as_mut(|inner| {
            let cc: ConfChange = cc.into();

            inner
                .apply_conf_change(&cc)
                .map(|cs| PyConfState {
                    inner: RefMutOwner::new(cs),
                })
                .map_err(|e| PyRaftError(e).into())
        })?
    }

    pub fn apply_conf_change_v2(&mut self, cc: PyConfChangeV2Mut) -> PyResult<PyConfState> {
        let cc: ConfChangeV2 = cc.into();

        self.inner.map_as_mut(|inner| {
            inner
                .apply_conf_change(&cc)
                .map(|cs| PyConfState {
                    inner: RefMutOwner::new(cs),
                })
                .map_err(|e| PyRaftError(e).into())
        })?
    }

    pub fn on_persist_ready(&mut self, number: u64) -> PyResult<()> {
        self.inner
            .map_as_mut(|inner| inner.on_persist_ready(number))
    }

    pub fn read_index(&mut self, rctx: &PyAny) -> PyResult<()> {
        let rctx = rctx.extract()?;
        self.inner.map_as_mut(|inner| inner.read_index(rctx))
    }

    pub fn get_raft(&mut self) -> PyResult<PyInMemoryRaftRef> {
        self.inner.map_as_mut(|inner| PyInMemoryRaftRef {
            inner: RefMutContainer::new_raw(&mut inner.raft),
        })
    }

    pub fn store(&mut self) -> PyResult<PyMemStorageRef> {
        self.inner.map_as_mut(|inner| PyMemStorageRef {
            inner: RefMutContainer::new_raw(inner.mut_store()),
        })
    }

    pub fn on_entries_fetched(&mut self, context: &mut PyGetEntriesContextRef) -> PyResult<()> {
        let context = context.inner.map_as_mut(|context| unsafe {
            std::ptr::replace(context, GetEntriesContext::empty(false))
        })?;

        self.inner
            .map_as_mut(|inner| inner.on_entries_fetched(context))
    }
}
