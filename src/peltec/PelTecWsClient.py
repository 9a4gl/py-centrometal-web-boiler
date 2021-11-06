# -*- coding: utf-8 -*-
"""
@author: Tihomir Heidelberg
"""

import websocket
import threading
import logging

from const import PELTEC_STOMP_LOGIN_USERNAME, PELTEC_STOMP_LOGIN_PASSCODE, PELTEC_STOMP_URL

class PelTecWsClient:

    def __init__(self, connected_callback, disconnected_callback, error_callback, data_callback):
        self.ws = None
        self.ws_thread = None
        self.logger = logging.getLogger(__name__)
        self.connected_callback = connected_callback
        self.disconnected_callback = disconnected_callback
        self.error_callback = error_callback
        self.data_callback = data_callback

    def start(self, enableWebSocketTracing = False):
        websocket.enableTrace(enableWebSocketTracing)
        self.ws = websocket.WebSocketApp(
            PELTEC_STOMP_URL, 
            on_message = self.on_msg, 
            on_error = self.on_error, 
            on_close = self.on_closed)
        self.ws.on_open = self.on_open
        self.ws_thread = threading.Thread(
            target = self.ws.run_forever, 
            kwargs = {"ping_interval": 60, "ping_timeout": 5})
        self.ws_thread.daemon = True
        self.ws_thread.start()
        self.logger.info("PelTecWsClient starting...")

    def subscribeToNotifications(self, ws):
        self.logger.info(f"PelTecWsClient::subscribeToNotifications")
        topic = "/queue/notification"
        msg = "SUBSCRIBE\nid:%s\ndestination:%s\nack:%s\n\n\x00\n" % ("sub-0", topic, "auto")
        ws.send(msg)

    def subscribeToInstallation(self, ws, serial):
        self.logger.info(f"PelTecWsClient::subscribeToInstallation {serial}")
        topic = "/topic/cm.inst.peltec." + serial
        msg = "SUBSCRIBE\nid:%s\ndestination:%s\nack:%s\n\n\x00\n" % ("Peltec", topic, "auto")
        ws.send(msg)

    def on_msg(self, ws, msg):
        if msg == "\n":
            ws.send("\n")
            return
        self.logger.debug(f"PelTecWsClient::on_msg {msg}")
        if msg.startswith("ERROR"):
            self.error_callback(ws, msg)
            return
        if msg.startswith("CONNECTED"):
            self.logger.info(f"PelTecWsClient::on_msg connected -> subscribing ...")
            self.subscribeToNotifications(ws)
            self.connected_callback(ws)
            return
        self.data_callback(ws, msg)

    def on_error(self, ws, err):
        self.logger.error(f"PelTecWsClient::on_error - {err}")
        self.error_callback(ws, err)

    def on_closed(self, ws, close_status_code, close_msg):
        self.logger.error("PelTecWsClient::on_closed #Closed#")
        self.logger.error(f"PelTecWsClient::on_closed close_status_code:", close_status_code)
        self.logger.error(f"PelTecWsClient::on_closed close_msg:", close_msg)
        self.disconnected_callback(ws, close_status_code, close_msg)

    def on_open(self, ws):
        self.logger.info(f"PelTecWsClient::on_open -> connecting ...")
        msg = "CONNECT\naccept-version:1.2\nheart-beat:%i,%i\nlogin:%s\npasscode:%s\n\n\x00\n" % (10000, 10000, PELTEC_STOMP_LOGIN_USERNAME, PELTEC_STOMP_LOGIN_PASSCODE)
        ws.send(msg)

