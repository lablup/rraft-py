use bincode::deserialize;
use pyo3::*;

use crate::errors::to_pyresult;

#[pyfunction]
pub fn deserialize_u64(v: &[u8]) -> PyResult<u64> {
    to_pyresult(deserialize(v))
}

#[pyfunction]
pub fn deserialize_str(v: &[u8]) -> PyResult<String> {
    to_pyresult(deserialize(v))
}
