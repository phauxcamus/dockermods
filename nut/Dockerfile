FROM alpine:latest
EXPOSE 3493/tcp
HEALTHCHECK CMD upsc -l

ENV TZ=America/Phoenix

VOLUME /etc/nut

RUN apk -q --no-cache --update add nut

ADD start.sh /start.sh

RUN chmod +x /start.sh

ENTRYPOINT ["/start.sh"]

LABEL org.opencontainers.image.source="https://github.com/phauxcamus/dockermods"
