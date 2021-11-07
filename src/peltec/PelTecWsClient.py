# -*- coding: utf-8 -*-
"""
@author: Tihomir Heidelberg
"""

import websocket
import threading
import logging
import stomper

from .const import (
    PELTEC_STOMP_LOGIN_USERNAME, 
    PELTEC_STOMP_LOGIN_PASSCODE, 
    PELTEC_STOMP_URL, 
    PELTEC_STOMP_DEVICE_TOPIC, 
    PELTEC_STOMP_NOTIFICATION_TOPIC)

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
            on_message = self.onWebsocketMessage, 
            on_error = self.onWebsocketError, 
            on_close = self.onWebsocketClosed)
        self.ws.on_open = self.onWebsocketOpen
        self.ws_thread = threading.Thread(
            target = self.ws.run_forever, 
            kwargs = {"ping_interval": 60, "ping_timeout": 5})
        self.ws_thread.daemon = True
        self.ws_thread.start()
        self.logger.info("PelTecWsClient starting...")

    def subscribeToNotifications(self, ws):
        self.logger.info(f"PelTecWsClient::subscribeToNotifications")
        topic = PELTEC_STOMP_NOTIFICATION_TOPIC
        ws.send(stomper.subscribe(topic, "sub-0", "auto"))

    def subscribeToInstallation(self, ws, serial):
        self.logger.info(f"PelTecWsClient::subscribeToInstallation {serial}")
        topic = PELTEC_STOMP_DEVICE_TOPIC + serial
        ws.send(stomper.subscribe(topic, "Peltec", "auto"))

    def onWebsocketMessage(self, ws, data):
        if data == "\n":
            ws.send("\n")
            return
        frame = stomper.unpack_frame(data)
        if frame["cmd"] == "ERROR":
            self.error_callback(ws, frame)
            return
        if frame["cmd"] == "CONNECTED":
            self.logger.info(f"PelTecWsClient::onWebsocketMessage connected")
            self.subscribeToNotifications(ws)
            self.connected_callback(ws, frame)
            return
        self.logger.debug(f"PelTecWsClient::onWebsocketMessage {frame}")
        self.data_callback(ws, frame)

    def onWebsocketError(self, ws, err):
        self.logger.error(f"PelTecWsClient::onWebsocketError - {err}")
        self.error_callback(ws, err)

    def onWebsocketClosed(self, ws, close_status_code, close_msg):
        self.logger.info(f"PelTecWsClient::onWebsocketClosed close_status_code:{close_status_code} close_msg:{close_msg}")
        self.disconnected_callback(ws, close_status_code, close_msg)

    def onWebsocketOpen(self, ws):
        self.logger.info(f"PelTecWsClient::onWebsocketOpen -> connecting ...")
        ws.send(stomper.connect(PELTEC_STOMP_LOGIN_USERNAME, PELTEC_STOMP_LOGIN_PASSCODE, "/", (10000, 10000)))

