use crate::utils::reference::{RefMutContainer, RefMutOwner};
use crate::utils::unsafe_cast::make_mut;
use pyo3::types::PyList;
use pyo3::{intern, prelude::*};

use crate::external_bindings::slog::PyLoggerMut;
use crate::raftpb_bindings::snapshot::{PySnapshotMut, PySnapshotRef};

use raft::{GetEntriesContext, RaftLog};

use super::py_storage::{PyStorage, PyStorageRef};
use crate::bindings::{get_entries_context::PyGetEntriesContextRef, unstable::PyUnstableRef};
use crate::raftpb_bindings::entry::{PyEntry, PyEntryMut, PyEntryRef};
use crate::utils::errors::PyRaftError;

#[pyclass(name = "RaftLog")]
pub struct PyRaftLog {
    pub inner: RefMutOwner<RaftLog<PyStorage>>,
}

#[pyclass(name = "RaftLogRef")]
pub struct PyRaftLogRef {
    pub inner: RefMutContainer<RaftLog<PyStorage>>,
}

#[pymethods]
impl PyRaftLog {
    #[new]
    pub fn new(store: &PyStorage, logger: PyLoggerMut) -> Self {
        PyRaftLog {
            inner: RefMutOwner::new(RaftLog::new(store.clone(), logger.into())),
        }
    }

    pub fn make_ref(&mut self) -> PyRaftLogRef {
        PyRaftLogRef {
            inner: RefMutContainer::new(&mut self.inner),
        }
    }

    pub fn __repr__(&self) -> String {
        format!("{:?}", self.inner.to_string())
    }

    fn __getattr__(this: PyObject, py: Python, attr: &str) -> PyResult<PyObject> {
        let reference = this.call_method0(py, intern!(py, "make_ref"))?;
        reference.getattr(py, attr)
    }
}

#[pymethods]
impl PyRaftLogRef {
    pub fn __repr__(&self) -> PyResult<String> {
        self.inner
            .map_as_ref(|inner| format!("{:?}", inner.to_string(),))
    }

    pub fn entries(
        &self,
        idx: u64,
        context: &mut PyGetEntriesContextRef,
        max_size: Option<u64>,
        py: Python,
    ) -> PyResult<PyObject> {
        let context = context.inner.map_as_mut(|context| unsafe {
            std::ptr::replace(context, GetEntriesContext::empty(false))
        })?;

        self.inner.map_as_ref(|inner| {
            inner
                .entries(idx, max_size, context)
                .map(|entries| {
                    entries
                        .into_iter()
                        .map(|entry| PyEntry {
                            inner: RefMutOwner::new(entry),
                        })
                        .collect::<Vec<_>>()
                        .into_py(py)
                })
                .map_err(|e| PyRaftError(e).into())
        })?
    }

    pub fn all_entries(&self, py: Python) -> PyResult<PyObject> {
        self.inner.map_as_ref(|inner| {
            inner
                .all_entries()
                .into_iter()
                .map(|entry| PyEntry {
                    inner: RefMutOwner::new(entry),
                })
                .collect::<Vec<_>>()
                .into_py(py)
        })
    }

    pub fn next_entries(&self, max_size: Option<u64>, py: Python) -> PyResult<Option<PyObject>> {
        self.inner.map_as_ref(|inner| {
            inner.next_entries(max_size).map(|entries| {
                entries
                    .into_iter()
                    .map(|entry| PyEntry {
                        inner: RefMutOwner::new(entry),
                    })
                    .collect::<Vec<_>>()
                    .into_py(py)
            })
        })
    }

    pub fn next_entries_since(
        &self,
        since_idx: u64,
        max_size: Option<u64>,
        py: Python,
    ) -> PyResult<Option<PyObject>> {
        self.inner.map_as_ref(|inner| {
            inner
                .next_entries_since(since_idx, max_size)
                .map(|entries| {
                    entries
                        .into_iter()
                        .map(|entry| PyEntry {
                            inner: RefMutOwner::new(entry),
                        })
                        .collect::<Vec<_>>()
                        .into_py(py)
                })
        })
    }

