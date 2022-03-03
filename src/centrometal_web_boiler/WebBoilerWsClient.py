# -*- coding: utf-8 -*-
"""
@author: Tihomir Heidelberg
"""

import logging
import stomper
import ssl
import ws

from centrometal_web_boiler.const import (
    WEB_BOILER_STOMP_LOGIN_USERNAME, 
    WEB_BOILER_STOMP_LOGIN_PASSCODE, 
    WEB_BOILER_STOMP_URL, 
    WEB_BOILER_STOMP_DEVICE_TOPIC, 
    WEB_BOILER_STOMP_NOTIFICATION_TOPIC)

class WebBoilerWsClient:

    def __init__(self, connected_callback, disconnected_callback, close_callback, data_callback):
        self.logger = logging.getLogger(__name__)
        self.connected_callback = connected_callback
        self.disconnected_callback = disconnected_callback
        self.close_callback = close_callback
        self.data_callback = data_callback
        self.client = ws.ClientSocket()
        self.username = ""

        @self.client.on('connect')        
        async def on_connect():
            self.logger.info(f"WebBoilerWsClient::on_connect ({self.username})")
            await self.client.send(stomper.connect(WEB_BOILER_STOMP_LOGIN_USERNAME, WEB_BOILER_STOMP_LOGIN_PASSCODE, "/", (90000, 60000)))

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
                self.logger.info(f"WebBoilerWsClient::on_message connected ({self.username})")
                await self.connected_callback(self.client, frame)
                return
            self.logger.debug(f"WebBoilerWsClient::on_message {frame} ({self.username})")
            await self.data_callback(self.client, frame)

        @self.client.on('disconnect')
        async def on_disconnect(code, reason):
            self.logger.error(f"WebBoilerWsClient::on_disconnect - {code} - {reason} ({self.username})")
            await self.disconnected_callback(self.client, code, reason)

        @self.client.on("close")
        async def on_close(code, reason):
            self.logger.info(f"WebBoilerWsClient::on_close close_status_code:{code} close_msg:{reason} ({self.username})")
            await self.disconnected_callback(self.client, code, reason)

    async def start(self, username, type):
        self.username = username
        self.type = type
        self.logger.info(f"WebBoilerWsClient connecting... ({self.username})")
        # _ClientSocket__main is hack to call private method __main in ClientSocket
        self.client.loop.create_task(self.client._ClientSocket__main(WEB_BOILER_STOMP_URL, ssl=ssl.create_default_context()))

    async def close(self):
        if self.client.connection:
            await self.client.close()

    async def subscribe_to_notifications(self, ws):
        self.logger.info(f"WebBoilerWsClient::subscribe_to_notifications ({self.username})")
        topic = WEB_BOILER_STOMP_NOTIFICATION_TOPIC
        await self.client.send(stomper.subscribe(topic, "sub-0", "auto"))

    async def subscribe_to_installation(self, ws, serial):
        self.logger.info(f"WebBoilerWsClient::subscribe_to_installation {serial} ({self.username})")
        topic = WEB_BOILER_STOMP_DEVICE_TOPIC + self.type + "." + serial
        await self.client.send(stomper.subscribe(topic, "sub-1", "auto"))
