FROM python:3.10-alpine

COPY requirements.txt .
RUN pip3 install -r requirements.txt

COPY ./src /pipelines/component/src

