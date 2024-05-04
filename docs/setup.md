# Setup

Before you get started with Local RAG, ensure you have:

- A local [Ollama](https://github.com/ollama/ollama/) instance
- At least one model available within Ollama
    - `llama3:8b` or `llama2:7b` are good starter models
- Python 3.10+

**WARNING:** This application is `untested` on Windows Subsystem for Linux. For best results, please utilize a Linux host if possible.

### Local
- `pip install pipenv && pipenv install`
- `pipenv shell && streamlit run main.py`

### Docker
- `docker compose up -d`

#### Note:

If you are running Ollama as a service, you may need to add an additional configuration to your docker-compose.yml file:
```
extra_hosts:
- 'host.docker.internal:host-gateway'
```