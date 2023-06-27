use std::collections::HashMap;
use std::{collections::HashSet, hash::BuildHasherDefault};

use pyo3::intern;
use pyo3::types::PyDict;
use pyo3::{prelude::*, types::PySet};

use fxhash::FxHasher;
use raft::{Progress, ProgressTracker};
use utils::implement_type_conversion;
use utils::reference::{RefMutOwner, RustRef};
use utils::unsafe_cast::{make_mut, make_static};

use super::joint_config::Py_JointConfig_Ref;
use super::progress::Py_Progress_Ref;

#[derive(Clone)]
#[pyclass(name = "ProgressTracker")]
pub struct Py_ProgressTracker {
    pub inner: RefMutOwner<ProgressTracker>,
}

#[derive(Clone)]
#[pyclass(name = "ProgressTracker_Ref")]
pub struct Py_ProgressTracker_Ref {
    pub inner: RustRef<ProgressTracker>,
}

#[derive(FromPyObject)]
pub enum Py_ProgressTracker_Mut<'p> {
    Owned(PyRefMut<'p, Py_ProgressTracker>),
    RefMut(Py_ProgressTracker_Ref),
}

implement_type_conversion!(ProgressTracker, Py_ProgressTracker_Mut);

#[pymethods]
impl Py_ProgressTracker {
    #[new]
    pub fn new(max_inflight: usize) -> Self {
        Py_ProgressTracker {
            inner: RefMutOwner::new(ProgressTracker::new(max_inflight)),
        }
    }

    pub fn make_ref(&mut self) -> Py_ProgressTracker_Ref {
        Py_ProgressTracker_Ref {
            inner: RustRef::new(&mut self.inner),
        }
    }

    pub fn __getitem__(&self, id: u64) -> Option<Py_Progress_Ref> {
        self.inner.get(id).map(|progress| Py_Progress_Ref {
            inner: RustRef::new_raw(unsafe { make_mut(progress) }),
        })
    }

    fn __getattr__(this: PyObject, py: Python, attr: &str) -> PyResult<PyObject> {
        let reference = this.call_method0(py, intern!(py, "make_ref"))?;
        reference.getattr(py, attr)
    }
}

#[pyclass]
pub struct Py_ProgressMapItem(pub &'static u64, pub &'static Progress);

#[pymethods]
impl Py_ProgressMapItem {
    pub fn id(&self) -> u64 {
        *self.0
    }

    pub fn progress(&self) -> Py_Progress_Ref {
        Py_Progress_Ref {
            inner: RustRef::new_raw(unsafe { make_mut(self.1) }),
        }
    }
}

#[pymethods]
impl Py_ProgressTracker_Ref {
    pub fn clone(&self) -> PyResult<Py_ProgressTracker> {
        Ok(Py_ProgressTracker {
            inner: RefMutOwner::new(self.inner.map_as_ref(|x| x.clone())?),
        })
    }

    pub fn __getitem__(&self, id: u64) -> PyResult<Option<Py_Progress_Ref>> {
        self.inner.map_as_ref(|inner| {
            inner.get(id).map(|progress| Py_Progress_Ref {
                inner: RustRef::new_raw(unsafe { make_mut(progress) }),
            })
        })
    }

    // TODO: Replace below function with `iter` when https://github.com/PyO3/pyo3/issues/1085 resolved.
    pub fn collect(&mut self, py: Python) -> PyResult<PyObject> {
        self.inner.map_as_mut(|inner| {
            inner
                .iter_mut()
                .map(|item| {
                    Py_ProgressMapItem(unsafe { make_static(item.0) }, unsafe {
                        make_static(item.1)
                    })
                })
                .collect::<Vec<_>>()
                .into_py(py)
        })
    }

    pub fn get(&self, id: u64) -> PyResult<Option<Py_Progress_Ref>> {
        self.inner.map_as_ref(|inner| {
            inner.get(id).map(|progress| Py_Progress_Ref {
                inner: RustRef::new_raw(unsafe { make_mut(progress) }),
            })
        })
    }

    pub fn group_commit(&self) -> PyResult<bool> {
        self.inner.map_as_ref(|inner| inner.group_commit())
    }

    pub fn votes(&self, py: Python) -> PyResult<PyObject> {
        self.inner.map_as_ref(|inner| inner.votes().to_object(py))
    }

    pub fn enable_group_commit(&mut self, enable: bool) -> PyResult<()> {
        self.inner
            .map_as_mut(|inner| inner.enable_group_commit(enable))
    }

    pub fn has_quorum(&self, potential_quorum: &PySet) -> PyResult<bool> {
        let potential_quorum =
            potential_quorum.extract::<HashSet<u64, BuildHasherDefault<FxHasher>>>()?;

        self.inner
            .map_as_ref(|inner| inner.has_quorum(&potential_quorum))
    }

    pub fn is_singleton(&self) -> PyResult<bool> {
        self.inner.map_as_ref(|inner| inner.is_singleton())
    }

    pub fn quorum_recently_active(&mut self, perspective_of: u64) -> PyResult<bool> {
        self.inner
            .map_as_mut(|inner| inner.quorum_recently_active(perspective_of))
    }

    pub fn maximal_committed_index(&mut self) -> PyResult<(u64, bool)> {
        self.inner
            .map_as_mut(|inner| inner.maximal_committed_index())
    }

    pub fn record_vote(&mut self, id: u64, vote: bool) -> PyResult<()> {
        self.inner.map_as_mut(|inner| inner.record_vote(id, vote))
    }

    pub fn reset_votes(&mut self) -> PyResult<()> {
        self.inner.map_as_mut(|inner| inner.reset_votes())
    }

    // TODO: Resolve "below types not exposed" issue.
    pub fn vote_result(&mut self, votes: &PyDict) -> PyResult<()> {
        self.inner.map_as_mut(|inner| {
            let votes = votes
                .extract::<HashMap<u64, bool, BuildHasherDefault<FxHasher>>>()
                .unwrap();

            let _vote_result = inner.vote_result(&votes);
        })
    }

    pub fn conf_voters(&mut self) -> PyResult<Py_JointConfig_Ref> {
        self.inner.map_as_mut(|inner| Py_JointConfig_Ref {
            inner: RustRef::new_raw(unsafe { make_mut(inner.conf().voters()) }),
        })
    }

    pub fn conf_learners(&mut self, py: Python) -> PyResult<PyObject> {
        self.inner
            .map_as_mut(|inner| inner.conf().learners().clone().into_py(py))
    }

    // pub fn tally_votes(&self) -> (usize, usize, VoteResult) {
    //     self.inner.tally_votes()
    // }

    // pub fn apply_conf(&mut self, conf: Configuration, changes: MapChange, next_idx: u64) -> bool {
    //     self.inner.apply_conf(conf, changes, next_idx)
    // }
}
