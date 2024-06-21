FROM mcr.microsoft.com/devcontainers/base:jammy
# FROM mcr.microsoft.com/devcontainers/base:jammy

ARG DEBIAN_FRONTEND=noninteractive
ARG USER=vscode

RUN DEBIAN_FRONTEND=noninteractive \
    && apt-get update \
    && apt-get install -y --no-install-recommends \
        autoconf \
        automake \
        build-essential \
        ca-certificates \
        cmake \
        cpio \
        curl \
        dpkg-dev \
        file \
        vim \
        g++ \
        gdb \
        git \
        language-pack-en \
        libantlr-dev \
        libarchive-dev \
        libbz2-dev \
        libcurl4-openssl-dev \
        libffi-dev \
        liblzma-dev\
        libncurses5-dev \
        libreadline-dev \
        libsqlite3-dev \
        libssl-dev \
        libssl-dev \
        libtool \
        libxml2-dev \
        libxml2-utils \
        libxmlsec1-dev \
        libxslt1-dev \
        llvm \
        locales \
        locales-all \
        make \
        man \
        ninja-build \
        pkg-config \
        software-properties-common \
        tk-dev \
        valgrind \
        wget \
        xz-utils \
        zip \
        libboost-all-dev \
        antlr \
    && rm -rf /var/lib/apt/lists/*

# Python and poetry installation
USER $USER
ARG HOME="/home/$USER"
ARG PYTHON_VERSION=3.10

ENV PYENV_ROOT="${HOME}/.pyenv"
ENV PATH="${PYENV_ROOT}/shims:${PYENV_ROOT}/bin:${HOME}/.local/bin:$PATH"

RUN echo "done 0" \
    && curl https://pyenv.run | bash \
    && echo "done 1" \
    && pyenv install ${PYTHON_VERSION} \
    && echo "done 2" \
    && pyenv global ${PYTHON_VERSION} \
    && echo "done 3" \
    && curl -sSL https://install.python-poetry.org | python3 - \
    && poetry config virtualenvs.in-project true