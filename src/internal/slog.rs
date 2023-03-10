use pyo3::{prelude::*, types::PyString};
use slog::*;
use slog_async::OverflowStrategy;

use utils::reference::RustRef;

#[pyclass(name = "OverflowStrategy")]
pub struct Py_OverflowStrategy(pub OverflowStrategy);

impl Into<OverflowStrategy> for Py_OverflowStrategy {
    fn into(self) -> OverflowStrategy {
        match self.0 {
            OverflowStrategy::Block => OverflowStrategy::Block,
            OverflowStrategy::Drop => OverflowStrategy::Drop,
            OverflowStrategy::DropAndReport => OverflowStrategy::DropAndReport,
            _ => todo!(),
        }
    }
}

impl From<OverflowStrategy> for Py_OverflowStrategy {
    fn from(strategy: OverflowStrategy) -> Self {
        match strategy {
            OverflowStrategy::Block => Py_OverflowStrategy(OverflowStrategy::Block),
            OverflowStrategy::Drop => Py_OverflowStrategy(OverflowStrategy::Drop),
            OverflowStrategy::DropAndReport => Py_OverflowStrategy(OverflowStrategy::DropAndReport),
            _ => todo!(),
        }
    }
}

#[pymethods]
impl Py_OverflowStrategy {
    pub fn __hash__(&self) -> u64 {
        self.0 as u64
    }

    #[classattr]
    pub fn Block() -> Self {
        Py_OverflowStrategy(OverflowStrategy::Block)
    }

    #[classattr]
    pub fn Drop() -> Self {
        Py_OverflowStrategy(OverflowStrategy::Drop)
    }

    #[classattr]
    pub fn DropAndReport() -> Self {
        Py_OverflowStrategy(OverflowStrategy::DropAndReport)
    }
}

#[derive(Clone)]
#[pyclass(name = "Logger_Owner")]
pub struct Py_Logger_Owner {
    pub inner: Logger,
}

#[derive(Clone)]
#[pyclass(name = "Logger_Ref")]
pub struct Py_Logger_Ref {
    pub inner: RustRef<Logger>,
}

#[derive(FromPyObject)]
pub enum Py_Logger_Mut<'p> {
    Owned(PyRefMut<'p, Py_Logger_Owner>),
    RefMut(Py_Logger_Ref),
}

impl Into<Logger> for Py_Logger_Mut<'_> {
    fn into(self) -> Logger {
        match self {
            Py_Logger_Mut::Owned(x) => x.inner.clone(),
            Py_Logger_Mut::RefMut(mut x) => x.inner.map_as_mut(|x| x.clone()).unwrap(),
        }
    }
}

#[pymethods]
impl Py_Logger_Owner {
    #[new]
    pub fn new(chan_size: usize, overflow_strategy: &Py_OverflowStrategy) -> Self {
        let decorator = slog_term::TermDecorator::new().build();
        let drain = slog_term::FullFormat::new(decorator).build().fuse();
        let drain = slog_async::Async::new(drain)
            .chan_size(chan_size)
            .overflow_strategy(overflow_strategy.0)
            .build()
            .fuse();

        let logger = slog::Logger::root(drain, o!());

        Py_Logger_Owner { inner: logger }
    }

    pub fn make_ref(&mut self) -> Py_Logger_Ref {
        Py_Logger_Ref {
            inner: RustRef::new(&mut self.inner),
        }
    }
}

#[pymethods]
impl Py_Logger_Ref {
    pub fn info(&mut self, s: &PyString) -> PyResult<()> {
        self.inner
            .map_as_ref(|inner| info!(inner, "{}", format!("{}", s)))
    }

    pub fn debug(&mut self, s: &PyString) -> PyResult<()> {
        self.inner
            .map_as_ref(|inner| debug!(inner, "{}", format!("{}", s)))
    }

    pub fn trace(&mut self, s: &PyString) -> PyResult<()> {
        self.inner
            .map_as_ref(|inner| trace!(inner, "{}", format!("{}", s)))
    }

    pub fn error(&mut self, s: &PyString) -> PyResult<()> {
        self.inner
            .map_as_ref(|inner| error!(inner, "{}", format!("{}", s)))
    }

    pub fn crit(&mut self, s: &PyString) -> PyResult<()> {
        self.inner
            .map_as_ref(|inner| crit!(inner, "{}", format!("{}", s)))
    }
}
