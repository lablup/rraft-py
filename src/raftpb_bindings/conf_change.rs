use prost::Message as ProstMessage;
use protobuf::Message as PbMessage;
use pyo3::{intern, prelude::*, pyclass::CompareOp, types::PyBytes};
use utils::{errors::to_pyresult, reference::RustRef};

use super::{conf_change_type::Py_ConfChangeType, conf_change_v2::Py_ConfChangeV2};

use raft::{
    eraftpb::ConfChange,
    prelude::{ConfChangeSingle, ConfChangeType, ConfChangeV2},
};

#[derive(Clone)]
#[pyclass(name = "ConfChange")]
pub struct Py_ConfChange {
    pub inner: ConfChange,
}

#[derive(Clone)]
#[pyclass(name = "ConfChange_Ref")]
pub struct Py_ConfChange_Ref {
    pub inner: RustRef<ConfChange>,
}

#[derive(FromPyObject)]
pub enum Py_ConfChange_Mut<'p> {
    Owned(PyRefMut<'p, Py_ConfChange>),
    RefMut(Py_ConfChange_Ref),
}

impl From<Py_ConfChange_Mut<'_>> for ConfChange {
    fn from(val: Py_ConfChange_Mut<'_>) -> Self {
        match val {
            Py_ConfChange_Mut::Owned(x) => x.inner.clone(),
            Py_ConfChange_Mut::RefMut(mut x) => x.inner.map_as_mut(|x| x.clone()).unwrap(),
        }
    }
}

impl From<&mut Py_ConfChange_Mut<'_>> for ConfChange {
    fn from(val: &mut Py_ConfChange_Mut<'_>) -> Self {
        match val {
            Py_ConfChange_Mut::Owned(x) => x.inner.clone(),
            Py_ConfChange_Mut::RefMut(x) => x.inner.map_as_mut(|x| x.clone()).unwrap(),
        }
    }
}

#[pymethods]
impl Py_ConfChange {
    #[new]
    pub fn new() -> Self {
        Py_ConfChange {
            inner: ConfChange::new(),
        }
    }

    #[staticmethod]
    pub fn default() -> Self {
        Py_ConfChange {
            inner: ConfChange::default(),
        }
    }

    #[staticmethod]
    pub fn decode(v: &[u8]) -> PyResult<Py_ConfChange> {
        Ok(Py_ConfChange {
            inner: to_pyresult(ProstMessage::decode(v))?,
        })
    }

    pub fn make_ref(&mut self) -> Py_ConfChange_Ref {
        Py_ConfChange_Ref {
            inner: RustRef::new(&mut self.inner),
        }
    }

    pub fn __repr__(&self) -> String {
        format!("{:?}", self.inner)
    }

    pub fn __richcmp__(&self, py: Python<'_>, rhs: Py_ConfChange_Mut, op: CompareOp) -> PyObject {
        let rhs: ConfChange = rhs.into();

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
impl Py_ConfChange_Ref {
    pub fn __repr__(&self) -> PyResult<String> {
        self.inner.map_as_ref(|inner| format!("{:?}", inner))
    }

    pub fn __richcmp__(
        &self,
        py: Python<'_>,
        rhs: Py_ConfChange_Mut,
        op: CompareOp,
    ) -> PyResult<PyObject> {
        self.inner.map_as_ref(|inner| {
            let rhs: ConfChange = rhs.into();

            match op {
                CompareOp::Eq => (inner == &rhs).into_py(py),
                CompareOp::Ne => (inner != &rhs).into_py(py),
                _ => py.NotImplemented(),
            }
        })
    }

    pub fn clone(&mut self) -> PyResult<Py_ConfChange> {
        Ok(Py_ConfChange {
            inner: self.inner.map_as_ref(|inner| inner.clone())?,
        })
    }

    pub fn encode(&self, py: Python) -> PyResult<PyObject> {
        self.inner
            .map_as_ref(|inner| PyBytes::new(py, inner.encode_to_vec().as_slice()).into_py(py))
    }

    pub fn get_id(&self) -> PyResult<u64> {
        self.inner.map_as_ref(|inner| inner.get_id())
    }

    pub fn set_id(&mut self, v: u64) -> PyResult<()> {
        self.inner.map_as_mut(|inner| inner.set_id(v))
    }

    pub fn clear_id(&mut self) -> PyResult<()> {
        self.inner.map_as_mut(|inner| inner.clear_id())
    }

    pub fn get_node_id(&self) -> PyResult<u64> {
        self.inner.map_as_ref(|inner| inner.get_node_id())
    }

    pub fn set_node_id(&mut self, v: u64) -> PyResult<()> {
        self.inner.map_as_mut(|inner| inner.set_node_id(v))
    }

    pub fn clear_node_id(&mut self) -> PyResult<()> {
        self.inner.map_as_mut(|inner| inner.clear_node_id())
    }

    pub fn get_change_type(&self) -> PyResult<Py_ConfChangeType> {
        self.inner
            .map_as_ref(|inner| inner.get_change_type().into())
    }

    pub fn set_change_type(&mut self, v: &Py_ConfChangeType) -> PyResult<()> {
        self.inner.map_as_mut(|inner| inner.set_change_type(v.0))
    }

    pub fn clear_change_type(&mut self) -> PyResult<()> {
        self.inner.map_as_mut(|inner| inner.clear_change_type())
    }

    pub fn get_context(&self, py: Python) -> PyResult<Py<PyBytes>> {
        self.inner
            .map_as_ref(|inner| PyBytes::new(py, inner.get_context()).into())
    }

    pub fn set_context(&mut self, v: &PyAny) -> PyResult<()> {
        let context = v.extract::<Vec<u8>>()?;
        self.inner.map_as_mut(|inner| inner.set_context(context))
    }

    pub fn clear_context(&mut self) -> PyResult<()> {
        self.inner.map_as_mut(|inner| inner.clear_context())
    }
}

#[pymethods]
impl Py_ConfChange_Ref {
    // This function could be implemented in Python by using `Decode`
    // and set properties one by one manually, but it is implemented here
    // to maintain concise code and assist in achieving better performance.
    pub fn merge_from_bytes(&mut self, bytes: &PyAny) -> PyResult<()> {
        let bytes = bytes.extract::<Vec<u8>>()?;

        self.inner
            .map_as_mut(|inner| inner.merge_from_bytes(bytes.as_slice()))
            .and_then(to_pyresult)
    }
}

#[pymethods]
impl Py_ConfChange_Ref {
    pub fn as_v1(&mut self) -> PyResult<Option<Py_ConfChange_Ref>> {
        self.inner.map_as_mut(|inner| {
            Some(Py_ConfChange_Ref {
                inner: RustRef::new(inner),
            })
        })
    }

    // TODO: Apply COW to below method
    pub fn as_v2(&mut self) -> PyResult<Py_ConfChangeV2> {
        self.clone().unwrap().make_ref().into_v2()
    }

    pub fn into_v2(&mut self) -> PyResult<Py_ConfChangeV2> {
        self.inner.map_as_mut(|inner| {
            let mut cc = ConfChangeV2::default();
            let single = new_conf_change_single(inner.node_id, inner.get_change_type());
            cc.mut_changes().push(single);
            cc.set_context(inner.take_context());

            Py_ConfChangeV2 { inner: cc }
        })
    }
}

/// Creates a `ConfChangeSingle`.
pub fn new_conf_change_single(node_id: u64, typ: ConfChangeType) -> ConfChangeSingle {
    let mut single = ConfChangeSingle {
        node_id,
        ..Default::default()
    };
    single.set_change_type(typ);
    single
}
