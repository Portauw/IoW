#!/bin/bash

echo "Going down!"
sudo ifconfig wlan0 down
sleep 120
echo "Going back up!"
sudo ifconfig wlan0 up
echo "Back online!"
