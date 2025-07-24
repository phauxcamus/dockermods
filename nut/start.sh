#!/bin/sh
rm -rf /var/run/nut/* 2> /dev/null && mkdir -m 700 /var/run/nut && chown nut:nut /var/run/nut
upsdrvctl -FF start &
upsd -FF
exit 1
