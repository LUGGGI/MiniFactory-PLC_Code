# MiniFactory

Documentation found in doc [/docs/_build/html/index.html](/docs/_build/html/index.html "/docs/_build/html/index.html").

## Command for uploading new software to right factory

```
scp -r lib rightline.py right_wh_content.json right_config.json pi@RightMiniFactory:/var/lib/revpipyload/PLC_Code
```

## Command for uploading new software to left factory

```
scp -r lib leftline.py left_wh_content.json left_config.json pi@LeftMiniFactory:/var/lib/revpipyload/PLC_Code
```

## Other

deactivate hw_clock
``sudo sh -c "echo 1-0051 > /sys/bus/i2c/drivers/rtc-pcf2127-i2c/unbind"``
change to uni time server

```
sudo nano /etc/systemd/timesyncd.conf
ADD lINE NTP=rustime01.rus.uni-stuttgart.de rustime02.rus.uni-stuttgart.de
systemctl restart systemd-timesyncd.service
```

change defaut python verision

```
Go to /usr/bin:
cd /usr/bin
Remove the current link:
sudo rm python
Link the version you intend to use instead:
sudo ln -s /usr/local/bin/python3.12 python
```

upload config if revpicommand is not working

```
copy file to /tmp
move into /tmp
sudo cp _config.rsc /var/www/revpi/pictory/projects

```
