# -*- coding: utf-8 -*-
"""
@author: Tihomir Heidelberg
"""

import os

PELTEC_WEBROOT = 'https://www.web-boiler.com'
PELTEC_WEB_CERTIFICATE_FILE = os.path.dirname(__file__)  + "/certs.pem"

PELTEC_STOMP_LOGIN_USERNAME = "appuser"
PELTEC_STOMP_LOGIN_PASSCODE = "appuser"
PELTEC_STOMP_URL = 'wss://web-boiler.com:15671/ws'
PELTEC_STOMP_DEVICE_TOPIC = "/topic/cm.inst.peltec."