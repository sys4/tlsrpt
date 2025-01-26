# Description of the Release Process 

## Releasing the Python tools on PyPI

1. Create a new releas branch: `$ git checkout -n "release/v1.2.3"`
2. Bump the version number in `pyproject.toml`
3. Install the package and the dev dependencies in a local virtualenv:
  * `$ python -m venv .venv`
  * `$ source .venv/bin/activate`
  * `(.venv) $ python -m pip install -e '.[dev]'`
4. Build the Python package: `python -m build`
  * This will create tlsrpt-x.y.z.tar.gz and tlsrpt-1.2.3-py3-none-any.whl in the `dist/` subdir.
5. Send packages to Test PyPI: `python3 -m twine upload --repository testpypi dist/*`
  * You need to enter your API key in order to finish this operation
  * Notice: this command will upload to the test instance of PyPI (test.pypi.org).


