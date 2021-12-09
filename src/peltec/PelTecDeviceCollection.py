# -*- coding: utf-8 -*-
"""
@author: Tihomir Heidelberg
"""

import json
import time
import datetime

from peltec.const import PELTEC_STOMP_DEVICE_TOPIC, PELTEC_STOMP_NOTIFICATION_TOPIC

class PelTecParameter(dict):
    def __init__(self):
        self.update_callback = None

    def set_update_callback(self, update_callback):
        self.update_callback = update_callback

    async def update(self, name, value, timestamp = None):
        self["name"] = name
        self["value"] = value
        self["timestamp"] = timestamp
        await self.notify_updated()

    async def notify_updated(self):
        if self.update_callback is not None:
            await self.update_callback(self)

class PelTecDevice(dict):
    def __init__(self):
        self["parameters"] = {}
        self["temperatures"] = {}
        self["info"] = {}
        self["weather"] = {}

    def has_parameter(self, name):
        return name in self["parameters"].keys()

    def getOrCreatePelTecParameter(self, name):
        if not name in self["parameters"].keys():
            self["parameters"][name] = PelTecParameter()
        return self["parameters"][name]

    async def update_parameter(self, name, value, timestamp = None) -> PelTecParameter:
        if timestamp == None:
            timestamp = int(time.time())
        else:
            date_time_obj = datetime.datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S")
            timestamp = int(date_time_obj.replace(tzinfo=datetime.timezone.utc).timestamp())
        if name not in self["parameters"].keys():
            self["parameters"][name] = PelTecParameter()
        parameter = self.getOrCreatePelTecParameter(name)
        await parameter.update(name, value, timestamp)
        return parameter


class PelTecDeviceCollection(dict):

    def __init__(self, on_update_callback = None):
        self.on_update_callback = on_update_callback

    def set_on_update_callback(self, on_update_callback):
        self.on_update_callback = on_update_callback

    async def notify_all_updated(self):
        if self.on_update_callback is not None:
            for device in self.values():
                parameters = device["parameters"]
                for parameter in parameters.values():
                    await self.on_update_callback(device, parameter, True)
                    await parameter.notify_updated()

    def get_device_by_id(self, id):
        for device in self.values():
            if str(id) == str(device["id"]):
                return device
        raise Exception(f"No device with id:{id}")

    def get_device_by_serial(self, serial):
        for device in self.values():
            if str(serial) == str(device["serial"]):
                return device
        raise Exception(f"No device with serial:{serial}")

    def parse_installations(self, installations : dict()):
        for device in installations:
            serial = device["label"]
            self[serial] = PelTecDevice()
            self[serial]["id"] = device["value"]
            self[serial]["serial"] = device["label"]
            self[serial]["place"] = device["place"]
            self[serial]["address"] = device["address"]
            self[serial]["type"] = device["type"]
            self[serial]["product"] = device["product"]

    async def parse_installation_statuses(self, installation_status_all : dict()):
        for device_id, value in installation_status_all.items():
            device = self.get_device_by_id(device_id)
            for group, data in value.items():
                if group == "installation":
                    device["country"] = data["country"]
                    device["countryCode"] = data["countryCode"]
                elif group == "params":
                    for param_id, param_data in data.items():
                        await device.update_parameter(param_id, param_data["v"], param_data["ut"])
                else:
                    raise Exception(f"Unknown group in installation_status_all group:{group}")
            
    def parse_parameter_lists(self, parameter_list):
        for serial, device_data in parameter_list.items():
            device = self.get_device_by_serial(serial)
            for data_id, data_value in device_data.items():
                if data_id == "city":
                    device["city"] = data_value
                elif data_id == "parameters":
                    for data_value_item in data_value:
                        group = data_value_item["group"]
                        if group == "Temperatures":
                            for list_item in data_value_item["list"]:
                                index = list_item["dbindex"]
                                device["temperatures"][index] = list_item
                        elif group == "Info":
                            for list_item in data_value_item["list"]:
                                index = list_item["installation_status"]
                                device["info"][index] = list_item
                        elif group == "Weather forecast":
                            for list_item in data_value_item["list"]:
                                index = list_item["naslov"]
                                device["weather"][index] = list_item
                        else:
                            raise Exception(f"Unknown group in parameter_list data_id:{group}")
                else:
                    raise Exception(f"Unknown data_id in parameter_list data_id:{data_id}")

    async def _update_device_with_real_time_data(self, device, body):
        data = json.loads(body)
        for param_id, value in data.items():
            if device.has_parameter(param_id):
                parameter = await device.update_parameter(param_id, value)
                if self.on_update_callback is not None:
                    await self.on_update_callback(device, parameter)

    async def parse_real_time_frame(self, stomp_frame):
        if "headers" in stomp_frame and "body" in stomp_frame:
            headers = stomp_frame["headers"]
            body = stomp_frame["body"]
            if "subscription" in headers and "destination" in headers:
                subscription = headers["subscription"]
                destination = headers["destination"]
                if subscription == "Peltec":
                    if destination.startswith(PELTEC_STOMP_DEVICE_TOPIC):
                        serial = destination[len(PELTEC_STOMP_DEVICE_TOPIC):]
                        device = self.get_device_by_serial(serial)
                        await self._update_device_with_real_time_data(device, body)
                    else:
                        raise Exception(f"Unexpected message for destination: {destination}")
                elif subscription == PELTEC_STOMP_NOTIFICATION_TOPIC:
                    self.logger.info(f"Notification received: {body}")
                else:
                    raise Exception(f"Unexpected message for subscription: {subscription}")
