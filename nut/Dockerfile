FROM alpine:latest
EXPOSE 3493/tcp
HEALTHCHECK CMD upsc -l

ENV TZ=America/Phoenix

VOLUME /etc/nut

RUN apk -q --no-cache --update add nut

COPY <<EOF /run-all
#!/bin/ash
rm -rf /var/run/nut/* 2> /dev/null && mkdir -m 700 /var/run/nut && chown nut:nut /var/run/nut
upsdrvctl -FF start &
upsd -FF
exit 1
EOF

RUN chmod +x /run-all

ENTRYPOINT ["/run-all"]

LABEL org.opencontainers.image.source="https://github.com/phauxcamus/dockermods"
