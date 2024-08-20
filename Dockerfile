#FROM python:alpine3.17
FROM python:3.12-slim

WORKDIR /app
COPY ["src/constants.py", "src/logging.config", "src/data_interface.py", "src/main.py", "requirements.txt", "./"]

RUN python -m pip install --upgrade pip && \
    pip install -r ./requirements.txt && \
    groupadd --gid 1000 appuser \
    && useradd --uid 1000 --gid 1000 -ms /bin/bash appuser

USER appuser

#RUN git clone https://github.com/streamlit/streamlit-example.git app


# RUN python -m pip install --upgrade pip && \
#     pip install -r ./requirements.txt
# ENV PATH="${PATH}:/home/appuser/.local/bin"

EXPOSE 8501

# debugging options...  "--server.enableWebsocketCompression=false", "--server.enableCORS=false", "--server.enableXsrfProtection=false"
ENTRYPOINT ["streamlit", "run", "main.py"]
