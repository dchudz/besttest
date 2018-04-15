This is an early prototype. I'd love if people try it out and let me know what you think, but there's a good chance it's not worth your time yet.

## Goal

Isn't it stressful when *all* your tests are failing? If there's a common cause to all your tests failing, this package aims to notice it and let you know.

We'll tell you that even though you have 765 failing tests, there's a single one that covers code that all the other failing tests cover too.

Since that code's probably broken, there's a code chance that fixing just this one test will fix all of them.

## Installation

This depends on the master branch of `pytest-cov` which (at the time of this writing) isn't released.

To install both the required version of that and this package itself, do:

```
pip install git+git://github.com/pytest-dev/pytest-cov.git@861955bf4fc5dac573ae4bd4f1ec50cd4934585b
pip install git+git://github.com/dchudz/besttest.git@master
```

## Example & Usage

In `example/`, we have:

`functions.py`:

```
def f():
    assert False


def g():
    f()


def h():
    f()
```

`test_functions.py`:

```
from functions import f, g, h


def test_f():
    f()


def test_g():
    g()


def test_h():
    h()
```

Run:

```
python -m pytest --cov-besttest=functions
```

Then in the output, we see all 3 failures, followed by this message:

```
All other failures include the code covered by these failures:
  example/test_functions.py::test_f
```


## How this works & future directions

This package is a terrible hack on top of `pytest-cov`. It's basically the `pytest-cov` plugin, but with some additional hooks that lead us to record code coverage for each test individually.

I'm not sure what the best path forward is: probably either a more sensible integration with `pytest-cov`, or doing something entirely separate.

## What doesn't work

Subprocesses won't be included. That can lead to very wrong results.

Lots of other stuff too probably.