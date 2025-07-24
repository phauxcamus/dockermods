#!/bin/sh
rm -rf /var/run/nut/* 2> /dev/null && mkdir -m 700 /var/run/nut 2> /dev/null && chown nut:nut /var/run/nut
upsdrvctl -FF start &
upsd -FF
echo "Fell through"
upsc -l
exit 99
