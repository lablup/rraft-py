use pyo3::{prelude::*, pyclass::CompareOp};

use raft::Progress;

use utils::{errors::to_pyresult, reference::RustRef};

use super::{
    inflights::{Py_Inflights_Mut, Py_Inflights_Ref},
    progress_state::Py_ProgressState,
};

#[derive(Clone)]
#[pyclass(name = "Progress_Owner")]
pub struct Py_Progress_Owner {
    pub inner: Progress,
}

#[derive(Clone)]
#[pyclass(name = "Progress_Ref")]
pub struct Py_Progress_Ref {
    pub inner: RustRef<Progress>,
}

#[derive(FromPyObject)]
pub enum Py_Progress_Mut<'p> {
    Owned(PyRefMut<'p, Py_Progress_Owner>),
    RefMut(Py_Progress_Ref),
}

impl Into<Progress> for Py_Progress_Mut<'_> {
    fn into(self) -> Progress {
        match self {
            Py_Progress_Mut::Owned(x) => x.inner.clone(),
            Py_Progress_Mut::RefMut(mut x) => x.inner.map_as_mut(|x| x.clone()).unwrap(),
        }
    }
}

impl Into<Progress> for &mut Py_Progress_Mut<'_> {
    fn into(self) -> Progress {
        match self {
            Py_Progress_Mut::Owned(x) => x.inner.clone(),
            Py_Progress_Mut::RefMut(x) => x.inner.map_as_mut(|x| x.clone()).unwrap(),
        }
    }
}

#[pymethods]
impl Py_Progress_Owner {
    #[new]
    pub fn new(next_idx: u64, ins_size: usize) -> Self {
        Py_Progress_Owner {
            inner: Progress::new(next_idx, ins_size),
        }
    }

    pub fn make_ref(&mut self) -> Py_Progress_Ref {
        Py_Progress_Ref {
            inner: RustRef::new(&mut self.inner),
        }
    }

    pub fn clone(&self) -> Py_Progress_Owner {
        Py_Progress_Owner {
            inner: self.inner.clone(),
        }
    }

    pub fn __repr__(&self) -> String {
        format!("{:?}", self.inner)
    }

    pub fn __richcmp__(&self, rhs: Py_Progress_Mut, op: CompareOp) -> bool {
        let rhs: Progress = rhs.into();

        match op {
            CompareOp::Eq => self.inner == rhs,
            CompareOp::Ne => self.inner != rhs,
            _ => panic!("Undefined operator"),
        }
    }
}

#[pymethods]
impl Py_Progress_Ref {
    pub fn __repr__(&self) -> PyResult<String> {
        self.inner.map_as_ref(|inner| format!("{:?}", inner))
    }

    pub fn __richcmp__(&self, rhs: Py_Progress_Mut, op: CompareOp) -> PyResult<bool> {
        self.inner.map_as_ref(|inner| {
            let rhs: Progress = rhs.into();

            match op {
                CompareOp::Eq => inner == &rhs,
                CompareOp::Ne => inner != &rhs,
                _ => panic!("Undefined operator"),
            }
        })
    }

    pub fn clone(&self) -> Py_Progress_Owner {
        Py_Progress_Owner {
            inner: self.inner.map_as_ref(|x| x.clone()).unwrap(),
        }
    }

    pub fn become_probe(&mut self) -> PyResult<()> {
        to_pyresult(self.inner.map_as_mut(|inner| inner.become_probe()))
    }

    pub fn become_replicate(&mut self) -> PyResult<()> {
        to_pyresult(self.inner.map_as_mut(|inner| inner.become_replicate()))
    }

    pub fn become_snapshot(&mut self, snapshot_idx: u64) -> PyResult<()> {
        to_pyresult(
            self.inner
                .map_as_mut(|inner| inner.become_snapshot(snapshot_idx)),
        )
    }

    pub fn maybe_snapshot_abort(&self) -> PyResult<bool> {
        self.inner.map_as_ref(|inner| inner.maybe_snapshot_abort())
    }

    pub fn maybe_update(&mut self, n: u64) -> PyResult<bool> {
        self.inner.map_as_mut(|inner| inner.maybe_update(n))
    }

    pub fn maybe_decr_to(
        &mut self,
        rejected: u64,
        match_hint: u64,
        request_snapshot: u64,
    ) -> PyResult<bool> {
        self.inner
            .map_as_mut(|inner| inner.maybe_decr_to(rejected, match_hint, request_snapshot))
    }

