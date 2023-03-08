use pyo3::{prelude::*, AsPyPointer};

use raft::{SoftState, Status};

use crate::eraftpb::hard_state::{Py_HardState_Mut, Py_HardState_Ref};

use utils::{
    reference::RustRef,
    uncloneable_reference::{UncloneableRustRef, UncloneableRustRef_Default_Implementation},
    unsafe_cast::{make_mut, make_static, make_static_mut},
};

use super::{
    progress_tracker::{Py_ProgressTracker_Mut, Py_ProgressTracker_Ref},
    raft::Py_Raft__MemStorage_Owner,
    soft_state::{Py_SoftState_Owner, Py_SoftState_Ref},
};

#[pyclass(name = "Status__MemStorage_Owner")]
pub struct Py_Status__MemStorage_Owner {
    pub inner: Status<'static>,
    pub raft_handle: Py<Py_Raft__MemStorage_Owner>,
}

#[pyclass(name = "Status__MemStorage_Ref")]
pub struct Py_Status__MemStorage_Ref {
    pub inner: UncloneableRustRef<Status<'static>>,
}

#[pymethods]
impl Py_Status__MemStorage_Owner {
    #[staticmethod]
    pub fn new(
        pyraft_ref: Py<Py_Raft__MemStorage_Owner>,
        py: Python,
    ) -> Py_Status__MemStorage_Owner {
        let pyraft = unsafe {
            pyo3::ffi::Py_INCREF(pyraft_ref.as_ptr());
            make_static_mut(&*(pyraft_ref.borrow(py)))
        };

        Py_Status__MemStorage_Owner {
            inner: Status::new(&pyraft.inner),
            raft_handle: pyraft_ref,
        }
    }

    pub fn make_ref(&mut self) -> Py_Status__MemStorage_Ref {
        Py_Status__MemStorage_Ref {
            inner: UncloneableRustRef::new(&mut self.inner),
        }
    }
}

#[pymethods]
impl Py_Status__MemStorage_Ref {
    pub fn __repr__(&self) -> PyResult<String> {
        self.inner.map_as_ref(|inner| {
            format!(
                "Status {{ \
                    id: {:?}, \
                    hs: {:?}, \
                    ss: {:?}, \
                    applied: {:?} \
                }}",
                inner.id, inner.hs, inner.ss, inner.applied,
            )
        })
    }

    pub fn get_applied(&self) -> PyResult<u64> {
        self.inner.map_as_ref(|inner| inner.applied)
    }

    pub fn set_applied(&mut self, applied: u64) -> PyResult<()> {
        self.inner.map_as_mut(|inner| inner.applied = applied)
    }

    pub fn get_id(&self) -> PyResult<u64> {
        self.inner.map_as_ref(|inner| inner.id)
    }

    pub fn set_id(&mut self, id: u64) -> PyResult<()> {
        self.inner.map_as_mut(|inner| inner.id = id)
    }

    pub fn get_hs(&mut self) -> PyResult<Py_HardState_Ref> {
        self.inner.map_as_mut(|inner| Py_HardState_Ref {
            inner: RustRef::new(&mut inner.hs),
        })
    }

    pub fn set_hs(&mut self, hs: Py_HardState_Mut) -> PyResult<()> {
        self.inner.map_as_mut(|inner| inner.hs = hs.into())
    }

    pub fn get_ss(&mut self) -> PyResult<Py_SoftState_Ref> {
        self.inner.map_as_mut(|inner| Py_SoftState_Ref {
            inner: UncloneableRustRef::new(unsafe { make_mut(&inner.ss) }),
        })
    }

    /// WARNING: This function replace rd with default SoftState.
    pub fn set_ss(&mut self, ss: &mut Py_SoftState_Ref) -> PyResult<()> {
        let ss = ss
            .inner
            .map_as_mut(|ss| std::mem::replace(ss, SoftState::default()))
            .unwrap();

        self.inner.map_as_mut(|inner| inner.ss = ss)
    }

    pub fn get_progress(&mut self) -> PyResult<Option<Py_ProgressTracker_Ref>> {
        self.inner.map_as_mut(|inner| match inner.progress {
            Some(p) => Some(Py_ProgressTracker_Ref {
                inner: RustRef::new(unsafe { make_mut(p) }),
            }),
            None => None,
        })
    }

    pub fn set_progress(&mut self, tracker: Py_ProgressTracker_Mut) -> PyResult<()> {
        self.inner.map_as_mut(|inner| {
            inner.progress = Some(unsafe { make_static(&tracker.into()) });
        })
    }
}

impl Drop for Py_Status__MemStorage_Owner {
    fn drop(&mut self) {
        unsafe { pyo3::ffi::Py_DECREF(self.raft_handle.to_owned().as_ptr()) }
    }
}
