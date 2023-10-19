use prost::Message as ProstMessage;
use protobuf::Message as PbMessage;
use pyo3::{
    intern,
    prelude::*,
    pyclass::CompareOp,
    types::{PyBytes, PyList},
};

use crate::implement_type_conversion;
use crate::utils::{
    errors::to_pyresult,
    reference::{RefMutContainer, RefMutOwner},
    unsafe_cast::make_mut,
};
use raft::derializer::format_message;
use raft::eraftpb::Message;

use super::{
    entry::{PyEntryMut, PyEntryRef},
    message_type::PyMessageType,
    snapshot::{PySnapshotMut, PySnapshotRef},
};

#[derive(Clone)]
#[pyclass(name = "Message")]
pub struct PyMessage {
    pub inner: RefMutOwner<Message>,
}

#[derive(Clone)]
#[pyclass(name = "MessageRef")]
pub struct PyMessageRef {
    pub inner: RefMutContainer<Message>,
}

#[derive(FromPyObject)]
pub enum PyMessageMut<'p> {
    Owned(PyRefMut<'p, PyMessage>),
    RefMut(PyMessageRef),
}

implement_type_conversion!(Message, PyMessageMut);

#[pymethods]
impl PyMessage {
    #[new]
    pub fn new() -> Self {
        PyMessage {
            inner: RefMutOwner::new(Message::new()),
        }
    }

    #[staticmethod]
    pub fn default() -> Self {
        PyMessage {
            inner: RefMutOwner::new(Message::default()),
        }
    }

    #[staticmethod]
    pub fn decode(v: &[u8]) -> PyResult<PyMessage> {
        Ok(PyMessage {
            inner: RefMutOwner::new(to_pyresult(ProstMessage::decode(v))?),
        })
    }

    pub fn make_ref(&mut self) -> PyMessageRef {
        PyMessageRef {
            inner: RefMutContainer::new(&mut self.inner),
        }
    }

    pub fn __repr__(&self) -> String {
        format_message(&self.inner.inner)
    }

    pub fn __richcmp__(&self, py: Python, rhs: PyMessageMut, op: CompareOp) -> PyObject {
        let rhs: Message = rhs.into();

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

// TODO: Implement `to_dict` to this type.
#[pymethods]
impl PyMessageRef {
    pub fn __repr__(&self) -> PyResult<String> {
        self.inner.map_as_ref(|inner| format_message(inner))
    }

    pub fn __richcmp__(&self, py: Python, rhs: PyMessageMut, op: CompareOp) -> PyResult<PyObject> {
        self.inner.map_as_ref(|inner| {
            let rhs: Message = rhs.into();

            match op {
                CompareOp::Eq => (inner == &rhs).into_py(py),
                CompareOp::Ne => (inner != &rhs).into_py(py),
                _ => py.NotImplemented(),
            }
        })
    }

    pub fn clone(&self) -> PyResult<PyMessage> {
        Ok(PyMessage {
            inner: RefMutOwner::new(self.inner.map_as_ref(|x| x.clone())?),
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
                .map(|entry| PyEntryRef {
                    inner: RefMutContainer::new_raw(unsafe { make_mut(entry) }),
                })
                .collect::<Vec<_>>();

            entries.into_py(py)
        })
    }

    pub fn set_entries(&mut self, ents: &PyList) -> PyResult<()> {
        let mut entries: Vec<PyEntryMut> = ents.extract::<Vec<PyEntryMut>>()?;

        self.inner.map_as_mut(|inner| {
            let entries = entries.iter_mut().map(|x| x.into()).collect::<Vec<_>>();
            inner.set_entries(entries)
        })
    }

    pub fn clear_entries(&mut self) -> PyResult<()> {
        self.inner.map_as_mut(|inner| inner.clear_entries())
    }

    pub fn get_msg_type(&self) -> PyResult<PyMessageType> {
        self.inner
            .map_as_ref(|inner| PyMessageType(inner.get_msg_type()))
    }

    pub fn set_msg_type(&mut self, typ: &PyMessageType) -> PyResult<()> {
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

    pub fn get_snapshot(&mut self) -> PyResult<PySnapshotRef> {
        self.inner.map_as_mut(|inner| PySnapshotRef {
            inner: RefMutContainer::new_raw(inner.mut_snapshot()),
        })
    }

    pub fn set_snapshot(&mut self, snapshot: PySnapshotMut) -> PyResult<()> {
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

    #[warn(deprecated)]
    pub fn get_deprecated_priority(&self) -> PyResult<u64> {
        self.inner
            .map_as_ref(|inner| inner.get_deprecated_priority())
    }

    #[warn(deprecated)]
    pub fn set_deprecated_priority(&mut self, v: u64) -> PyResult<()> {
        self.inner
            .map_as_mut(|inner| inner.set_deprecated_priority(v))
    }
}

#[pymethods]
impl PyMessageRef {
    pub fn compute_size(&self) -> PyResult<u32> {
        self.inner.map_as_ref(|inner| inner.compute_size())
    }
}
