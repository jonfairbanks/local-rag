FROM python:3.11-alpine

RUN adduser -D python
RUN mkdir /app/ && chown -R python:python /app
WORKDIR /app

USER python

COPY --chown=python:python . .

RUN pip install --trusted-host pypi.python.org pipenv
RUN pipenv install && pipenv shell

EXPOSE 8501

CMD ["streamlit", "run", "main.py"]