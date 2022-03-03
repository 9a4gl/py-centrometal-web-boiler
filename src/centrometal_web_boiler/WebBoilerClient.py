# -*- coding: utf-8 -*-
"""
@author: Tihomir Heidelberg
"""

import logging
import asyncio

from centrometal_web_boiler.HttpClient import HttpClient
from centrometal_web_boiler.HttpHelper import HttpHelper
from centrometal_web_boiler.WebBoilerWsClient import WebBoilerWsClient
from centrometal_web_boiler.WebBoilerDeviceCollection import WebBoilerDeviceCollection


class WebBoilerClient:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.websocket_connected = False
        self.connectivity_callback = None
        self.ws_client = WebBoilerWsClient(
            self.ws_connected_callback,
            self.ws_disconnected_callback,
            self.ws_error_callback,
            self.ws_data_callback,
        )

    async def login(self, username, password):
        self.logger.info("WebBoilerClient - Logging in... (" + username + ")")
        self.username = username
        self.password = password
        self.http_client = HttpClient(self.username, self.password)
        self.http_helper = HttpHelper(self.http_client)
        self.data = WebBoilerDeviceCollection(username)
        return await self.http_client.login()

    async def get_configuration(self):
        await self.http_client.get_installations()
        if self.http_helper.get_device_count() == 0:
            self.logger.warning(f"WebBoilerClient - there is no installed device ({self.username})")
            return False
        self.data.parse_installations(self.http_client.installations)
        await asyncio.gather(
            self.http_client.get_configuration(), self.http_client.get_widgetgrid_list()
        )
        tasks = []
        tasks.append(
            self.http_client.get_widgetgrid(
                self.http_client.widgetgrid_list["selected"]
            )
        )
        tasks.append(
            self.http_client.get_installation_status_all(
                self.http_helper.get_all_devices_ids()
            )
        )
        for serial in self.http_helper.get_all_devices_serials():
            tasks.append(self.http_client.get_parameter_list(serial))
        tasks.append(self.http_client.get_notifications())
        await asyncio.gather(*tasks)
        await self.data.parse_installation_statuses(
            self.http_client.installation_status_all
        )
        self.data.parse_parameter_lists(self.http_client.parameter_list)
        self.data.parse_grid(self.http_client)
        return True

    async def close_websocket(self) -> bool:
        try:
            await self.ws_client.close()
            return True
        except Exception as e:
            self.logger.error("WebBoilerClient::close_websocket failed" + str(e) + f" ({self.username})")
            return False

    async def start_websocket(self, on_parameter_updated_callback):
        self.logger.info(f"WebBoilerClient - Starting websocket... ({self.username})")
        self.on_parameter_updated_callback = on_parameter_updated_callback
        device = list(self.data.values())[0]
        await self.ws_client.start(self.username, device["type"])

    async def refresh(self, delay = 2) -> bool:
        try:
            for id in self.http_helper.get_all_devices_ids():
                await self.http_client.refresh_device(id)
                await asyncio.sleep(delay)
                await self.http_client.rstat_all_device(id)
                await asyncio.sleep(delay)
            return True
        except Exception as e:
            self.logger.error("WebBoilerClient::refresh failed" + str(e) + f" ({self.username})")
            return False

    async def ws_connected_callback(self, ws, frame):
        self.logger.info(f"WebBoilerClient - connected ({self.username})")
        self.websocket_connected = True
        if self.connectivity_callback is not None:
            await self.connectivity_callback(self.websocket_connected)
        await self.ws_client.subscribe_to_notifications(ws)
        for serial in self.http_helper.get_all_devices_serials():
            await self.ws_client.subscribe_to_installation(ws, serial)
        self.data.set_on_update_callback(self.on_parameter_updated_callback)
        await self.data.notify_all_updated()

    async def ws_disconnected_callback(self, ws, close_status_code, close_msg):
        self.websocket_connected = False
        if self.connectivity_callback is not None:
            await self.connectivity_callback(self.websocket_connected)
        await self.data.notify_all_updated()
        self.logger.warning(
            f"WebBoilerClient - disconnected close_status_code:{close_status_code} close_msg:{close_msg} ({self.username})"
        )

    async def ws_error_callback(self, ws, err):
        self.logger.error(f"WebBoilerClient - error err:{err} ({self.username})")

    async def ws_data_callback(self, ws, stomp_frame):
        await self.data.parse_real_time_frame(stomp_frame)

    def is_websocket_connected(self) -> bool:
        return self.websocket_connected

    async def relogin(self):
        await self.http_client.close_session()
        await self.http_client.reinitialize_session()
        return await self.http_client.login()

    async def turn(self, serial, on):
        device = self.data.get_device_by_serial(serial)
        try:
            response = await self.http_client.turn_device_by_id(device["id"], on)
            return response["status"] == "success"
        except Exception as e:
            return False

    async def turn_circuit(self, serial, circuit, on):
        device = self.data.get_device_by_serial(serial)
        try:
            response = await self.http_client.turn_device_circuit(
                device["id"], circuit, on
            )
            return response["status"] == "success"
        except Exception as e:
            return False

    def set_connectivity_callback(self, connectivity_callback):
        self.connectivity_callback = connectivity_callback
