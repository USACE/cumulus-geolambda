ARG VERSION=2.0.0
FROM rsgis/geolambda:${VERSION}

ARG PYVERSION=3.7.4

# install Python
ENV \
    PYENV_ROOT=/root/.pyenv \
    PATH=/root/.pyenv/shims:/root/.pyenv/bin:$PATH

RUN \
    curl https://pyenv.run | bash; \
    CONFIGURE_OPTS="--with-openssl=${PREFIX}/openssl" \
        LD_RUN_PATH="${PREFIX}/openssl/lib" \
        pyenv install ${PYVERSION}; \
    pyenv global ${PYVERSION}; \
    pip install --upgrade pip

COPY requirements*.txt ./

RUN \
    pip install -r requirements-pre.txt; \
    pip install -r requirements.txt

# Copy, build, install cumulus
COPY ./cumulus ./cumulus
RUN cd cumulus \
 && pip install wheel \
 && python3 setup.py bdist_wheel \
 && pip install dist/snodas-0.0.1-py3-none-any.whl \
 && cd ../ \
 && rm -rf ./cumulus

COPY bin/* /usr/local/bin/
