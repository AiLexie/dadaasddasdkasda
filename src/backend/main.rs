use pyo3::prelude::{Python, PyObject, PyResult, PyErr};
use std::fs::canonicalize;
use std::error::Error;
use std::boxed;
use std::fmt;

#[derive(Debug)]
struct PyError {
  pyo3_error: PyErr
}

impl fmt::Display for PyError {
  fn fmt(&self, f: &mut fmt::Formatter) -> fmt::Result {
    write!(f, "Python Exception: {:?}", self.pyo3_error)
  }
}

impl Error for PyError {
  fn source(&self) -> Option<&(dyn Error + 'static)> {
    None
  }
}

fn pete<T>(py_res: PyResult<T>) -> Result<T, Box<PyError>> {
  match py_res {
    Ok(val) => Ok(val),
    Err(err) => {
      //Print actual stack trace here please!
      Err(boxed::Box::new(PyError {pyo3_error: err}))
    }
  }
}

fn main() -> Result<(), Box<dyn Error>> {
  let mod_location_raw = canonicalize("./out/")?;
  let mod_location_cow = mod_location_raw.to_string_lossy();
  let mod_location = mod_location_cow.as_ref();

  let py_gil = Python::acquire_gil();
  let py = py_gil.python();

  //Add working directory to list of module search paths.
  let sys_mod =
    pete(py.import("sys"))?;
  let py_search_paths: PyObject =
    pete(sys_mod.get("path"))?.into();
  let py_search_paths_append: PyObject =
    pete(py_search_paths.getattr(py, "append"))?.into();
  pete(py_search_paths_append.call1(py, (mod_location,)))?;

  //Import it.
  let impl_mod = pete(py.import("server_impl"))?;
  //Run it.
  pete(PyObject::from(pete(impl_mod.get("main"))?).call0(py))?;

  Ok(())
}
