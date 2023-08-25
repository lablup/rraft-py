use std::sync::Mutex;

use ::once_cell::sync::Lazy;
use pyo3::*;
use pyo3::{types::PyBytes, IntoPy, PyObject, Python};
use raft::derializer::{Bytes, CustomDeserializer};
pub struct MyDeserializer;

// TODO: Refactor below codes to reduce code redundancy.
static ENTRY_CONTEXT_DESERIALIZE_CB: Lazy<Mutex<Option<PyObject>>> = Lazy::new(|| Mutex::new(None));
static ENTRY_DATA_DESERIALIZE_CB: Lazy<Mutex<Option<PyObject>>> = Lazy::new(|| Mutex::new(None));
static CONFCHANGEV2_CONTEXT_DESERIALIZE_CB: Lazy<Mutex<Option<PyObject>>> =
    Lazy::new(|| Mutex::new(None));
static CONFCHANGE_CONTEXT_DESERIALIZE_CB: Lazy<Mutex<Option<PyObject>>> =
    Lazy::new(|| Mutex::new(None));
static MESSAGE_CONTEXT_DESERIALIZER_CB: Lazy<Mutex<Option<PyObject>>> =
    Lazy::new(|| Mutex::new(None));
static SNAPSHOT_DATA_DESERIALIZER_CB: Lazy<Mutex<Option<PyObject>>> =
    Lazy::new(|| Mutex::new(None));

#[pyfunction]
pub fn set_entry_context_deserializer(cb: PyObject) {
    *ENTRY_CONTEXT_DESERIALIZE_CB.lock().unwrap() = Some(cb);
}

#[pyfunction]
pub fn set_entry_data_deserializer(cb: PyObject) {
    *ENTRY_DATA_DESERIALIZE_CB.lock().unwrap() = Some(cb);
}

#[pyfunction]
pub fn set_confchangev2_context_deserializer(cb: PyObject) {
    *CONFCHANGEV2_CONTEXT_DESERIALIZE_CB.lock().unwrap() = Some(cb);
}

#[pyfunction]
pub fn set_confchange_context_deserializer(cb: PyObject) {
    *CONFCHANGE_CONTEXT_DESERIALIZE_CB.lock().unwrap() = Some(cb);
}

#[pyfunction]
pub fn set_message_context_deserializer(cb: PyObject) {
    *MESSAGE_CONTEXT_DESERIALIZER_CB.lock().unwrap() = Some(cb);
}

#[pyfunction]
pub fn set_snapshot_data_deserializer(cb: PyObject) {
    *SNAPSHOT_DATA_DESERIALIZER_CB.lock().unwrap() = Some(cb);
}

impl CustomDeserializer for MyDeserializer {
    fn entry_context_deserialize(&self, v: &Bytes) -> String {
        fn deserialize(py: Python, data: &[u8]) -> String {
            let callback_lock = ENTRY_CONTEXT_DESERIALIZE_CB.lock().unwrap();

            if let Some(callback) = &*callback_lock {
                callback
                    .call(py, (PyBytes::new(py, data),), None)
                    .unwrap()
                    .into_py(py)
                    .to_string()
            } else {
                format!("{:?}", data)
            }
        }

        Python::with_gil(|py| match v {
            Bytes::Prost(v) => format!("{:?}", deserialize(py, &v[..])),
            Bytes::Protobuf(v) => format!("{:?}", deserialize(py, &v[..])),
        })
    }

    fn entry_data_deserialize(&self, v: &Bytes) -> String {
        fn deserialize(py: Python, data: &[u8]) -> String {
            let callback_lock = ENTRY_DATA_DESERIALIZE_CB.lock().unwrap();

            if let Some(callback) = &*callback_lock {
                callback
                    .call(py, (PyBytes::new(py, data),), None)
                    .unwrap()
                    .into_py(py)
                    .to_string()
            } else {
                format!("{:?}", data)
            }
        }

        Python::with_gil(|py| match v {
            Bytes::Prost(v) => format!("{:?}", deserialize(py, &v[..])),
            Bytes::Protobuf(v) => format!("{:?}", deserialize(py, &v[..])),
        })
    }

    fn confchangev2_context_deserialize(&self, v: &Bytes) -> String {
        fn deserialize(py: Python, data: &[u8]) -> String {
            let callback_lock = CONFCHANGEV2_CONTEXT_DESERIALIZE_CB.lock().unwrap();

            if let Some(callback) = &*callback_lock {
                callback
                    .call(py, (PyBytes::new(py, data),), None)
                    .unwrap()
                    .into_py(py)
                    .to_string()
            } else {
                format!("{:?}", data)
            }
        }

        Python::with_gil(|py| match v {
            Bytes::Prost(v) => format!("{:?}", deserialize(py, &v[..])),
            Bytes::Protobuf(v) => format!("{:?}", deserialize(py, &v[..])),
        })
    }

    fn confchange_context_deserialize(&self, v: &Bytes) -> String {
        fn deserialize(py: Python, data: &[u8]) -> String {
            let callback_lock = CONFCHANGE_CONTEXT_DESERIALIZE_CB.lock().unwrap();

            if let Some(callback) = &*callback_lock {
                callback
                    .call(py, (PyBytes::new(py, data),), None)
                    .unwrap()
                    .into_py(py)
                    .to_string()
            } else {
                format!("{:?}", data)
            }
        }

        Python::with_gil(|py| match v {
            Bytes::Prost(v) => format!("{:?}", deserialize(py, &v[..])),
            Bytes::Protobuf(v) => format!("{:?}", deserialize(py, &v[..])),
        })
    }

    fn message_context_deserializer(&self, v: &Bytes) -> String {
        fn deserialize(py: Python, data: &[u8]) -> String {
            let callback_lock = MESSAGE_CONTEXT_DESERIALIZER_CB.lock().unwrap();

            if let Some(callback) = &*callback_lock {
                callback
                    .call(py, (PyBytes::new(py, data),), None)
                    .unwrap()
                    .into_py(py)
                    .to_string()
            } else {
                format!("{:?}", data)
            }
        }

        Python::with_gil(|py| match v {
            Bytes::Prost(v) => format!("{:?}", deserialize(py, &v[..])),
            Bytes::Protobuf(v) => format!("{:?}", deserialize(py, &v[..])),
        })
    }

    fn snapshot_data_deserializer(&self, v: &Bytes) -> String {
        fn deserialize(py: Python, data: &[u8]) -> String {
            let callback_lock = SNAPSHOT_DATA_DESERIALIZER_CB.lock().unwrap();

            if let Some(callback) = &*callback_lock {
                callback
                    .call(py, (PyBytes::new(py, data),), None)
                    .unwrap()
                    .into_py(py)
                    .to_string()
            } else {
                format!("{:?}", data)
            }
        }

        Python::with_gil(|py| match v {
            Bytes::Prost(v) => format!("{:?}", deserialize(py, &v[..])),
            Bytes::Protobuf(v) => format!("{:?}", deserialize(py, &v[..])),
        })
    }
}
