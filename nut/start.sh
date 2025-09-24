#!/bin/sh

# Housekeeping
rm -rf /var/run/nut/* 2> /dev/null
mkdir /var/run/nut 2> /dev/null
chown -R nut:nut /etc/nut /var/run/nut
chmod -R 700 /etc/nut /var/run/nut

# Start
upsdrvctl -FF start &
upsd -FF

# Programs exited
echo "Fell through, dumping state and quitting"
upsc -l
exit 1
