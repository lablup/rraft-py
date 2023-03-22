use pyo3::{exceptions::{{PyException, PyRuntimeError}}, prelude::*};

#[inline]
pub fn runtime_error(msg: &str) -> PyErr {
    PyException::new_err(msg.to_string())
}

#[inline]
pub fn to_pyresult<T, E: std::fmt::Display>(res: Result<T, E>) -> PyResult<T> {
    match res {
        Ok(x) => Ok(x),
        Err(err) => Err(PyRuntimeError::new_err(err.to_string())),
    }
}

#[inline]
pub fn destroyed_error() -> PyErr {
    runtime_error("Cannot use a destroyed object's reference!")
}
