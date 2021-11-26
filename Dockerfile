FROM python:3.7-slim

RUN apt-get update && apt-get install -y gcc git make build-essential checkinstall

WORKDIR inspectorcell
COPY . .
RUN ./icell -i venv
CMD ./icell