    pub fn snapshot_failure(&mut self) -> PyResult<()> {
        to_pyresult(self.inner.map_as_mut(|inner| inner.snapshot_failure()))
    }

    pub fn is_paused(&self) -> PyResult<bool> {
        self.inner.map_as_ref(|inner| inner.is_paused())
    }

    pub fn resume(&mut self) -> PyResult<()> {
        to_pyresult(self.inner.map_as_mut(|inner| inner.resume()))
    }

    pub fn update_state(&mut self, last: u64) -> PyResult<()> {
        to_pyresult(self.inner.map_as_mut(|inner| inner.update_state(last)))
    }

    pub fn update_committed(&mut self, committed_index: u64) -> PyResult<()> {
        to_pyresult(
            self.inner
                .map_as_mut(|inner| inner.update_committed(committed_index)),
        )
    }

    pub fn optimistic_update(&mut self, n: u64) -> PyResult<()> {
        to_pyresult(self.inner.map_as_mut(|inner| inner.optimistic_update(n)))
    }

    pub fn get_ins(&mut self) -> PyResult<Py_Inflights_Ref> {
        self.inner.map_as_mut(|inner| Py_Inflights_Ref {
            inner: RustRef::new(&mut inner.ins),
        })
    }

    pub fn set_ins(&mut self, inflights: Py_Inflights_Mut) -> PyResult<()> {
        self.inner.map_as_mut(|inner| inner.ins = inflights.into())
    }

    pub fn get_commit_group_id(&self) -> PyResult<u64> {
        self.inner.map_as_ref(|inner| inner.commit_group_id)
    }

    pub fn set_commit_group_id(&mut self, v: u64) -> PyResult<()> {
        self.inner.map_as_mut(|inner| inner.commit_group_id = v)
    }

    pub fn get_committed_index(&self) -> PyResult<u64> {
        self.inner.map_as_ref(|inner| inner.committed_index)
    }

    pub fn set_committed_index(&mut self, v: u64) -> PyResult<()> {
        self.inner.map_as_mut(|inner| inner.committed_index = v)
    }

    pub fn get_matched(&self) -> PyResult<u64> {
        self.inner.map_as_ref(|inner| inner.matched)
    }

    pub fn set_matched(&mut self, v: u64) -> PyResult<()> {
        self.inner.map_as_mut(|inner| inner.matched = v)
    }

    pub fn get_next_idx(&self) -> PyResult<u64> {
        self.inner.map_as_ref(|inner| inner.next_idx)
    }

    pub fn set_next_idx(&mut self, v: u64) -> PyResult<()> {
        self.inner.map_as_mut(|inner| inner.next_idx = v)
    }

    pub fn get_pending_snapshot(&self) -> PyResult<u64> {
        self.inner.map_as_ref(|inner| inner.pending_snapshot)
    }

    pub fn set_pending_snapshot(&mut self, v: u64) -> PyResult<()> {
        self.inner.map_as_mut(|inner| inner.pending_snapshot = v)
    }

    pub fn get_pending_request_snapshot(&self) -> PyResult<u64> {
        self.inner
            .map_as_ref(|inner| inner.pending_request_snapshot)
    }

    pub fn set_pending_request_snapshot(&mut self, v: u64) -> PyResult<()> {
        self.inner
            .map_as_mut(|inner| inner.pending_request_snapshot = v)
    }

    pub fn get_recent_active(&self) -> PyResult<bool> {
        self.inner.map_as_ref(|inner| inner.recent_active)
    }

    pub fn set_recent_active(&mut self, v: bool) -> PyResult<()> {
        self.inner.map_as_mut(|inner| inner.recent_active = v)
    }

    pub fn get_paused(&self) -> PyResult<bool> {
        self.inner.map_as_ref(|inner| inner.paused)
    }

    pub fn set_paused(&mut self, v: bool) -> PyResult<()> {
        self.inner.map_as_mut(|inner| inner.paused = v)
    }

    pub fn get_state(&self) -> PyResult<Py_ProgressState> {
        self.inner.map_as_ref(|inner| Py_ProgressState(inner.state))
    }

    pub fn set_state(&mut self, v: &Py_ProgressState) -> PyResult<()> {
        self.inner.map_as_mut(|inner| inner.state = v.0)
    }
}
