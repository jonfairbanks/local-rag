# Setup

Before you get started with Local RAG, ensure you have:

- A local [Ollama](https://github.com/ollama/ollama/) instance
- At least one model available within
    - `llama2:7b` is a good starter model
- Python 3.10+

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