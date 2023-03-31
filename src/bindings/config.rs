use pyo3::prelude::*;

use raft::Config;
use utils::errors::to_pyresult;

use utils::reference::RustRef;

use super::readonly_option::Py_ReadOnlyOption;

#[derive(Clone)]
#[pyclass(name = "Config_Owner")]
pub struct Py_Config_Owner {
    pub inner: Config,
}

#[derive(Clone)]
#[pyclass(name = "Config_Ref")]
pub struct Py_Config_Ref {
    pub inner: RustRef<Config>,
}

#[derive(FromPyObject)]
pub enum Py_Config_Mut<'p> {
    Owned(PyRefMut<'p, Py_Config_Owner>),
    RefMut(Py_Config_Ref),
}

impl From<Py_Config_Mut<'_>> for Config {
    fn from(val: Py_Config_Mut<'_>) -> Self {
        match val {
            Py_Config_Mut::Owned(x) => x.inner.clone(),
            Py_Config_Mut::RefMut(mut x) => x.inner.map_as_mut(|x| x.clone()).unwrap(),
        }
    }
}

impl From<&mut Py_Config_Mut<'_>> for Config {
    fn from(val: &mut Py_Config_Mut<'_>) -> Self {
        match val {
            Py_Config_Mut::Owned(x) => x.inner.clone(),
            Py_Config_Mut::RefMut(x) => x.inner.map_as_mut(|x| x.clone()).unwrap(),
        }
    }
}

fn format_config<T: Into<Config>>(cfg: T) -> String {
    let cfg: Config = cfg.into();

    format!(
        "Config {{ \
            id: {:?}, \
            election_tick: {:?}, \
            heartbeat_tick: {:?}, \
            applied: {:?}, \
            max_size_per_msg: {:?}, \
            max_inflight_msgs: {:?}, \
            check_quorum: {:?}, \
            pre_vote: {:?}, \
            min_election_tick: {:?}, \
            max_election_tick: {:?}, \
            read_only_option: {:?}, \
            skip_bcast_commit: {:?}, \
            batch_append: {:?}, \
            priority: {:?}, \
            max_uncommitted_size: {:?}, \
            max_committed_size_per_ready: {:?} \
        }}",
        cfg.id,
        cfg.election_tick,
        cfg.heartbeat_tick,
        cfg.applied,
        cfg.max_size_per_msg,
        cfg.max_inflight_msgs,
        cfg.check_quorum,
        cfg.pre_vote,
        cfg.min_election_tick,
        cfg.max_election_tick,
        cfg.read_only_option,
        cfg.skip_bcast_commit,
        cfg.batch_append,
        cfg.priority,
        cfg.max_uncommitted_size,
        cfg.max_committed_size_per_ready,
    )
}

#[pymethods]
impl Py_Config_Owner {
    #![allow(clippy::too_many_arguments)]
    #[new]
    pub fn new(
        id: Option<u64>,
        election_tick: Option<usize>,
        heartbeat_tick: Option<usize>,
        applied: Option<u64>,
        max_size_per_msg: Option<u64>,
        max_inflight_msgs: Option<usize>,
        check_quorum: Option<bool>,
        pre_vote: Option<bool>,
        min_election_tick: Option<usize>,
        max_election_tick: Option<usize>,
        read_only_option: Option<&Py_ReadOnlyOption>,
        skip_bcast_commit: Option<bool>,
        batch_append: Option<bool>,
        priority: Option<u64>,
        max_uncommitted_size: Option<u64>,
        max_committed_size_per_ready: Option<u64>,
    ) -> Self {
        let mut config = Config::default();

        config.applied = applied.unwrap_or(config.applied);
        config.batch_append = batch_append.unwrap_or(config.batch_append);
        config.check_quorum = check_quorum.unwrap_or(config.check_quorum);
        config.election_tick = election_tick.unwrap_or(config.election_tick);
        config.heartbeat_tick = heartbeat_tick.unwrap_or(config.heartbeat_tick);
        config.id = id.unwrap_or(config.id);
        config.max_committed_size_per_ready =
            max_committed_size_per_ready.unwrap_or(config.max_committed_size_per_ready);
        config.max_inflight_msgs = max_inflight_msgs.unwrap_or(config.max_inflight_msgs);
        config.max_size_per_msg = max_size_per_msg.unwrap_or(config.max_size_per_msg);
        config.max_uncommitted_size = max_uncommitted_size.unwrap_or(config.max_uncommitted_size);
        config.min_election_tick = min_election_tick.unwrap_or(config.min_election_tick);
        config.max_election_tick = max_election_tick.unwrap_or(config.max_election_tick);
        config.pre_vote = pre_vote.unwrap_or(config.pre_vote);
        config.priority = priority.unwrap_or(config.priority);
        config.skip_bcast_commit = skip_bcast_commit.unwrap_or(config.skip_bcast_commit);

        config.read_only_option = read_only_option.map_or(config.read_only_option, |opt| opt.0);

        Py_Config_Owner { inner: config }
    }

    #[staticmethod]
    pub fn default() -> Py_Config_Owner {
        Py_Config_Owner {
            inner: Config::default(),
        }
    }

    pub fn make_ref(&mut self) -> Py_Config_Ref {
        Py_Config_Ref {
            inner: RustRef::new(&mut self.inner),
        }
    }

    pub fn __repr__(&self) -> String {
        format_config(self.inner.clone())
    }

    fn __getattr__(this: PyObject, py: Python<'_>, attr: &str) -> PyResult<PyObject> {
        let reference = this.call_method0(py, "make_ref")?;
        reference.getattr(py, attr)
    }
}

