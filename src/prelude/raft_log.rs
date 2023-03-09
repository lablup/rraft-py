use pyo3::prelude::*;
use pyo3::types::PyList;
use utils::errors::to_pyresult;
use utils::unsafe_cast::make_mut;

use crate::eraftpb::entry::Py_Entry_Owner;
use crate::eraftpb::snapshot::Py_Snapshot_Ref;
use crate::internal::slog::Py_Logger_Mut;

use crate::storage::mem_storage::{Py_MemStorage_Mut, Py_MemStorage_Ref};
use crate::storage::storage::Py_Storage;
use raft::prelude::Entry;
use raft::storage::MemStorage;
use raft::RaftLog;
use utils::reference::RustRef;

use super::super::eraftpb::entry::{Py_Entry_Mut, Py_Entry_Ref};
use super::unstable::Py_Unstable_Ref;

#[pyclass(name = "RaftLog__MemStorage_Owner")]
pub struct Py_RaftLog__MemStorage_Owner {
    pub inner: RaftLog<MemStorage>,
}

#[pyclass(name = "RaftLog__MemStorage_Ref")]
pub struct Py_RaftLog__MemStorage_Ref {
    pub inner: RustRef<RaftLog<MemStorage>>,
}

#[pymethods]
impl Py_RaftLog__MemStorage_Owner {
    #[new]
    pub fn new(store: Py_MemStorage_Mut, logger: Py_Logger_Mut) -> Self {
        Py_RaftLog__MemStorage_Owner {
            inner: RaftLog::new(store.into(), logger.into()),
        }
    }

    pub fn make_ref(&mut self) -> Py_RaftLog__MemStorage_Ref {
        Py_RaftLog__MemStorage_Ref {
            inner: RustRef::new(&mut self.inner),
        }
    }

    pub fn __repr__(&self) -> String {
        format!("{:?}", self.inner.to_string())
    }
}

#[pymethods]
impl Py_RaftLog__MemStorage_Ref {
    pub fn __repr__(&self) -> PyResult<String> {
        self.inner
            .map_as_ref(|inner| format!("{:?}", inner.to_string(),))
    }

    pub fn entries(&self, idx: u64, max_size: Option<u64>, py: Python) -> PyResult<PyObject> {
        self.inner.map_as_ref(|inner| {
            // TODO: Handle below type unwrapping properly.
            let entries = inner.entries(idx, max_size).unwrap();

            entries
                .into_iter()
                .map(|entry| Py_Entry_Owner { inner: entry })
                .collect::<Vec<_>>()
                .into_py(py)
        })
    }

    pub fn all_entries(&self, py: Python) -> PyResult<PyObject> {
        self.inner.map_as_ref(|inner| {
            inner
                .all_entries()
                .into_iter()
                .map(|entry| Py_Entry_Owner { inner: entry })
                .collect::<Vec<_>>()
                .into_py(py)
        })
    }

    pub fn next_entries(&self, max_size: Option<u64>, py: Python) -> PyResult<Option<PyObject>> {
        self.inner.map_as_ref(|inner| {
            inner.next_entries(max_size).and_then(|entries| {
                Some(
                    entries
                        .into_iter()
                        .map(|entry| Py_Entry_Owner { inner: entry })
                        .collect::<Vec<_>>()
                        .into_py(py),
                )
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
                .and_then(|entries| {
                    let entries = entries
                        .into_iter()
                        .map(|entry| Py_Entry_Owner { inner: entry })
                        .collect::<Vec<_>>();

                    Some(entries.into_py(py))
                })
        })
    }

    pub fn append(&mut self, ents: &PyList) -> PyResult<u64> {
        self.inner.map_as_mut(|inner| {
            let mut entries = ents.extract::<Vec<Py_Entry_Mut>>().unwrap();
            inner.append(
                entries
                    .iter_mut()
                    .map(|x| x.into())
                    .collect::<Vec<Entry>>()
                    .as_slice(),
            )
        })
    }

    pub fn applied(&self) -> PyResult<u64> {
        self.inner.map_as_ref(|inner| inner.applied())
    }

    pub fn find_conflict(&self, ents: &PyList) -> PyResult<u64> {
        self.inner.map_as_ref(|inner| {
            let mut entries = ents.extract::<Vec<Py_Entry_Mut>>().unwrap();

            inner.find_conflict(
                entries
                    .iter_mut()
                    .map(|x| x.into())
                    .collect::<Vec<Entry>>()
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
        self.inner.map_as_mut(|inner| {
            let mut entries = ents.extract::<Vec<Py_Entry_Mut>>().unwrap();

            inner.maybe_append(
                idx,
                term,
                committed,
                entries
                    .iter_mut()
                    .map(|x| x.into())
                    .collect::<Vec<Entry>>()
                    .as_slice(),
            )
        })
    }

    pub fn snapshot(&self, request_index: u64) -> PyResult<Py_Snapshot_Ref> {
        self.inner
            .map_as_ref(|inner| match inner.snapshot(request_index) {
                Ok(mut snapshot) => Py_Snapshot_Ref {
                    inner: RustRef::new(&mut snapshot),
                },
                Err(e) => panic!("snapshot error: {:?}", e),
            })
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
            .map_as_ref(|inner| inner.term(idx))
            .and_then(to_pyresult)
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

    pub fn unstable(&self) -> PyResult<Py_Unstable_Ref> {
        self.inner.map_as_ref(|inner| Py_Unstable_Ref {
            inner: RustRef::new(unsafe { make_mut(inner.unstable()) }),
        })
    }

    pub fn unstable_entries(&self, py: Python) -> PyResult<PyObject> {
        self.inner
            .map_as_ref(|inner| {
                inner
                    .unstable_entries()
                    .iter()
                    .map(|entry| Py_Entry_Ref {
                        inner: RustRef::new(unsafe { make_mut(entry) }),
                    })
                    .collect::<Vec<_>>()
            })
            .map(|entries| entries.into_py(py))
    }

    pub fn unstable_snapshot(&self) -> PyResult<Option<Py_Snapshot_Ref>> {
        self.inner
            .map_as_ref(|inner| match inner.unstable_snapshot() {
                Some(snapshot) => Some(Py_Snapshot_Ref {
                    inner: RustRef::new(unsafe { make_mut(snapshot) }),
                }),
                None => None,
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

    pub fn store(&mut self) -> PyResult<Py_MemStorage_Ref> {
        self.inner.map_as_mut(|inner| Py_MemStorage_Ref {
            inner: RustRef::new(unsafe { make_mut(inner.store()) }),
        })
    }

    pub fn get_store(&self) -> PyResult<Py_MemStorage_Ref> {
        self.inner.map_as_ref(|inner| Py_MemStorage_Ref {
            inner: RustRef::new(unsafe { make_mut(inner.store()) }),
        })
    }
}

#[pyclass(name = "RaftLog_Owner")]
pub struct Py_RaftLog__PyStorage_Owner {
    pub inner: RaftLog<Py_Storage>,
}

#[pymethods]
impl Py_RaftLog__PyStorage_Owner {}

#[pyclass(name = "RaftLog_Ref")]
pub struct Py_RaftLog__PyStorage_Ref {
    pub inner: RustRef<RaftLog<Py_Storage>>,
}

impl Py_RaftLog__PyStorage_Ref {}
