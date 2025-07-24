#!/bin/sh

# Housekeeping
rm -rf /var/run/nut/* 2> /dev/null && mkdir -m 700 /var/run/nut 2> /dev/null && chown nut:nut /var/run/nut
chown -R nut:nut /etc/nut && chmod -R 700 /etc/nut

# Start
upsdrvctl -FF start &
upsd -FF

# Programs exited
echo "Fell through, dumping state and quitting"
upsc -l
exit 1
