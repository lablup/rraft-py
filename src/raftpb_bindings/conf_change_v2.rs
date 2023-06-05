use prost::Message as ProstMessage;
use protobuf::Message as PbMessage;
use pyo3::{
    intern,
    prelude::*,
    pyclass::CompareOp,
    types::{PyBytes, PyList},
};
use raft::eraftpb::ConfChangeV2;
use utils::{errors::to_pyresult, reference::RustRef, unsafe_cast::make_mut};

use super::{
    conf_change::Py_ConfChange_Ref,
    conf_change_single::{Py_ConfChangeSingle_Mut, Py_ConfChangeSingle_Ref},
    conf_change_transition::Py_ConfChangeTransition,
};

#[derive(Clone)]
#[pyclass(name = "ConfChangeV2")]
pub struct Py_ConfChangeV2 {
    pub inner: ConfChangeV2,
}

#[derive(Clone)]
#[pyclass(name = "ConfChangeV2_Ref")]
pub struct Py_ConfChangeV2_Ref {
    pub inner: RustRef<ConfChangeV2>,
}

#[derive(FromPyObject)]
pub enum Py_ConfChangeV2_Mut<'p> {
    Owned(PyRefMut<'p, Py_ConfChangeV2>),
    RefMut(Py_ConfChangeV2_Ref),
}

impl From<Py_ConfChangeV2_Mut<'_>> for ConfChangeV2 {
    fn from(val: Py_ConfChangeV2_Mut<'_>) -> Self {
        match val {
            Py_ConfChangeV2_Mut::Owned(x) => x.inner.clone(),
            Py_ConfChangeV2_Mut::RefMut(mut x) => x.inner.map_as_mut(|x| x.clone()).unwrap(),
        }
    }
}

impl From<&mut Py_ConfChangeV2_Mut<'_>> for ConfChangeV2 {
    fn from(val: &mut Py_ConfChangeV2_Mut<'_>) -> Self {
        match val {
            Py_ConfChangeV2_Mut::Owned(x) => x.inner.clone(),
            Py_ConfChangeV2_Mut::RefMut(x) => x.inner.map_as_mut(|x| x.clone()).unwrap(),
        }
    }
}

#[pymethods]
impl Py_ConfChangeV2 {
    #[new]
    pub fn new() -> Self {
        Py_ConfChangeV2 {
            inner: ConfChangeV2::new(),
        }
    }

    #[staticmethod]
    pub fn default() -> Self {
        Py_ConfChangeV2 {
            inner: ConfChangeV2::default(),
        }
    }

    #[staticmethod]
    pub fn decode(v: &[u8]) -> PyResult<Py_ConfChangeV2> {
        Ok(Py_ConfChangeV2 {
            inner: to_pyresult(ProstMessage::decode(v))?,
        })
    }

    pub fn make_ref(&mut self) -> Py_ConfChangeV2_Ref {
        Py_ConfChangeV2_Ref {
            inner: RustRef::new(&mut self.inner),
        }
    }

    pub fn __repr__(&self) -> String {
        format!("{:?}", self.inner)
    }

    pub fn __richcmp__(&self, py: Python, rhs: Py_ConfChangeV2_Mut, op: CompareOp) -> PyObject {
        let rhs: ConfChangeV2 = rhs.into();

        match op {
            CompareOp::Eq => (self.inner == rhs).into_py(py),
            CompareOp::Ne => (self.inner != rhs).into_py(py),
            _ => py.NotImplemented(),
        }
    }

    fn __getattr__(this: PyObject, py: Python, attr: &str) -> PyResult<PyObject> {
        let reference = this.call_method0(py, intern!(py, "make_ref"))?;
        reference.getattr(py, attr)
    }
}

impl Default for Py_ConfChangeV2 {
    fn default() -> Self {
        Self::new()
    }
}

#[pymethods]
impl Py_ConfChangeV2_Ref {
    pub fn __repr__(&self) -> PyResult<String> {
        self.inner.map_as_ref(|inner| format!("{:?}", inner))
    }

    pub fn __richcmp__(
        &self,
        py: Python,
        rhs: Py_ConfChangeV2_Mut,
        op: CompareOp,
    ) -> PyResult<PyObject> {
        self.inner.map_as_ref(|inner| {
            let rhs: ConfChangeV2 = rhs.into();

            match op {
                CompareOp::Eq => (inner == &rhs).into_py(py),
                CompareOp::Ne => (inner != &rhs).into_py(py),
                _ => py.NotImplemented(),
            }
        })
    }

    pub fn clone(&self) -> PyResult<Py_ConfChangeV2> {
        Ok(Py_ConfChangeV2 {
            inner: self.inner.map_as_ref(|x| x.clone())?,
        })
    }

    pub fn encode(&self, py: Python) -> PyResult<PyObject> {
        self.inner
            .map_as_ref(|inner| PyBytes::new(py, inner.encode_to_vec().as_slice()).into_py(py))
    }

    pub fn get_changes(&self, py: Python) -> PyResult<PyObject> {
        self.inner.map_as_ref(|inner| {
            inner
                .get_changes()
                .iter()
                .map(|cs| Py_ConfChangeSingle_Ref {
                    inner: RustRef::new(unsafe { make_mut(cs) }),
                })
                .collect::<Vec<_>>()
                .into_py(py)
        })
    }

    pub fn set_changes(&mut self, v: &PyList) -> PyResult<()> {
        self.inner.map_as_mut(|inner| {
            inner.set_changes(
                v.iter()
                    .map(|cs| cs.extract::<Py_ConfChangeSingle_Mut>().unwrap().into())
                    .collect::<Vec<_>>(),
            )
        })
    }

    pub fn clear_changes(&mut self) -> PyResult<()> {
        self.inner.map_as_mut(|inner| inner.clear_changes())
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

    pub fn get_transition(&self) -> PyResult<Py_ConfChangeTransition> {
        self.inner
            .map_as_ref(|inner| Py_ConfChangeTransition(inner.get_transition()))
    }

    pub fn set_transition(&mut self, v: &Py_ConfChangeTransition) -> PyResult<()> {
        self.inner.map_as_mut(|inner| inner.set_transition(v.0))
    }

    pub fn clear_transition(&mut self) -> PyResult<()> {
        self.inner.map_as_mut(|inner| inner.clear_transition())
    }

    pub fn enter_joint(&self) -> PyResult<Option<bool>> {
        self.inner.map_as_ref(|inner| inner.enter_joint())
    }

    pub fn leave_joint(&self) -> PyResult<bool> {
        self.inner.map_as_ref(|inner| inner.leave_joint())
    }
}

#[pymethods]
impl Py_ConfChangeV2_Ref {
    pub fn as_v1(&mut self) -> PyResult<Option<Py_ConfChange_Ref>> {
        self.inner.map_as_mut(|_inner| None)
    }

    // TODO: Apply COW to below method
    pub fn as_v2(&mut self) -> PyResult<Py_ConfChangeV2> {
        self.clone().unwrap().make_ref().into_v2()
    }

    pub fn into_v2(&mut self) -> PyResult<Py_ConfChangeV2> {
        self.inner.map_as_mut(|inner| Py_ConfChangeV2 {
            inner: inner.clone(),
        })
    }
}

#[pymethods]
impl Py_ConfChangeV2_Ref {
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
