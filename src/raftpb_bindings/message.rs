use prost::Message as ProstMessage;
use protobuf::Message as PbMessage;
use pyo3::{
    intern,
    prelude::*,
    pyclass::CompareOp,
    types::{PyBytes, PyList},
};

use raft::eraftpb::Message;
use utils::{errors::to_pyresult, unsafe_cast::make_mut};

use utils::reference::RustRef;

use super::{
    entry::{Py_Entry_Mut, Py_Entry_Ref},
    message_type::Py_MessageType,
    snapshot::{Py_Snapshot_Mut, Py_Snapshot_Ref},
};

#[derive(Clone)]
#[pyclass(name = "Message")]
pub struct Py_Message {
    pub inner: Message,
}

#[derive(Clone)]
#[pyclass(name = "Message_Ref")]
pub struct Py_Message_Ref {
    pub inner: RustRef<Message>,
}

#[derive(FromPyObject)]
pub enum Py_Message_Mut<'p> {
    Owned(PyRefMut<'p, Py_Message>),
    RefMut(Py_Message_Ref),
}

impl From<Py_Message_Mut<'_>> for Message {
    fn from(val: Py_Message_Mut<'_>) -> Self {
        match val {
            Py_Message_Mut::Owned(x) => x.inner.clone(),
            Py_Message_Mut::RefMut(mut x) => x.inner.map_as_mut(|x| x.clone()).unwrap(),
        }
    }
}

impl From<&mut Py_Message_Mut<'_>> for Message {
    fn from(val: &mut Py_Message_Mut<'_>) -> Self {
        match val {
            Py_Message_Mut::Owned(x) => x.inner.clone(),
            Py_Message_Mut::RefMut(x) => x.inner.map_as_mut(|x| x.clone()).unwrap(),
        }
    }
}

#[pymethods]
impl Py_Message {
    #[new]
    pub fn new() -> Self {
        Py_Message {
            inner: Message::new(),
        }
    }

    #[staticmethod]
    pub fn default() -> Self {
        Py_Message {
            inner: Message::default(),
        }
    }

    #[staticmethod]
    pub fn decode(v: &[u8]) -> PyResult<Py_Message> {
        Ok(Py_Message {
            inner: to_pyresult(ProstMessage::decode(v))?,
        })
    }

    pub fn make_ref(&mut self) -> Py_Message_Ref {
        Py_Message_Ref {
            inner: RustRef::new(&mut self.inner),
        }
    }

    pub fn __repr__(&self) -> String {
        format!("{:?}", self.inner)
    }

    pub fn __richcmp__(&self, py: Python<'_>, rhs: Py_Message_Mut, op: CompareOp) -> PyObject {
        let rhs: Message = rhs.into();

        match op {
            CompareOp::Eq => (self.inner == rhs).into_py(py),
            CompareOp::Ne => (self.inner != rhs).into_py(py),
            _ => py.NotImplemented(),
        }
    }

    fn __getattr__(this: PyObject, py: Python<'_>, attr: &str) -> PyResult<PyObject> {
        let reference = this.call_method0(py, intern!(py, "make_ref"))?;
        reference.getattr(py, attr)
    }
}

#[pymethods]
impl Py_Message_Ref {
    pub fn __repr__(&self) -> PyResult<String> {
        self.inner.map_as_ref(|inner| format!("{:?}", inner))
    }

    pub fn __richcmp__(
        &self,
        py: Python<'_>,
        rhs: Py_Message_Mut,
        op: CompareOp,
    ) -> PyResult<PyObject> {
        self.inner.map_as_ref(|inner| {
            let rhs: Message = rhs.into();

            match op {
                CompareOp::Eq => (inner == &rhs).into_py(py),
                CompareOp::Ne => (inner != &rhs).into_py(py),
                _ => py.NotImplemented(),
            }
        })
    }

