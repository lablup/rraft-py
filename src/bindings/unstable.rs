use pyo3::{intern, prelude::*, types::PyList};

use external_bindings::slog::{Py_Logger_Mut, Py_Logger_Ref};
use raftpb_bindings::{
    entry::{Py_Entry_Mut, Py_Entry_Ref},
    snapshot::{Py_Snapshot_Mut, Py_Snapshot_Ref},
};

use raft::Unstable;
use utils::unsafe_cast::make_mut;

use utils::reference::RustRef;

#[pyclass(name = "Unstable")]
pub struct Py_Unstable {
    pub inner: Unstable,
}

#[pyclass(name = "Unstable_Ref")]
pub struct Py_Unstable_Ref {
    pub inner: RustRef<Unstable>,
}

#[pymethods]
impl Py_Unstable {
    #[new]
    pub fn new(offset: u64, logger: Py_Logger_Mut) -> Self {
        Py_Unstable {
            inner: Unstable::new(offset, logger.into()),
        }
    }

    pub fn make_ref(&mut self) -> Py_Unstable_Ref {
        Py_Unstable_Ref {
            inner: RustRef::new(&mut self.inner),
        }
    }

    pub fn __repr__(&self) -> String {
        format!("{:?}", self.inner)
    }

    fn __getattr__(this: PyObject, py: Python<'_>, attr: &str) -> PyResult<PyObject> {
        let reference = this.call_method0(py, intern!(py, "make_ref"))?;
        reference.getattr(py, attr)
    }
}

#[pymethods]
impl Py_Unstable_Ref {
    pub fn __repr__(&self) -> PyResult<String> {
        self.inner.map_as_ref(|inner| format!("{:?}", inner))
    }

    pub fn maybe_first_index(&self) -> PyResult<Option<u64>> {
        self.inner.map_as_ref(|inner| inner.maybe_first_index())
    }

    pub fn maybe_last_index(&self) -> PyResult<Option<u64>> {
        self.inner.map_as_ref(|inner| inner.maybe_last_index())
    }

    pub fn maybe_term(&self, idx: u64) -> PyResult<Option<u64>> {
        self.inner.map_as_ref(|inner| inner.maybe_term(idx))
    }

    pub fn must_check_outofbounds(&self, lo: u64, hi: u64) -> PyResult<()> {
        self.inner
            .map_as_ref(|inner| inner.must_check_outofbounds(lo, hi))
    }

    pub fn slice(&self, lo: u64, hi: u64, py: Python) -> PyResult<PyObject> {
        self.inner.map_as_ref(|inner| {
            inner
                .slice(lo, hi)
                .iter()
                .map(|entry| Py_Entry_Ref {
                    inner: RustRef::new(unsafe { make_mut(entry) }),
                })
                .collect::<Vec<_>>()
                .into_py(py)
        })
    }

    pub fn stable_snap(&mut self, index: u64) -> PyResult<()> {
        self.inner.map_as_mut(|inner| inner.stable_snap(index))
    }

    pub fn stable_entries(&mut self, index: u64, term: u64) -> PyResult<()> {
        self.inner
            .map_as_mut(|inner| inner.stable_entries(index, term))
    }

    pub fn restore(&mut self, snap: Py_Snapshot_Mut) -> PyResult<()> {
        self.inner.map_as_mut(|inner| inner.restore(snap.into()))
    }

    pub fn truncate_and_append(&mut self, ents: &PyList) -> PyResult<()> {
        let mut entries = ents.extract::<Vec<Py_Entry_Mut>>()?;

        self.inner.map_as_mut(|inner| {
            inner.truncate_and_append(
                entries
                    .iter_mut()
                    .map(|x| x.into())
                    .collect::<Vec<_>>()
                    .as_slice(),
            )
        })
    }

    pub fn get_entries_size(&self) -> PyResult<usize> {
        self.inner.map_as_ref(|inner| inner.entries_size)
    }

    pub fn set_entries_size(&mut self, entries_size: usize) -> PyResult<()> {
        self.inner
            .map_as_mut(|inner| inner.entries_size = entries_size)
    }

    pub fn get_offset(&self) -> PyResult<u64> {
        self.inner.map_as_ref(|inner| inner.offset)
    }

    pub fn set_offset(&mut self, offset: u64) -> PyResult<()> {
        self.inner.map_as_mut(|inner| inner.offset = offset)
    }

    pub fn get_entries(&mut self, py: Python) -> PyResult<PyObject> {
        self.inner.map_as_mut(|inner| {
            inner
                .entries
                .iter_mut()
                .map(|entry| Py_Entry_Ref {
                    inner: RustRef::new(entry),
                })
                .collect::<Vec<_>>()
                .into_py(py)
        })
    }

    pub fn set_entries(&mut self, ents: &PyList) -> PyResult<()> {
        let mut entries = ents.extract::<Vec<Py_Entry_Mut>>()?;

        self.inner.map_as_mut(|inner| {
            inner.entries = entries.iter_mut().map(|x| x.into()).collect::<Vec<_>>();
        })
    }

    pub fn get_logger(&mut self) -> PyResult<Py_Logger_Ref> {
        self.inner.map_as_mut(|inner| Py_Logger_Ref {
            inner: RustRef::new(&mut inner.logger),
        })
    }

    pub fn set_logger(&mut self) -> PyResult<()> {
        todo!()
    }

    pub fn get_snapshot(&mut self) -> PyResult<Option<Py_Snapshot_Ref>> {
        self.inner.map_as_mut(|inner| {
            inner.snapshot.as_ref().map(|snapshot| Py_Snapshot_Ref {
                inner: RustRef::new(unsafe { make_mut(snapshot) }),
            })
        })
    }

    pub fn set_snapshot(&mut self, snapshot: Option<Py_Snapshot_Mut>) -> PyResult<()> {
        self.inner.map_as_mut(|inner| match snapshot {
            Some(snapshot) => inner.snapshot = Some(snapshot.into()),
            None => inner.snapshot = None,
        })
    }
}
