use pyo3::prelude::*;

use std::sync::{Arc, Mutex};

#[derive(Clone)]
#[pyclass(name = "Mutex")]
pub struct PyMutex {
    pub inner: Arc<Mutex<u64>>,
}

impl PyMutex {
    #[tokio::main]
    pub async fn acquire_lock_and<T>(&self, cb: impl FnOnce() -> PyResult<T>) -> PyResult<T> {
        let mut guard = self.inner.lock().unwrap();

        // Wait until the guard's int value becomes 0.
        while *guard != 0 {
            tokio::task::yield_now().await;
            guard = self.inner.lock().unwrap();
        }

        *guard += 1;
        // The guard will be dropped when after cb executed.
        let res = cb();
        *guard -= 1;
        res
    }
}

#[pymethods]
impl PyMutex {
    #[new]
    pub fn new() -> Self {
        Self {
            inner: Arc::new(Mutex::new(0)),
        }
    }

    pub fn clone(&self) -> Self {
        Self {
            inner: Arc::clone(&self.inner),
        }
    }

    pub fn incr(&self) -> PyResult<()> {
        let mut guard = self.inner.lock().unwrap();
        *guard += 1;
        Ok(())
    }

    pub fn decr(&self) -> PyResult<()> {
        let mut guard = self.inner.lock().unwrap();
        *guard -= 1;
        Ok(())
    }

    #[pyo3(name = "acquire_lock_and")]
    pub fn py_acquire_lock_and(&self, cb: PyObject, py: Python) -> PyResult<PyObject> {
        self.acquire_lock_and(|| cb.call(py, (), None))
    }
}
