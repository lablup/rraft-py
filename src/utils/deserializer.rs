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
