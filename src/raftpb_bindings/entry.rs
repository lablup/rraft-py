use crate::implement_type_conversion;
use crate::utils::errors::to_pyresult;
use crate::utils::reference::{RefMutContainer, RefMutOwner};
use prost::Message as ProstMessage;
use protobuf::Message as PbMessage;
use pyo3::pyclass::CompareOp;
use pyo3::types::{PyBytes, PyDict};
use pyo3::{intern, prelude::*};
use raft::derializer::format_entry;
use raft::eraftpb::Entry;

use super::entry_type::PyEntryType;

#[derive(Clone)]
#[pyclass(name = "Entry")]
pub struct PyEntry {
    pub inner: RefMutOwner<Entry>,
}

#[derive(Clone)]
#[pyclass(name = "EntryRef")]
pub struct PyEntryRef {
    pub inner: RefMutContainer<Entry>,
}

#[derive(FromPyObject)]
pub enum PyEntryMut<'p> {
    Owned(PyRefMut<'p, PyEntry>),
    RefMut(PyEntryRef),
}

implement_type_conversion!(Entry, PyEntryMut);

#[pymethods]
impl PyEntry {
    #[new]
    pub fn new() -> Self {
        PyEntry {
            inner: RefMutOwner::new(Entry::new()),
        }
    }

    #[staticmethod]
    pub fn default() -> Self {
        PyEntry {
            inner: RefMutOwner::new(Entry::default()),
        }
    }

    #[staticmethod]
    pub fn decode(v: &[u8]) -> PyResult<PyEntry> {
        Ok(PyEntry {
            inner: RefMutOwner::new(to_pyresult(ProstMessage::decode(v))?),
        })
    }

    pub fn make_ref(&mut self) -> PyEntryRef {
        PyEntryRef {
            inner: RefMutContainer::new(&mut self.inner),
        }
    }

    pub fn __repr__(&self) -> String {
        format_entry(&self.inner.inner)
    }

    pub fn __richcmp__(&self, py: Python, rhs: PyEntryMut, op: CompareOp) -> PyObject {
        let rhs: Entry = rhs.into();

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
impl PyEntryRef {
    pub fn __repr__(&self) -> PyResult<String> {
        self.inner.map_as_ref(|inner| format_entry(inner))
    }

    pub fn __richcmp__(&self, py: Python, rhs: PyEntryMut, op: CompareOp) -> PyResult<PyObject> {
        self.inner.map_as_ref(|inner| {
            let rhs: Entry = rhs.into();

            match op {
                CompareOp::Eq => (inner == &rhs).into_py(py),
                CompareOp::Ne => (inner != &rhs).into_py(py),
                _ => py.NotImplemented(),
            }
        })
    }

    pub fn clone(&self) -> PyResult<PyEntry> {
        Ok(PyEntry {
            inner: RefMutOwner::new(self.inner.map_as_ref(|x| x.clone())?),
        })
    }

    pub fn to_dict(&mut self, py: Python) -> PyResult<PyObject> {
        let data = self.get_data(py)?;
        let context = self.get_context(py)?;
        let entry_type = self.get_entry_type()?.__repr__();
        let index = self.get_index()?;
        let term = self.get_term()?;
        let sync_log = self.get_sync_log()?;

        self.inner.map_as_ref(|_inner| {
            let res = PyDict::new(py);
            res.set_item("data", data).unwrap();
            res.set_item("context", context).unwrap();
            res.set_item("entry_type", entry_type).unwrap();
            res.set_item("index", index).unwrap();
            res.set_item("term", term).unwrap();
            res.set_item("sync_log", sync_log).unwrap();
            res.into_py(py)
        })
    }

    pub fn encode(&self, py: Python) -> PyResult<PyObject> {
        self.inner
            .map_as_ref(|inner| PyBytes::new(py, inner.encode_to_vec().as_slice()).into_py(py))
    }

    pub fn get_context(&self, py: Python) -> PyResult<Py<PyBytes>> {
        self.inner
            .map_as_ref(|inner| PyBytes::new(py, inner.get_context()).into())
    }

    pub fn set_context(&mut self, byte_arr: &PyAny) -> PyResult<()> {
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

    pub fn set_data(&mut self, byte_arr: &PyAny) -> PyResult<()> {
        let v = byte_arr.extract::<Vec<u8>>()?;
        self.inner.map_as_mut(|inner| inner.set_data(v))
    }

    pub fn clear_data(&mut self) -> PyResult<()> {
        self.inner.map_as_mut(|inner| inner.clear_data())
    }

    pub fn get_entry_type(&self) -> PyResult<PyEntryType> {
        self.inner.map_as_ref(|inner| inner.get_entry_type().into())
    }

    pub fn set_entry_type(&mut self, typ: &PyEntryType) -> PyResult<()> {
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

#[pymethods]
impl PyEntryRef {
    pub fn compute_size(&self) -> PyResult<u32> {
        self.inner.map_as_ref(|inner| inner.compute_size())
    }
}