    pub fn clone(&self) -> PyResult<Py_Message> {
        Ok(Py_Message {
            inner: self.inner.map_as_ref(|x| x.clone())?,
        })
    }

    pub fn encode(&self, py: Python) -> PyResult<PyObject> {
        self.inner
            .map_as_ref(|inner| PyBytes::new(py, inner.encode_to_vec().as_slice()).into_py(py))
    }

    pub fn get_commit(&self) -> PyResult<u64> {
        self.inner.map_as_ref(|inner| inner.get_commit())
    }

    pub fn set_commit(&mut self, v: u64) -> PyResult<()> {
        self.inner.map_as_mut(|inner| inner.set_commit(v))
    }

    pub fn clear_commit(&mut self) -> PyResult<()> {
        self.inner.map_as_mut(|inner| inner.clear_commit())
    }

    pub fn get_commit_term(&self) -> PyResult<u64> {
        self.inner.map_as_ref(|inner| inner.get_commit_term())
    }

    pub fn set_commit_term(&mut self, v: u64) -> PyResult<()> {
        self.inner.map_as_mut(|inner| inner.set_commit_term(v))
    }

    pub fn clear_commit_term(&mut self) -> PyResult<()> {
        self.inner.map_as_mut(|inner| inner.clear_commit_term())
    }

    pub fn get_from(&self) -> PyResult<u64> {
        self.inner.map_as_ref(|inner| inner.get_from())
    }

    pub fn set_from(&mut self, v: u64) -> PyResult<()> {
        self.inner.map_as_mut(|inner| inner.set_from(v))
    }

