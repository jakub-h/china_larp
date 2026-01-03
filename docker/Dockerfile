FROM python:3.12-slim-bookworm

ARG DEBIAN_FRONTEND=noninteractive

# Keep the devcontainer expectation: interpreter at /opt/venv/bin/python
ENV VIRTUAL_ENV=/opt/venv
ENV PATH="/opt/venv/bin:${PATH}"

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        ca-certificates \
        curl \
        git \
        locales \
        zsh \
    && rm -rf /var/lib/apt/lists/*

# Locale is also set by .devcontainer/on-create-command.sh, but having it here
# makes non-devcontainer usage consistent too.
RUN echo "en_US.UTF-8 UTF-8" >> /etc/locale.gen \
    && locale-gen

RUN python -m venv "${VIRTUAL_ENV}" \
    && python -m pip install --upgrade pip \
    && python -m pip install --upgrade uv

WORKDIR /mnt/workspace

# Install app deps (and the app itself) via pyproject.toml.
# We copy pyproject first to maximize Docker layer caching, then copy the whole repo
# so we don't have to keep a manual list of files here.
COPY pyproject.toml README.md LICENSE /tmp/china_larp/
COPY . /tmp/china_larp/
RUN cd /tmp/china_larp \
    && uv pip install --no-cache -e ".[dev]" \
    && rm -rf /tmp/china_larp

EXPOSE 5000

CMD ["python", "app.py"]
