use pyo3::{types::PyBytes, IntoPy, Python};

#[macro_export]
macro_rules! deserialize_bytes {
    ($inner:ident, $deserializer_name: literal, $attr:ident, $py:ident) => {{
        if let Some(deserializer) = $py.eval($deserializer_name, None, None).ok() {
            deserializer
                .call((PyBytes::new($py, $inner.$attr.as_slice()),), None)
                .unwrap()
                .into_py($py)
                .to_string()
        } else {
            format!("{:?}", $inner.$attr)
        }
    }};
}

// IMPORTANT: UNCOMMENT ALL THE BELOW CODES when you want to use raft-rs's upstream repository.
use raft::derializer::{Bytes, CustomDeserializer};
pub struct MyDeserializer;

// TODO: Refactor below codes to reduce code redundancy.
impl CustomDeserializer for MyDeserializer {
    fn entry_context_deserialize(&self, v: &Bytes) -> String {
        fn deserialize(py: Python, data: &[u8]) -> String {
            if let Some(deserializer) = py.eval("entry_context_deserializer", None, None).ok() {
                deserializer
                    .call((PyBytes::new(py, data),), None)
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
            if let Some(deserializer) = py.eval("entry_data_deserializer", None, None).ok() {
                deserializer
                    .call((PyBytes::new(py, data),), None)
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
            if let Some(deserializer) = py
                .eval("confchangev2_context_deserializer", None, None)
                .ok()
            {
                deserializer
                    .call((PyBytes::new(py, data),), None)
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
            if let Some(deserializer) = py.eval("confchange_context_deserializer", None, None).ok()
            {
                deserializer
                    .call((PyBytes::new(py, data),), None)
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
            if let Some(deserializer) = py.eval("message_context_deserializer", None, None).ok() {
                deserializer
                    .call((PyBytes::new(py, data),), None)
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
            if let Some(deserializer) = py.eval("snapshot_data_deserializer", None, None).ok() {
                deserializer
                    .call((PyBytes::new(py, data),), None)
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
