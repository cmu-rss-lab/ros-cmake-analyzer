# ros-cmake-analyzer
A small Python library to analyze ROS CMake files

## Build Instructions

### Prerequisites

The code in this project requires both Python 3.12+ and Poetry to be installed.
Since Python 3.12 or greater is not provided as the system Python installation on
many distributions, we optionally recommend using pyenv to automatically install
a standalone Python 3.12 without interfering with the rest of your system.

#### pyenv (optional)

[pyenv](https://github.com/pyenv/pyenv) is a tool for managing multiple Python installations.
Installation instructions for pyenv can be found at https://github.com/pyenv/pyenv-installer.
Once you have installed the dependencies for pyenv, you can quickly install
pyenv itself by executing the following:

    curl https://pyenv.run | bash

You should then check that your `~/.profile` sources `~/.bashrc`.
Once you have ensured that is the case, you should add the following lines to
`~/.profile` immediately prior to the point where `~/.bashrc` is
sourced.

    export PYENV_ROOT="$HOME/.pyenv"
    export PATH="$PYENV_ROOT/bin:$PATH"
    eval "$(pyenv init --path)"

Additionally, you should add the following lines to your `~/.bashrc`:

    eval "$(pyenv init -)"
    eval "$(pyenv virtualenv-init -)"

After making the above changes, you should restart your shell so that the changes
in `~/.profile` and `~/.bashrc` take effect. You can then install
Python 3.12.0 via the following:

    pyenv install 3.12.0

#### Poetry (required)

[Poetry](https://python-poetry.org) is a dependency management and virtual environment management tool for Python.
It allows you to safely isolate the installation of your package and its dependencies from
your system's Python installation.

To install Poetry:

    curl -sSL https://raw.githubusercontent.com/python-poetry/poetry/master/get-poetry.py | python
    source $HOME/.poetry/env

More detailed installation instructions can be found at:
https://python-poetry.org/docs/#installation

#### Additional Dependencies (macOS)

If you are using macOS and plan to use the ROS anatomy pipeline natively, rather than via the provided Docker image, you will also need to install the following dependencies:

    brew install libmagic

### Installation

To install this project via pyenv and Poetry:

    git clone git@github.com:cmu-rss/ros-cmak-analyzer
    cd ros-cmak-analyzer
    pyenv local 3.12.0
    poetry install

Notice that `pyenv local 3.12.0` instructs `pyenv` to use
Python 3.12.0 as `python` within the repo directory.

    $ cd ros-cmak-analyzer
    $ python --version
    Python 3.12.0

## Development Container

In addition, there is a devcontainer defintion in `devcontainer/devcontainer.json`.

## Use

The library defines code for reading `package.xml` and `CMakeLists.txt` files to
determine the source code for nodes, plugins, and other libraries.

To use in your own code, you need to do the following (for ROS 1):

```python
import ros_cmake_analyzer.ros1.ROS1CMakeExtractor

path = "."  # Path contains a package.xml and CMakeLists.txt
cmake = ROS1CMakeExtractor(path)
info = cmake.get_cmake_info()

```

The `info` object is an instance of `ros_cmake_extractor.CMakeInfo`, which contains
a dictionary of targets, keyed by name, and a list of sources that will be generated.

Note that when the analyzer is used on projects that are not built, the generated sources
will not exist.