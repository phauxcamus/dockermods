# phauxcamus/dockermods:flask
# some small change
FROM python:alpine

WORKDIR /data

RUN python -m pip install --upgrade pip && \
	pip install --no-cache-dir flask requests feedgen bs4

ENV TZ America/Phoenix

CMD [ "python", "app.py" ]
