FROM alpine:latest
EXPOSE 3493/tcp
HEALTHCHECK CMD upsc -l

VOLUME /etc/nut

RUN apk -q --no-cache --update add nut
RUN mkdir -m 700 /var/run/nut && chown nut:nut /var/run/nut

ENTRYPOINT upsdrvctl start && upsd -FF

LABEL org.opencontainers.image.source="https://github.com/phauxcamus/dockermods"
