FROM python:alpine

WORKDIR /data
COPY . .

RUN python -m pip --root-user-action install --upgrade pip
RUN pip --root-user-action install --no-cache-dir -r requirements.txt

CMD [ "python", "app.py" ]

LABEL org.opencontainers.image.source="https://github.com/phauxcamus/dockermods"