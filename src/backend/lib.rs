use pyo3::prelude::*;

#[pymodule]
fn hyper_py(_py: Python, _m: &PyModule) -> PyResult<()> {
  Ok(())
}
