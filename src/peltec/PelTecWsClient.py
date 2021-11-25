# -*- coding: utf-8 -*-
"""
@author: Tihomir Heidelberg
"""

import logging
import stomper
import peltec.ws

from peltec.const import (
    PELTEC_STOMP_LOGIN_USERNAME, 
    PELTEC_STOMP_LOGIN_PASSCODE, 
    PELTEC_STOMP_URL, 
    PELTEC_STOMP_DEVICE_TOPIC, 
    PELTEC_STOMP_NOTIFICATION_TOPIC)

class PelTecWsClient:

    def __init__(self, connected_callback, disconnected_callback, close_callback, data_callback):
        self.logger = logging.getLogger(__name__)
        self.connected_callback = connected_callback
        self.disconnected_callback = disconnected_callback
        self.close_callback = close_callback
        self.data_callback = data_callback
        self.client = peltec.ws.ClientSocket()

        @self.client.on('connect')        
        async def on_connect():
            self.logger.info(f"PelTecWsClient::on_connect -> stop connecting ...")
            await self.client.send(stomper.connect(PELTEC_STOMP_LOGIN_USERNAME, PELTEC_STOMP_LOGIN_PASSCODE, "/", (90000, 60000)))

        @self.client.on('message')
        async def on_message(message):
            data = message.data
            # Send new line to any frame (keep alive frame)
            await self.client.send("\n")
            if data == "\n": # We received keep alive frame, ignore it
                return
            frame = stomper.unpack_frame(data)
            if frame["cmd"] == "ERROR":
                await self.error_callback(self.client, frame)
                return
            if frame["cmd"] == "CONNECTED":
                self.logger.info(f"PelTecWsClient::on_message connected")
                await self.connected_callback(self.client, frame)
                return
            self.logger.debug(f"PelTecWsClient::on_message {frame}")
            await self.data_callback(self.client, frame)

        @self.client.on('disconnect')
        async def on_disconnect(code, reason):
            self.logger.error(f"PelTecWsClient::on_disconnect - {code} - {reason}")
            await self.disconnected_callback(self.client, code, reason)

        @self.client.on("close")
        async def on_close(code, reason):
            self.logger.info(f"PelTecWsClient::on_close close_status_code:{code} close_msg:{reason}")
            await self.disconnected_callback(self.client, code, reason)

    async def start(self):
        self.logger.info("PelTecWsClient connecting...")
        self.client.connect(PELTEC_STOMP_URL)

    async def close(self):
        await self.client.close()

    async def subscribe_to_notifications(self, ws):
        self.logger.info(f"PelTecWsClient::subscribe_to_notifications")
        topic = PELTEC_STOMP_NOTIFICATION_TOPIC
        await self.client.send(stomper.subscribe(topic, "sub-0", "auto"))

    async def subscribe_to_installation(self, ws, serial):
        self.logger.info(f"PelTecWsClient::subscribe_to_installation {serial}")
        topic = PELTEC_STOMP_DEVICE_TOPIC + serial
        await self.client.send(stomper.subscribe(topic, "Peltec", "auto"))
