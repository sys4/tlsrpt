# tlsrpt
A set of libraries and tools to implement TLSRPT reporting into an MTA and to generate and submit TLSRPT reports.


# How to setup the virtual environment for Python

Clone this repository and chdir into to the root directory of the repository:

```
git clone https://github.com/sys4/tlsrpt.git
cd tlsrpt
```

Then create a new virtual environment (venv) for Python using the following command:

```
python3 -m venv venv
```

You have to do this only once. After this, the `venv` directory is created that contains
the files of the Python venv.

Activate the venv by typing the shell command

```
source venv/bin/activate
```

This should change the shell prompt, you should now see a `(venv)` in front of the shell prompt
as long as the venv is activated.

Inside the activated venv you can now install everything that is needed for development and testing
with this command:

```
python -m pip install ".[test]"
```

This will install both the dependencies of the `tlsrpt` package as well as any testing tools (e.g. `tox`)
that are necessary for running automated tests.


# Running the unit tests manually

To run the unit tests manually on the console, first activate the venv (if not already activated) and the
run the tests:

```
$ source venv/bin/activate
(venv) $ python -m unittest discover

.
----------------------------------------------------------------------
Ran 1 test in 0.000s

OK
```