    pub fn append(&mut self, ents: &PyList) -> PyResult<u64> {
        let mut entries = ents.extract::<Vec<PyEntryMut>>()?;

        self.inner.map_as_mut(|inner| {
            inner.append(
                entries
                    .iter_mut()
                    .map(|x| x.into())
                    .collect::<Vec<_>>()
                    .as_slice(),
            )
        })
    }

    pub fn applied(&self) -> PyResult<u64> {
        self.inner.map_as_ref(|inner| inner.applied())
    }

    pub fn find_conflict(&self, ents: &PyList) -> PyResult<u64> {
        let mut entries = ents.extract::<Vec<PyEntryMut>>()?;

        self.inner.map_as_ref(|inner| {
            inner.find_conflict(
                entries
                    .iter_mut()
                    .map(|x| x.into())
                    .collect::<Vec<_>>()
                    .as_slice(),
            )
        })
    }

    pub fn find_conflict_by_term(&self, index: u64, term: u64) -> PyResult<(u64, Option<u64>)> {
        self.inner
            .map_as_ref(|inner| inner.find_conflict_by_term(index, term))
    }

    pub fn commit_to(&mut self, to_commit: u64) -> PyResult<()> {
        self.inner.map_as_mut(|inner| inner.commit_to(to_commit))
    }

    pub fn commit_info(&self) -> PyResult<(u64, u64)> {
        self.inner.map_as_ref(|inner| inner.commit_info())
    }

    pub fn has_next_entries(&self) -> PyResult<bool> {
        self.inner.map_as_ref(|inner| inner.has_next_entries())
    }

    pub fn has_next_entries_since(&self, since_idx: u64) -> PyResult<bool> {
        self.inner
            .map_as_ref(|inner| inner.has_next_entries_since(since_idx))
    }

    pub fn is_up_to_date(&self, last_index: u64, term: u64) -> PyResult<bool> {
        self.inner
            .map_as_ref(|inner| inner.is_up_to_date(last_index, term))
    }

    pub fn maybe_commit(&mut self, max_index: u64, term: u64) -> PyResult<bool> {
        self.inner
            .map_as_mut(|inner| inner.maybe_commit(max_index, term))
    }

    pub fn maybe_persist(&mut self, index: u64, term: u64) -> PyResult<bool> {
        self.inner
            .map_as_mut(|inner| inner.maybe_persist(index, term))
    }

    pub fn maybe_persist_snap(&mut self, index: u64) -> PyResult<bool> {
        self.inner
            .map_as_mut(|inner| inner.maybe_persist_snap(index))
    }

    pub fn maybe_append(
        &mut self,
        idx: u64,
        term: u64,
        committed: u64,
        ents: &PyList,
    ) -> PyResult<Option<(u64, u64)>> {
        let mut entries = ents.extract::<Vec<PyEntryMut>>()?;

        self.inner.map_as_mut(|inner| {
            inner.maybe_append(
                idx,
                term,
                committed,
                entries
                    .iter_mut()
                    .map(|x| x.into())
                    .collect::<Vec<_>>()
                    .as_slice(),
            )
        })
    }

    pub fn snapshot(&self, request_index: u64, to: u64) -> PyResult<PySnapshotRef> {
        self.inner.map_as_ref(|inner| {
            inner
                .snapshot(request_index, to)
                .map(|mut snapshot| PySnapshotRef {
                    inner: RefMutContainer::new_raw(&mut snapshot),
                })
                .map_err(|e| PyRaftError(e).into())
        })?
    }

    pub fn stable_entries(&mut self, index: u64, term: u64) -> PyResult<()> {
        self.inner
            .map_as_mut(|inner| inner.stable_entries(index, term))
    }

    pub fn stable_snap(&mut self, index: u64) -> PyResult<()> {
        self.inner.map_as_mut(|inner| inner.stable_snap(index))
    }

    pub fn term(&self, idx: u64) -> PyResult<u64> {
        self.inner
            .map_as_ref(|inner| inner.term(idx).map_err(|e| PyRaftError(e).into()))?
    }