    pub fn clear_from(&mut self) -> PyResult<()> {
        self.inner.map_as_mut(|inner| inner.clear_from())
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

    pub fn get_term(&self) -> PyResult<u64> {
        self.inner.map_as_ref(|inner| inner.get_term())
    }

    pub fn set_term(&mut self, v: u64) -> PyResult<()> {
        self.inner.map_as_mut(|inner| inner.set_term(v))
    }

    pub fn clear_term(&mut self) -> PyResult<()> {
        self.inner.map_as_mut(|inner| inner.clear_term())
    }

    pub fn get_log_term(&self) -> PyResult<u64> {
        self.inner.map_as_ref(|inner| inner.get_log_term())
    }

    pub fn set_log_term(&mut self, v: u64) -> PyResult<()> {
        self.inner.map_as_mut(|inner| inner.set_log_term(v))
    }

    pub fn clear_log_term(&mut self) -> PyResult<()> {
        self.inner.map_as_mut(|inner| inner.clear_log_term())
    }

    pub fn get_priority(&self) -> PyResult<i64> {
        self.inner.map_as_ref(|inner| inner.get_priority())
    }

    pub fn set_priority(&mut self, v: i64) -> PyResult<()> {
        self.inner.map_as_mut(|inner| inner.set_priority(v))
    }

    pub fn clear_priority(&mut self) -> PyResult<()> {
        self.inner.map_as_mut(|inner| inner.clear_priority())
    }

    pub fn get_context(&self, py: Python) -> PyResult<Py<PyBytes>> {
        self.inner
            .map_as_ref(|inner| PyBytes::new(py, inner.get_context()).into())
    }

    pub fn set_context(&mut self, context: &PyAny) -> PyResult<()> {
        let v = context.extract::<Vec<u8>>()?;
        self.inner.map_as_mut(|inner| inner.set_context(v))
    }

    pub fn clear_context(&mut self) -> PyResult<()> {
        self.inner.map_as_mut(|inner| inner.clear_context())
    }

    pub fn get_reject_hint(&self) -> PyResult<u64> {
        self.inner.map_as_ref(|inner| inner.get_reject_hint())
    }

    pub fn set_reject_hint(&mut self, v: u64) -> PyResult<()> {
        self.inner.map_as_mut(|inner| inner.set_reject_hint(v))
    }

    pub fn clear_reject_hint(&mut self) -> PyResult<()> {
        self.inner.map_as_mut(|inner| inner.clear_reject_hint())
    }

    pub fn get_entries(&self, py: Python) -> PyResult<PyObject> {
        self.inner.map_as_ref(|inner| {
            let entries = inner
                .get_entries()
                .iter()
                .map(|entry| Py_Entry_Ref {
                    inner: RustRef::new(unsafe { make_mut(entry) }),
                })
                .collect::<Vec<_>>();

            entries.into_py(py)
        })
    }

    pub fn set_entries(&mut self, ents: &PyList) -> PyResult<()> {
        self.inner.map_as_mut(|inner| {
            let entries = ents
                .extract::<Vec<Py_Entry_Mut>>()
                .unwrap()
                .iter_mut()
                .map(|x| x.into())
                .collect::<Vec<_>>();

            inner.set_entries(entries)
        })
    }

    pub fn clear_entries(&mut self) -> PyResult<()> {
        self.inner.map_as_mut(|inner| inner.clear_entries())
    }

    pub fn get_msg_type(&self) -> PyResult<Py_MessageType> {
        self.inner
            .map_as_ref(|inner| Py_MessageType(inner.get_msg_type()))
    }

    pub fn set_msg_type(&mut self, typ: &Py_MessageType) -> PyResult<()> {
        self.inner.map_as_mut(|inner| inner.set_msg_type(typ.0))
    }

    pub fn clear_msg_type(&mut self) -> PyResult<()> {
        self.inner.map_as_mut(|inner| inner.clear_msg_type())
    }

    pub fn get_reject(&self) -> PyResult<bool> {
        self.inner.map_as_ref(|inner| inner.get_reject())
    }

    pub fn set_reject(&mut self, v: bool) -> PyResult<()> {
        self.inner.map_as_mut(|inner| inner.set_reject(v))
    }

    pub fn clear_reject(&mut self) -> PyResult<()> {
        self.inner.map_as_mut(|inner| inner.clear_reject())
    }

    pub fn get_snapshot(&mut self) -> PyResult<Py_Snapshot_Ref> {
        self.inner.map_as_mut(|inner| Py_Snapshot_Ref {
            inner: RustRef::new(inner.mut_snapshot()),
        })
    }

    pub fn set_snapshot(&mut self, snapshot: Py_Snapshot_Mut) -> PyResult<()> {
        self.inner
            .map_as_mut(|inner| inner.set_snapshot(snapshot.into()))
    }

    pub fn clear_snapshot(&mut self) -> PyResult<()> {
        self.inner.map_as_mut(|inner| inner.clear_snapshot())
    }

    pub fn get_to(&self) -> PyResult<u64> {
        self.inner.map_as_ref(|inner| inner.get_to())
    }

    pub fn set_to(&mut self, v: u64) -> PyResult<()> {
        self.inner.map_as_mut(|inner| inner.set_to(v))
    }

    pub fn clear_to(&mut self) -> PyResult<()> {
        self.inner.map_as_mut(|inner| inner.clear_to())
    }

    pub fn get_request_snapshot(&self) -> PyResult<u64> {
        self.inner.map_as_ref(|inner| inner.get_request_snapshot())
    }

    pub fn set_request_snapshot(&mut self, v: u64) -> PyResult<()> {
        self.inner.map_as_mut(|inner| inner.set_request_snapshot(v))
    }

    pub fn clear_request_snapshot(&mut self) -> PyResult<()> {
        self.inner
            .map_as_mut(|inner| inner.clear_request_snapshot())
    }

    pub fn has_snapshot(&self) -> PyResult<bool> {
        self.inner.map_as_ref(|inner| inner.has_snapshot())
    }
}

#[pymethods]
impl Py_Message_Ref {
    pub fn compute_size(&self) -> PyResult<u32> {
        self.inner.map_as_ref(|inner| inner.compute_size())
    }
}
