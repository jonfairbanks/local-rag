FROM python:3.14-slim AS base

# Setup env
ENV LANG=C.UTF-8
ENV LC_ALL=C.UTF-8
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONFAULTHANDLER=1


FROM base AS python-deps

ENV PIP_NO_CACHE_DIR=1

# Install pipenv and compilation dependencies
RUN pip install pipenv
RUN apt-get update && apt-get install -y --no-install-recommends gcc \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies in /.venv
COPY Pipfile .
COPY Pipfile.lock .
RUN PIPENV_VENV_IN_PROJECT=1 pipenv install --deploy
COPY scripts/fix_cusparselt_metadata.py /tmp/fix_cusparselt_metadata.py
RUN /.venv/bin/python /tmp/fix_cusparselt_metadata.py \
    && /.venv/bin/python -m pip check


FROM base AS runtime

# Copy virtual env from python-deps stage
COPY --from=python-deps /.venv /.venv
ENV PATH="/.venv/bin:$PATH"

# Create and switch to a new user
RUN useradd --create-home appuser
WORKDIR /home/appuser
USER appuser

# Install application into container
COPY . .

# Expose the Streamlit port
EXPOSE 8501

# Setup a health check against Streamlit
HEALTHCHECK CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8501/_stcore/health', timeout=5)"

# Run the application
ENTRYPOINT [ "python", "-m", "streamlit" ]
CMD ["run", "main.py", "--server.port=8501", "--server.address=0.0.0.0"]

FROM runtime AS test
RUN HF_HUB_OFFLINE=1 python tests/container_smoke.py

FROM runtime AS final
