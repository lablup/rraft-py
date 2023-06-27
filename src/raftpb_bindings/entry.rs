use prost::Message as ProstMessage;
use protobuf::Message as PbMessage;
use pyo3::pyclass::CompareOp;
use pyo3::types::PyBytes;
use pyo3::{intern, prelude::*};
use raft::eraftpb::Entry;
use utils::errors::to_pyresult;
use utils::implement_type_conversion;
use utils::reference::{RefMutContainer, RefMutOwner};

use super::entry_type::Py_EntryType;

#[derive(Clone)]
#[pyclass(name = "Entry")]
pub struct Py_Entry {
    pub inner: RefMutOwner<Entry>,
}

#[derive(Clone)]
#[pyclass(name = "Entry_Ref")]
pub struct Py_Entry_Ref {
    pub inner: RefMutContainer<Entry>,
}

#[derive(FromPyObject)]
pub enum Py_Entry_Mut<'p> {
    Owned(PyRefMut<'p, Py_Entry>),
    RefMut(Py_Entry_Ref),
}

implement_type_conversion!(Entry, Py_Entry_Mut);

#[pymethods]
impl Py_Entry {
    #[new]
    pub fn new() -> Self {
        Py_Entry {
            inner: RefMutOwner::new(Entry::new()),
        }
    }

    #[staticmethod]
    pub fn default() -> Self {
        Py_Entry {
            inner: RefMutOwner::new(Entry::default()),
        }
    }

    #[staticmethod]
    pub fn decode(v: &[u8]) -> PyResult<Py_Entry> {
        Ok(Py_Entry {
            inner: RefMutOwner::new(to_pyresult(ProstMessage::decode(v))?),
        })
    }

    pub fn make_ref(&mut self) -> Py_Entry_Ref {
        Py_Entry_Ref {
            inner: RefMutContainer::new(&mut self.inner),
        }
    }

    pub fn __repr__(&self) -> String {
        format!("{:?}", self.inner.inner)
    }

    pub fn __richcmp__(&self, py: Python, rhs: Py_Entry_Mut, op: CompareOp) -> PyObject {
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
impl Py_Entry_Ref {
    pub fn __repr__(&self) -> PyResult<String> {
        self.inner.map_as_ref(|inner| format!("{:?}", inner))
    }

    pub fn __richcmp__(&self, py: Python, rhs: Py_Entry_Mut, op: CompareOp) -> PyResult<PyObject> {
        self.inner.map_as_ref(|inner| {
            let rhs: Entry = rhs.into();

            match op {
                CompareOp::Eq => (inner == &rhs).into_py(py),
                CompareOp::Ne => (inner != &rhs).into_py(py),
                _ => py.NotImplemented(),
            }
        })
    }

    pub fn clone(&self) -> PyResult<Py_Entry> {
        Ok(Py_Entry {
            inner: RefMutOwner::new(self.inner.map_as_ref(|x| x.clone())?),
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

#[pymethods]
impl Py_Entry_Ref {
    pub fn compute_size(&self) -> PyResult<u32> {
        self.inner.map_as_ref(|inner| inner.compute_size())
    }
}