#[pymethods]
impl Py_Config_Ref {
    pub fn __repr__(&self) -> PyResult<String> {
        self.inner.map_as_ref(|inner| format_config(inner.clone()))
    }

    pub fn clone(&self) -> PyResult<Py_Config_Owner> {
        Ok(Py_Config_Owner {
            inner: self.inner.map_as_ref(|inner| inner.clone())?,
        })
    }

    pub fn min_election_tick(&self) -> PyResult<usize> {
        self.inner.map_as_ref(|inner| inner.min_election_tick())
    }

    pub fn set_min_election_tick(&mut self, v: usize) -> PyResult<()> {
        self.inner.map_as_mut(|inner| inner.min_election_tick = v)
    }

    pub fn max_election_tick(&self) -> PyResult<usize> {
        self.inner.map_as_ref(|inner| inner.max_election_tick())
    }

    pub fn set_max_election_tick(&mut self, v: usize) -> PyResult<()> {
        self.inner.map_as_mut(|inner| inner.max_election_tick = v)
    }

    pub fn validate(&self) -> PyResult<()> {
        self.inner
            .map_as_ref(|inner| inner.validate())
            .and_then(to_pyresult)
    }

    pub fn get_read_only_option(&self) -> PyResult<Py_ReadOnlyOption> {
        self.inner
            .map_as_ref(|inner| Py_ReadOnlyOption(inner.read_only_option))
    }

    pub fn set_read_only_option(&mut self, read_only_option: &Py_ReadOnlyOption) -> PyResult<()> {
        self.inner.map_as_mut(|inner| {
            inner.read_only_option = read_only_option.0;
        })
    }

    pub fn get_id(&self) -> PyResult<u64> {
        self.inner.map_as_ref(|inner| inner.id)
    }

    pub fn set_id(&mut self, id: u64) -> PyResult<()> {
        self.inner.map_as_mut(|inner| inner.id = id)
    }

    pub fn get_election_tick(&self) -> PyResult<usize> {
        self.inner.map_as_ref(|inner| inner.election_tick)
    }

    pub fn set_election_tick(&mut self, election_tick: usize) -> PyResult<()> {
        self.inner
            .map_as_mut(|inner| inner.election_tick = election_tick)
    }

    pub fn get_heartbeat_tick(&self) -> PyResult<usize> {
        self.inner.map_as_ref(|inner| inner.heartbeat_tick)
    }

    pub fn set_heartbeat_tick(&mut self, heartbeat_tick: usize) -> PyResult<()> {
        self.inner
            .map_as_mut(|inner| inner.heartbeat_tick = heartbeat_tick)
    }

    pub fn get_max_size_per_msg(&self) -> PyResult<u64> {
        self.inner.map_as_ref(|inner| inner.max_size_per_msg)
    }

    pub fn set_max_size_per_msg(&mut self, max_size_per_msg: u64) -> PyResult<()> {
        self.inner
            .map_as_mut(|inner| inner.max_size_per_msg = max_size_per_msg)
    }

    pub fn get_max_inflight_msgs(&self) -> PyResult<usize> {
        self.inner.map_as_ref(|inner| inner.max_inflight_msgs)
    }

    pub fn set_max_inflight_msgs(&mut self, max_inflight_msgs: usize) -> PyResult<()> {
        self.inner
            .map_as_mut(|inner| inner.max_inflight_msgs = max_inflight_msgs)
    }

    pub fn get_applied(&self) -> PyResult<u64> {
        self.inner.map_as_ref(|inner| inner.applied)
    }

    pub fn set_applied(&mut self, applied: u64) -> PyResult<()> {
        self.inner.map_as_mut(|inner| inner.applied = applied)
    }

    pub fn get_check_quorum(&self) -> PyResult<bool> {
        self.inner.map_as_ref(|inner| inner.check_quorum)
    }

    pub fn set_check_quorum(&mut self, check_quorum: bool) -> PyResult<()> {
        self.inner
            .map_as_mut(|inner| inner.check_quorum = check_quorum)
    }

    pub fn get_pre_vote(&self) -> PyResult<bool> {
        self.inner.map_as_ref(|inner| inner.pre_vote)
    }

    pub fn set_pre_vote(&mut self, pre_vote: bool) -> PyResult<()> {
        self.inner.map_as_mut(|inner| inner.pre_vote = pre_vote)
    }

    pub fn get_batch_append(&self) -> PyResult<bool> {
        self.inner.map_as_ref(|inner| inner.batch_append)
    }

    pub fn set_batch_append(&mut self, batch_append: bool) -> PyResult<()> {
        self.inner
            .map_as_mut(|inner| inner.batch_append = batch_append)
    }

    pub fn get_skip_bcast_commit(&self) -> PyResult<bool> {
        self.inner.map_as_ref(|inner| inner.skip_bcast_commit)
    }

    pub fn set_skip_bcast_commit(&mut self, v: bool) -> PyResult<()> {
        self.inner.map_as_mut(|inner| inner.skip_bcast_commit = v)
    }

    pub fn get_priority(&self) -> PyResult<u64> {
        self.inner.map_as_ref(|inner| inner.priority)
    }

    pub fn set_priority(&mut self, priority: u64) -> PyResult<()> {
        self.inner.map_as_mut(|inner| inner.priority = priority)
    }

    pub fn get_max_uncommitted_size(&self) -> PyResult<u64> {
        self.inner.map_as_ref(|inner| inner.max_uncommitted_size)
    }

    pub fn set_max_uncommitted_size(&mut self, max_uncommitted_size: u64) -> PyResult<()> {
        self.inner
            .map_as_mut(|inner| inner.max_uncommitted_size = max_uncommitted_size)
    }
}