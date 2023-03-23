use pyo3::pyclass::CompareOp;
use pyo3::types::PyBytes;
use pyo3::{prelude::*, types::PyList};

use raft::eraftpb::Entry;

use utils::reference::RustRef;

use super::entry_type::Py_EntryType;

#[derive(Clone)]
#[pyclass(name = "Entry_Owner")]
pub struct Py_Entry_Owner {
    pub inner: Entry,
}

#[derive(Clone)]
#[pyclass(name = "Entry_Ref")]
pub struct Py_Entry_Ref {
    pub inner: RustRef<Entry>,
}

#[derive(FromPyObject)]
pub enum Py_Entry_Mut<'p> {
    Owned(PyRefMut<'p, Py_Entry_Owner>),
    RefMut(Py_Entry_Ref),
}

impl Into<Entry> for Py_Entry_Mut<'_> {
    fn into(self) -> Entry {
        match self {
            Py_Entry_Mut::Owned(x) => x.inner.clone(),
            Py_Entry_Mut::RefMut(mut x) => x.inner.map_as_mut(|x| x.clone()).unwrap(),
        }
    }
}

impl Into<Entry> for &mut Py_Entry_Mut<'_> {
    fn into(self) -> Entry {
        match self {
            Py_Entry_Mut::Owned(x) => x.inner.clone(),
            Py_Entry_Mut::RefMut(x) => x.inner.map_as_mut(|x| x.clone()).unwrap(),
        }
    }
}

#[pymethods]
impl Py_Entry_Owner {
    #[new]
    pub fn new() -> Self {
        Py_Entry_Owner {
            inner: Entry::new_(),
        }
    }

    #[staticmethod]
    pub fn default() -> Self {
        Py_Entry_Owner {
            inner: Entry::default(),
        }
    }

    pub fn make_ref(&mut self) -> Py_Entry_Ref {
        Py_Entry_Ref {
            inner: RustRef::new(&mut self.inner),
        }
    }

    pub fn __repr__(&self) -> String {
        format!("{:?}", self.inner)
    }

    pub fn __richcmp__(&self, rhs: Py_Entry_Mut, op: CompareOp) -> bool {
        let rhs: Entry = rhs.into();

        match op {
            CompareOp::Eq => self.inner == rhs,
            CompareOp::Ne => self.inner != rhs,
            _ => panic!("Undefined operator"),
        }
    }

    fn __getattr__(this: PyObject, py: Python<'_>, attr: &str) -> PyResult<PyObject> {
        let reference = this.call_method0(py, "make_ref")?;
        reference.getattr(py, attr)
    }
}

#[pymethods]
impl Py_Entry_Ref {
    pub fn __repr__(&self) -> PyResult<String> {
        self.inner.map_as_ref(|inner| format!("{:?}", inner))
    }

    pub fn __richcmp__(&self, rhs: Py_Entry_Mut, op: CompareOp) -> PyResult<bool> {
        self.inner.map_as_ref(|inner| {
            let rhs: Entry = rhs.into();

            match op {
                CompareOp::Eq => inner == &rhs,
                CompareOp::Ne => inner != &rhs,
                _ => panic!("Undefined operator"),
            }
        })
    }

    pub fn clone(&self) -> PyResult<Py_Entry_Owner> {
        Ok(Py_Entry_Owner {
            inner: self.inner.map_as_ref(|x| x.clone())?,
        })
    }

    pub fn get_context(&self, py: Python) -> PyResult<Py<PyBytes>> {
        self.inner
            .map_as_ref(|inner| PyBytes::new(py, inner.get_context()).into())
    }

    pub fn set_context(&mut self, byte_arr: &PyBytes) -> PyResult<()> {
        let v = byte_arr.extract::<Vec<u8>>()?;
        self.inner.map_as_mut(|inner| inner.set_context(v))
    }

    pub fn clear_context(&mut self) -> PyResult<()> {
        self.inner.map_as_mut(|inner| inner.clear_context())
    }

    pub fn get_data(&self, py: Python) -> PyResult<Py<PyBytes>> {
        self.inner
            .map_as_ref(|inner| PyBytes::new(py, inner.get_data()).into())
    }

    pub fn set_data(&mut self, byte_arr: &PyBytes) -> PyResult<()> {
        let v = byte_arr.extract::<Vec<u8>>()?;
        self.inner.map_as_mut(|inner| inner.set_data(v))
    }

    pub fn clear_data(&mut self) -> PyResult<()> {
        self.inner.map_as_mut(|inner| inner.clear_data())
    }

    pub fn get_entry_type(&self) -> PyResult<Py_EntryType> {
        self.inner.map_as_ref(|inner| inner.get_entry_type().into())
    }

    pub fn set_entry_type(&mut self, typ: &Py_EntryType) -> PyResult<()> {
        self.inner.map_as_mut(|inner| inner.set_entry_type(typ.0))
    }

    pub fn clear_entry_type(&mut self) -> PyResult<()> {
        self.inner.map_as_mut(|inner| inner.clear_entry_type())
    }

    pub fn get_sync_log(&self) -> PyResult<bool> {
        self.inner.map_as_ref(|inner| inner.get_sync_log())
    }

    pub fn set_sync_log(&mut self, v: bool) -> PyResult<()> {
        self.inner.map_as_mut(|inner| inner.set_sync_log(v))
    }

    pub fn clear_sync_log(&mut self) -> PyResult<()> {
        self.inner.map_as_mut(|inner| inner.clear_sync_log())
    }

    pub fn get_term(&self) -> PyResult<u64> {
        self.inner.map_as_ref(|inner| inner.get_term())
    }

    pub fn set_term(&mut self, v: u64) -> PyResult<()> {
        self.inner.map_as_mut(|inner| inner.set_term(v))
    }

    pub fn clear_term(&mut self) -> PyResult<()> {
        self.inner.map_as_mut(|inner| inner.clear_term())
    }

    pub fn get_index(&self) -> PyResult<u64> {
        self.inner.map_as_ref(|inner| inner.get_index())
    }

    pub fn set_index(&mut self, v: u64) -> PyResult<()> {
        self.inner.map_as_mut(|inner| inner.set_index(v))
    }

    pub fn clear_index(&mut self) -> PyResult<()> {
        self.inner.map_as_mut(|inner| inner.clear_index())
    }
}