    pub fn last_term(&self) -> PyResult<u64> {
        self.inner.map_as_ref(|inner| inner.last_term())
    }

    pub fn match_term(&self, idx: u64, term: u64) -> PyResult<bool> {
        self.inner.map_as_ref(|inner| inner.match_term(idx, term))
    }

    pub fn first_index(&self) -> PyResult<u64> {
        self.inner.map_as_ref(|inner| inner.first_index())
    }

    pub fn last_index(&self) -> PyResult<u64> {
        self.inner.map_as_ref(|inner| inner.last_index())
    }

    pub fn unstable(&self) -> PyResult<PyUnstableRef> {
        self.inner.map_as_ref(|inner| PyUnstableRef {
            inner: RefMutContainer::new_raw(unsafe { make_mut(inner.unstable()) }),
        })
    }

    pub fn unstable_entries(&self, py: Python) -> PyResult<PyObject> {
        self.inner
            .map_as_ref(|inner| {
                inner
                    .unstable_entries()
                    .iter()
                    .map(|entry| PyEntryRef {
                        inner: RefMutContainer::new_raw(unsafe { make_mut(entry) }),
                    })
                    .collect::<Vec<_>>()
            })
            .map(|entries| entries.into_py(py))
    }

    pub fn unstable_snapshot(&self) -> PyResult<Option<PySnapshotRef>> {
        self.inner.map_as_ref(|inner| {
            inner
                .unstable_snapshot()
                .as_ref()
                .map(|snapshot| PySnapshotRef {
                    inner: RefMutContainer::new_raw(unsafe { make_mut(snapshot) }),
                })
        })
    }

    pub fn get_applied(&self) -> PyResult<u64> {
        self.inner.map_as_ref(|inner| inner.applied)
    }

    pub fn set_applied(&mut self, v: u64) -> PyResult<()> {
        self.inner.map_as_mut(|inner| inner.applied = v)
    }

    pub fn get_committed(&self) -> PyResult<u64> {
        self.inner.map_as_ref(|inner| inner.committed)
    }

    pub fn set_committed(&mut self, v: u64) -> PyResult<()> {
        self.inner.map_as_mut(|inner| inner.committed = v)
    }

    pub fn get_persisted(&self) -> PyResult<u64> {
        self.inner.map_as_ref(|inner| inner.persisted)
    }

    pub fn set_persisted(&mut self, v: u64) -> PyResult<()> {
        self.inner.map_as_mut(|inner| inner.persisted = v)
    }

    pub fn store(&mut self) -> PyResult<PyStorageRef> {
        self.inner.map_as_mut(|inner| PyStorageRef {
            inner: RefMutContainer::new_raw(inner.mut_store()),
        })
    }

    pub fn get_store(&mut self) -> PyResult<PyStorageRef> {
        self.inner.map_as_mut(|inner| PyStorageRef {
            inner: RefMutContainer::new_raw(inner.mut_store()),
        })
    }

    pub fn slice(
        &self,
        _low: u64,
        _high: u64,
        context: &mut PyGetEntriesContextRef,
        _max_size: Option<u64>,
        _py: Python,
    ) -> PyResult<PyObject> {
        let _context = context.inner.map_as_mut(|context| unsafe {
            std::ptr::replace(context, GetEntriesContext::empty(false))
        })?;

        // self.inner.map_as_ref(|inner| {
        //     inner
        //         .slice(low, high, max_size, context)
        //         .iter()
        //         .map(|entries| {
        //             entries.iter().map(|entry| {
        //                 PyEntryRef {
        //                     inner: RefMutContainer::new(unsafe { make_mut(entry) }),
        //                 }
        //             }).collect::<Vec<_>>()
        //         }).collect::<Result<Vec<PyEntryRef>, _>>()
        // }).and_then(to_pyresult)

        todo!()
    }

    pub fn restore(&mut self, snapshot: PySnapshotMut) -> PyResult<()> {
        self.inner
            .map_as_mut(|inner| inner.restore(snapshot.into()))
    }
}
