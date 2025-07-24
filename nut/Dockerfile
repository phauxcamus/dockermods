FROM alpine:latest
EXPOSE 3493/tcp
HEALTHCHECK CMD upsc -l

ENV TZ=America/Phoenix

VOLUME /etc/nut

RUN apk -q --no-cache --update add nut

COPY <<EOF /bin/run-all
#!/bin/ash
rm -rf /var/run/nut/* && mkdir -m 700 /var/run/nut && chown nut:nut /var/run/nut
upsdrvctl -FF start &
upsd -FF
exit 1
EOF

RUN chmod +x /bin/run-all

CMD ['/bin/run-all']

LABEL org.opencontainers.image.source="https://github.com/phauxcamus/dockermods"
