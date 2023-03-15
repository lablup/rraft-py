use pyo3::{prelude::*, pyclass::CompareOp, types::PyList};
use utils::reference::RustRef;

use super::{conf_change_type::Py_ConfChangeType, conf_change_v2::Py_ConfChangeV2_Owner};

use raft::{
    eraftpb::ConfChange,
    prelude::{ConfChangeSingle, ConfChangeType, ConfChangeV2},
};

#[derive(Clone)]
#[pyclass(name = "ConfChange_Owner")]
pub struct Py_ConfChange_Owner {
    pub inner: ConfChange,
}

#[derive(Clone)]
#[pyclass(name = "ConfChange_Ref")]
pub struct Py_ConfChange_Ref {
    pub inner: RustRef<ConfChange>,
}

#[derive(FromPyObject)]
pub enum Py_ConfChange_Mut<'p> {
    Owned(PyRefMut<'p, Py_ConfChange_Owner>),
    RefMut(Py_ConfChange_Ref),
}

impl Into<ConfChange> for Py_ConfChange_Mut<'_> {
    fn into(self) -> ConfChange {
        match self {
            Py_ConfChange_Mut::Owned(x) => x.inner.clone(),
            Py_ConfChange_Mut::RefMut(mut x) => x.inner.map_as_mut(|x| x.clone()).unwrap(),
        }
    }
}

impl Into<ConfChange> for &mut Py_ConfChange_Mut<'_> {
    fn into(self) -> ConfChange {
        match self {
            Py_ConfChange_Mut::Owned(x) => x.inner.clone(),
            Py_ConfChange_Mut::RefMut(x) => x.inner.map_as_mut(|x| x.clone()).unwrap(),
        }
    }
}

#[pymethods]
impl Py_ConfChange_Owner {
    #[new]
    pub fn new() -> Self {
        Py_ConfChange_Owner {
            inner: ConfChange::new_(),
        }
    }

    #[staticmethod]
    pub fn default() -> Self {
        Py_ConfChange_Owner {
            inner: ConfChange::default(),
        }
    }

    pub fn make_ref(&mut self) -> Py_ConfChange_Ref {
        Py_ConfChange_Ref {
            inner: RustRef::new(&mut self.inner),
        }
    }

    pub fn clone(&self) -> Py_ConfChange_Owner {
        Py_ConfChange_Owner {
            inner: self.inner.clone(),
        }
    }

    pub fn __repr__(&self) -> String {
        format!("{:?}", self.inner)
    }

    pub fn __richcmp__(&self, rhs: Py_ConfChange_Mut, op: CompareOp) -> bool {
        let rhs: ConfChange = rhs.into();

        match op {
            CompareOp::Eq => self.inner == rhs,
            CompareOp::Ne => self.inner != rhs,
            _ => panic!("Undefined operator"),
        }
    }
}

#[pymethods]
impl Py_ConfChange_Ref {
    pub fn __repr__(&self) -> PyResult<String> {
        self.inner.map_as_ref(|inner| format!("{:?}", inner))
    }

    pub fn __richcmp__(&self, rhs: Py_ConfChange_Mut, op: CompareOp) -> PyResult<bool> {
        self.inner.map_as_ref(|inner| {
            let rhs: ConfChange = rhs.into();

            match op {
                CompareOp::Eq => inner == &rhs,
                CompareOp::Ne => inner != &rhs,
                _ => panic!("Undefined operator"),
            }
        })
    }

    pub fn clone(&mut self) -> Py_ConfChange_Owner {
        Py_ConfChange_Owner {
            inner: self.inner.map_as_ref(|inner| inner.clone()).unwrap(),
        }
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

    pub fn get_context(&self, py: Python) -> PyResult<Py<PyList>> {
        self.inner
            .map_as_ref(|inner| PyList::new(py, inner.get_context()).into())
    }

    pub fn set_context(&mut self, context: &PyList) -> PyResult<()> {
        self.inner.map_as_mut(|inner| {
            inner.set_context(context.extract::<Vec<u8>>().unwrap());
        })
    }

    pub fn clear_context(&mut self) -> PyResult<()> {
        self.inner.map_as_mut(|inner| inner.clear_context())
    }

    pub fn into_v2(&mut self) -> PyResult<Py_ConfChangeV2_Owner> {
        self.inner.map_as_mut(|inner| {
            let mut cc = ConfChangeV2::default();
            let single = new_conf_change_single(inner.node_id, inner.get_change_type());
            cc.mut_changes().push(single);
            cc.set_context(inner.take_context());

            Py_ConfChangeV2_Owner { inner: cc }
        })
    }
}

/// Creates a `ConfChangeSingle`.
fn new_conf_change_single(node_id: u64, typ: ConfChangeType) -> ConfChangeSingle {
    let mut single = ConfChangeSingle::default();
    single.node_id = node_id;
    single.set_change_type(typ);
    single
}
