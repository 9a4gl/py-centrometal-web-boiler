# py-centrometal-web-boiler

Python library to interact with Centrometal Boiler System. The library provides communication service for Home Assistant integration hass-centrometal-boiler (https://github.com/9a4gl/hass-centrometal-boiler).

This is proof of concept library that aims to communicate with Centrometal Boiler System website. It is based on analysis of Centrometal's web application. I have asked Centrometal for specification and support for integrating their boilers into Home Assistant. They have not replied to any of my 5 emails sent during March, April and May of 2021. After calling them by phone, they comfirmed receiving of my emails and promised to contact me back on Friday 16-Apr-2021, but that have not happened on 16-Apr-2021 or any date later so far. What a pity. 

## PYPI

Library is available from https://pypi.org/project/py-centrometal-web-boiler/

Install it with: pip install py-centrometal-web-boiler

## How to use it

* Create virtual environment

python -m venv vbenv

* Activate virtual environment

venv/Scripts/Activate.ps1

* Install dependencies

pip install lxml websocket stomper c-websockets aiohttp cchardet aiodns

* Run example

python.exe examples\test_client.py --username your.email@example-com --password some_password

## Disclaimer

Use it at your own risk.
