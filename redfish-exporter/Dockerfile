FROM python:alpine

WORKDIR /data
COPY . .

RUN python -m pip install --root-user-action ignore --upgrade pip
RUN pip install --root-user-action ignore --no-cache-dir -r requirements.txt

CMD [ "python", "app.py" ]

LABEL org.opencontainers.image.source="https://github.com/phauxcamus/dockermods"