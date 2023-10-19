use crate::implement_type_conversion;
use crate::utils::{
    errors::to_pyresult,
    reference::{RefMutContainer, RefMutOwner},
    unsafe_cast::make_mut,
};
use prost::Message as ProstMessage;
use protobuf::Message as PbMessage;
use pyo3::types::PyDict;
use pyo3::{
    intern,
    prelude::*,
    pyclass::CompareOp,
    types::{PyBytes, PyList},
};
use raft::eraftpb::ConfChangeV2;

use super::{
    conf_change::PyConfChangeRef,
    conf_change_single::{PyConfChangeSingleMut, PyConfChangeSingleRef},
    conf_change_transition::PyConfChangeTransition,
};
use raft::derializer::format_confchangev2;

#[derive(Clone)]
#[pyclass(name = "ConfChangeV2")]
pub struct PyConfChangeV2 {
    pub inner: RefMutOwner<ConfChangeV2>,
}

#[derive(Clone)]
#[pyclass(name = "ConfChangeV2Ref")]
pub struct PyConfChangeV2Ref {
    pub inner: RefMutContainer<ConfChangeV2>,
}

#[derive(FromPyObject)]
pub enum PyConfChangeV2Mut<'p> {
    Owned(PyRefMut<'p, PyConfChangeV2>),
    RefMut(PyConfChangeV2Ref),
}

implement_type_conversion!(ConfChangeV2, PyConfChangeV2Mut);

#[pymethods]
impl PyConfChangeV2 {
    #[new]
    pub fn new() -> Self {
        PyConfChangeV2 {
            inner: RefMutOwner::new(ConfChangeV2::new()),
        }
    }

    #[staticmethod]
    pub fn default() -> Self {
        PyConfChangeV2 {
            inner: RefMutOwner::new(ConfChangeV2::default()),
        }
    }

    #[staticmethod]
    pub fn decode(v: &[u8]) -> PyResult<PyConfChangeV2> {
        Ok(PyConfChangeV2 {
            inner: RefMutOwner::new(to_pyresult(ProstMessage::decode(v))?),
        })
    }

    pub fn make_ref(&mut self) -> PyConfChangeV2Ref {
        PyConfChangeV2Ref {
            inner: RefMutContainer::new(&mut self.inner),
        }
    }

    pub fn __repr__(&self) -> String {
        format_confchangev2(&self.inner.inner)
    }

    pub fn __richcmp__(&self, py: Python, rhs: PyConfChangeV2Mut, op: CompareOp) -> PyObject {
        let rhs: ConfChangeV2 = rhs.into();

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

impl Default for PyConfChangeV2 {
    fn default() -> Self {
        Self::new()
    }
}

#[pymethods]
impl PyConfChangeV2Ref {
    pub fn __repr__(&self) -> PyResult<String> {
        self.inner.map_as_ref(|inner| format_confchangev2(inner))
    }

    pub fn __richcmp__(
        &self,
        py: Python,
        rhs: PyConfChangeV2Mut,
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

    pub fn to_dict(&mut self, py: Python) -> PyResult<PyObject> {
        let context = self.get_context(py)?;
        let transition: String = self.get_transition()?.__repr__();

        self.inner.map_as_ref(|inner| {
            let changes = inner
                .get_changes()
                .iter()
                .map(|cs| {
                    PyConfChangeSingleRef {
                        inner: RefMutContainer::new_raw(unsafe { make_mut(cs) }),
                    }
                    .to_dict(py)
                    .unwrap()
                })
                .collect::<Vec<_>>();
            let changes = PyList::new(py, changes);

            let res = PyDict::new(py);
            res.set_item("changes", changes).unwrap();
            res.set_item("context", context).unwrap();
            res.set_item("transition", transition).unwrap();
            res.into_py(py)
        })
    }

    pub fn clone(&self) -> PyResult<PyConfChangeV2> {
        Ok(PyConfChangeV2 {
            inner: RefMutOwner::new(self.inner.map_as_ref(|x| x.clone())?),
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
                .map(|cs| PyConfChangeSingleRef {
                    inner: RefMutContainer::new_raw(unsafe { make_mut(cs) }),
                })
                .collect::<Vec<_>>()
                .into_py(py)
        })
    }

    pub fn set_changes(&mut self, v: &PyList) -> PyResult<()> {
        self.inner.map_as_mut(|inner| {
            inner.set_changes(
                v.iter()
                    .map(|cs| cs.extract::<PyConfChangeSingleMut>().unwrap().into())
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

    pub fn get_transition(&self) -> PyResult<PyConfChangeTransition> {
        self.inner
            .map_as_ref(|inner| PyConfChangeTransition(inner.get_transition()))
    }

    pub fn set_transition(&mut self, v: &PyConfChangeTransition) -> PyResult<()> {
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
impl PyConfChangeV2Ref {
    pub fn as_v1(&mut self) -> PyResult<Option<PyConfChangeRef>> {
        self.inner.map_as_mut(|_inner| None)
    }

    // TODO: Apply COW to below method
    pub fn as_v2(&mut self) -> PyResult<PyConfChangeV2> {
        self.clone().unwrap().make_ref().into_v2()
    }

    pub fn into_v2(&mut self) -> PyResult<PyConfChangeV2> {
        self.inner.map_as_mut(|inner| PyConfChangeV2 {
            inner: RefMutOwner::new(inner.clone()),
        })
    }
}

#[pymethods]
impl PyConfChangeV2Ref {
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
