use std::collections::HashMap;
use std::{collections::HashSet, hash::BuildHasherDefault};

use pyo3::intern;
use pyo3::types::{PyDict, PyList};
use pyo3::{prelude::*, types::PySet};

use crate::implement_type_conversion;
use crate::utils::reference::{RefMutContainer, RefMutOwner};
use crate::utils::unsafe_cast::{make_mut, make_static};
use fxhash::FxHasher;
use raft::{Progress, ProgressTracker};

use super::joint_config::PyJointConfigRef;
use super::progress::PyProgressRef;

#[derive(Clone)]
#[pyclass(name = "ProgressTracker")]
pub struct PyProgressTracker {
    pub inner: RefMutOwner<ProgressTracker>,
}

#[derive(Clone)]
#[pyclass(name = "ProgressTrackerRef")]
pub struct PyProgressTrackerRef {
    pub inner: RefMutContainer<ProgressTracker>,
}

#[derive(FromPyObject)]
pub enum PyProgressTrackerMut<'p> {
    Owned(PyRefMut<'p, PyProgressTracker>),
    RefMut(PyProgressTrackerRef),
}

implement_type_conversion!(ProgressTracker, PyProgressTrackerMut);

#[pymethods]
impl PyProgressTracker {
    #[new]
    pub fn new(max_inflight: usize) -> Self {
        PyProgressTracker {
            inner: RefMutOwner::new(ProgressTracker::new(max_inflight)),
        }
    }

    pub fn make_ref(&mut self) -> PyProgressTrackerRef {
        PyProgressTrackerRef {
            inner: RefMutContainer::new(&mut self.inner),
        }
    }

    pub fn __getitem__(&self, id: u64) -> Option<PyProgressRef> {
        self.inner.get(id).map(|progress| PyProgressRef {
            inner: RefMutContainer::new_raw(unsafe { make_mut(progress) }),
        })
    }

    fn __getattr__(this: PyObject, py: Python, attr: &str) -> PyResult<PyObject> {
        let reference = this.call_method0(py, intern!(py, "make_ref"))?;
        reference.getattr(py, attr)
    }
}

#[pyclass]
pub struct PyProgressMapItem(pub &'static u64, pub &'static Progress);

#[pymethods]
impl PyProgressMapItem {
    pub fn __repr__(&self) -> String {
        format!("ProgressMapItem (id: {}, progress: {:?})", self.0, self.1)
    }

    pub fn id(&self) -> u64 {
        *self.0
    }

    pub fn progress(&self) -> PyProgressRef {
        PyProgressRef {
            inner: RefMutContainer::new_raw(unsafe { make_mut(self.1) }),
        }
    }
}

#[pymethods]
impl PyProgressTrackerRef {
    pub fn clone(&self) -> PyResult<PyProgressTracker> {
        Ok(PyProgressTracker {
            inner: RefMutOwner::new(self.inner.map_as_ref(|x| x.clone())?),
        })
    }

    pub fn __getitem__(&self, id: u64) -> PyResult<Option<PyProgressRef>> {
        self.inner.map_as_ref(|inner| {
            inner.get(id).map(|progress| PyProgressRef {
                inner: RefMutContainer::new_raw(unsafe { make_mut(progress) }),
            })
        })
    }

    // TODO: Replace below function with `iter` when https://github.com/PyO3/pyo3/issues/1085 resolved.
    pub fn collect(&mut self, py: Python) -> PyResult<PyObject> {
        self.inner.map_as_mut(|inner| {
            inner
                .iter_mut()
                .map(|item| {
                    PyProgressMapItem(unsafe { make_static(item.0) }, unsafe {
                        make_static(item.1)
                    })
                })
                .collect::<Vec<_>>()
                .into_py(py)
        })
    }

    pub fn get(&self, id: u64) -> PyResult<Option<PyProgressRef>> {
        self.inner.map_as_ref(|inner| {
            inner.get(id).map(|progress| PyProgressRef {
                inner: RefMutContainer::new_raw(unsafe { make_mut(progress) }),
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

    pub fn vote_result(&mut self, votes: &PyDict) -> PyResult<String> {
        self.inner.map_as_mut(|inner| {
            let votes = votes
                .extract::<HashMap<u64, bool, BuildHasherDefault<FxHasher>>>()
                .unwrap();

            format!("{}", inner.vote_result(&votes))
        })
    }

    pub fn conf_voters(&mut self) -> PyResult<PyJointConfigRef> {
        self.inner.map_as_mut(|inner| PyJointConfigRef {
            inner: RefMutContainer::new_raw(unsafe { make_mut(inner.conf().voters()) }),
        })
    }

    pub fn conf_learners(&mut self, py: Python) -> PyResult<PyObject> {
        self.inner
            .map_as_mut(|inner| inner.conf().learners().clone().into_py(py))
    }

    pub fn tally_votes(&mut self, py: Python) -> PyResult<PyObject> {
        self.inner.map_as_mut(|inner| {
            let vote_result = inner.tally_votes();

            let res = PyList::new(py, vec![0, 0, 0]);
            res.set_item(0, vote_result.0).unwrap();
            res.set_item(1, vote_result.1).unwrap();
            res.set_item(2, format!("{}", vote_result.2)).unwrap();
            res.to_object(py)
        })
    }

    // pub fn apply_conf(&mut self, conf: Configuration, changes: MapChange, next_idx: u64) -> bool {
    //     self.inner.apply_conf(conf, changes, next_idx)
    // }
}
