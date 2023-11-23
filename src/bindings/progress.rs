use pyo3::types::PyDict;
use pyo3::{intern, prelude::*, pyclass::CompareOp};

use crate::implement_type_conversion;
use crate::utils::reference::{RefMutContainer, RefMutOwner};
use raft::Progress;

use super::{
    inflights::{PyInflightsMut, PyInflightsRef},
    progress_state::PyProgressState,
};

#[derive(Clone)]
#[pyclass(name = "Progress")]
pub struct PyProgress {
    pub inner: RefMutOwner<Progress>,
}

#[derive(Clone)]
#[pyclass(name = "ProgressRef")]
pub struct PyProgressRef {
    pub inner: RefMutContainer<Progress>,
}

#[derive(FromPyObject)]
pub enum PyProgressMut<'p> {
    Owned(PyRefMut<'p, PyProgress>),
    RefMut(PyProgressRef),
}

implement_type_conversion!(Progress, PyProgressMut);

#[pymethods]
impl PyProgress {
    #[new]
    pub fn new(next_idx: u64, ins_size: usize) -> Self {
        PyProgress {
            inner: RefMutOwner::new(Progress::new(next_idx, ins_size)),
        }
    }

    pub fn make_ref(&mut self) -> PyProgressRef {
        PyProgressRef {
            inner: RefMutContainer::new(&mut self.inner),
        }
    }

    pub fn __repr__(&self) -> String {
        format!("{:?}", self.inner.inner)
    }

    pub fn __richcmp__(&self, py: Python, rhs: PyProgressMut, op: CompareOp) -> PyObject {
        let rhs: Progress = rhs.into();

        match op {
            CompareOp::Eq => (self.inner.inner == rhs).into_py(py),
            CompareOp::Ne => (self.inner.inner != rhs).into_py(py),
            _ => py.NotImplemented(),
        }
    }

    fn __getattr__(this: PyObject, py: Python, attr: &str) -> PyResult<PyObject> {
        let reference = this.call_method0(py, intern!(py, "make_ref"))?;
        reference.getattr(py, attr)
    }
}

#[pymethods]
impl PyProgressRef {
    pub fn __repr__(&self) -> PyResult<String> {
        self.inner.map_as_ref(|inner| format!("{:?}", inner))
    }

    pub fn __richcmp__(&self, py: Python, rhs: PyProgressMut, op: CompareOp) -> PyResult<PyObject> {
        self.inner.map_as_ref(|inner| {
            let rhs: Progress = rhs.into();

            match op {
                CompareOp::Eq => (inner == &rhs).into_py(py),
                CompareOp::Ne => (inner != &rhs).into_py(py),
                _ => py.NotImplemented(),
            }
        })
    }

    pub fn to_dict(&mut self, py: Python) -> PyResult<PyObject> {
        let commit_group_id = self.get_commit_group_id()?;
        let committed_index = self.get_committed_index()?;
        // let ins = self.get_ins()?;
        let matched = self.get_matched()?;
        let next_idx = self.get_next_idx()?;
        let paused = self.get_paused()?;
        let pending_request_snapshot = self.get_pending_request_snapshot()?;
        let pending_snapshot = self.get_pending_snapshot()?;
        let recent_active = self.get_recent_active()?;
        let state = self.get_state()?.__repr__();

        self.inner.map_as_ref(|_inner| {
            let res = PyDict::new(py);
            res.set_item("commit_group_id", commit_group_id).unwrap();
            res.set_item("committed_index", committed_index).unwrap();
            res.set_item("matched", matched).unwrap();
            res.set_item("next_idx", next_idx).unwrap();
            res.set_item("paused", paused).unwrap();
            res.set_item("pending_request_snapshot", pending_request_snapshot)
                .unwrap();
            res.set_item("pending_snapshot", pending_snapshot).unwrap();
            res.set_item("recent_active", recent_active).unwrap();
            res.set_item("state", state).unwrap();
            res.into_py(py)
        })
    }

    pub fn clone(&self) -> PyResult<PyProgress> {
        Ok(PyProgress {
            inner: RefMutOwner::new(self.inner.map_as_ref(|x| x.clone())?),
        })
    }

    pub fn become_probe(&mut self) -> PyResult<()> {
        self.inner.map_as_mut(|inner| inner.become_probe())
    }

    pub fn become_replicate(&mut self) -> PyResult<()> {
        self.inner.map_as_mut(|inner| inner.become_replicate())
    }

    pub fn become_snapshot(&mut self, snapshot_idx: u64) -> PyResult<()> {
        self.inner
            .map_as_mut(|inner| inner.become_snapshot(snapshot_idx))
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
        self.inner.map_as_mut(|inner| inner.snapshot_failure())
    }

    pub fn pause(&mut self) -> PyResult<()> {
        self.inner.map_as_mut(|inner| inner.pause())
    }

    pub fn is_paused(&self) -> PyResult<bool> {
        self.inner.map_as_ref(|inner| inner.is_paused())
    }

    pub fn is_snapshot_caught_up(&self) -> PyResult<bool> {
        self.inner.map_as_ref(|inner| inner.is_snapshot_caught_up())
    }

    pub fn resume(&mut self) -> PyResult<()> {
        self.inner.map_as_mut(|inner| inner.resume())
    }

    pub fn update_state(&mut self, last: u64) -> PyResult<()> {
        self.inner.map_as_mut(|inner| inner.update_state(last))
    }

    pub fn update_committed(&mut self, committed_index: u64) -> PyResult<()> {
        self.inner
            .map_as_mut(|inner| inner.update_committed(committed_index))
    }

    pub fn optimistic_update(&mut self, n: u64) -> PyResult<()> {
        self.inner.map_as_mut(|inner| inner.optimistic_update(n))
    }

    pub fn get_ins(&mut self) -> PyResult<PyInflightsRef> {
        self.inner.map_as_mut(|inner| PyInflightsRef {
            inner: RefMutContainer::new_raw(&mut inner.ins),
        })
    }

    pub fn set_ins(&mut self, inflights: PyInflightsMut) -> PyResult<()> {
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

    pub fn get_state(&self) -> PyResult<PyProgressState> {
        self.inner.map_as_ref(|inner| PyProgressState(inner.state))
    }

    pub fn set_state(&mut self, v: &PyProgressState) -> PyResult<()> {
        self.inner.map_as_mut(|inner| inner.state = v.0)
    }
}
