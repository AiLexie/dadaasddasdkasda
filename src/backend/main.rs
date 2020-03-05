use pyo3::prelude::{Python, PyObject};
use std::fs::canonicalize;

fn main() {
  let panic_msg = "Python server implementation not found or invalid.";
  let mod_location_raw = canonicalize("./out/").expect(panic_msg);
  let mod_location = mod_location_raw.to_str();

  let py_gil = Python::acquire_gil();
  let py = py_gil.python();

  //Add working directory to list of module search paths.
  let sys_mod = py.import("sys").expect(panic_msg);
  let py_search_paths: PyObject = sys_mod.get("path").expect(panic_msg).into();
  let py_search_paths_append: PyObject = py_search_paths.getattr(py, "append")
    .expect(panic_msg).into();
  py_search_paths_append.call1(py, (mod_location,)).expect(panic_msg);

  //Run it.
  let res = py.import("python");
  if res.as_ref().err().is_some() {
    res.err().unwrap().print(py)
  }
}
