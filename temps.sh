#!/bin/bash
cd /home/pi/octobot/
> temps_t.txt
echo -n "🌡 Верх бокса: |"  >> temps_t.txt
cat /sys/bus/w1/devices/28-00044a1fefff/temperature >> temps_t.txt
echo -n "🌡 Снаружи/подвал: |"  >> temps_t.txt
cat /sys/bus/w1/devices/28-00044e4508ff/temperature >> temps_t.txt
echo -n "🌡 Радиатор: |"  >> temps_t.txt
cat /sys/bus/w1/devices/28-00044e5814ff/temperature >> temps_t.txt
echo -n "🌡 Экструдер: |"  >> temps_t.txt
cat /sys/bus/w1/devices/28-00044e5ed6ff/temperature >> temps_t.txt
echo -n "🌡 Низ бокса: |" >> temps_t.txt
cat /sys/bus/w1/devices/28-00044e681aff/temperature >> temps_t.txt
mv temps_t.txt temps.txt
python3 gettemps.py