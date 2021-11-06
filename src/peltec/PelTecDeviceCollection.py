# -*- coding: utf-8 -*-
"""
@author: Tihomir Heidelberg
"""

import json
import time
import datetime

from const import PELTEC_STOMP_DEVICE_TOPIC, PELTEC_STOMP_NOTIFICATION_TOPIC

class PelTecParameter(dict):
    def update(self, name, value, timestamp = None):
        self["name"] = name
        self["value"] = value
        self["timestamp"] = timestamp

class PelTecDevice(dict):
    def __init__(self):
        self["parameters"] = {}
        self["temperatures"] = {}
        self["info"] = {}
        self["weather"] = {}

    def hasParameter(self, name):
        return name in self["parameters"].keys()

    def updateParameter(self, name, value, timestamp = None) -> PelTecParameter:
        if timestamp == None:
            timestamp = int(time.time())
        else:
            date_time_obj = datetime.datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S")
            timestamp = int(date_time_obj.replace(tzinfo=datetime.timezone.utc).timestamp())
        if name not in self["parameters"].keys():
            self["parameters"][name] = PelTecParameter()
        parameter = self["parameters"][name]
        parameter.update(name, value, timestamp)
        return parameter

class PelTecDeviceCollection(dict):

    def __init__(self, on_update_callback = None):
        self.on_update_callback = on_update_callback

    def setOnUpdateCallback(self, on_update_callback):
        self.on_update_callback = on_update_callback

    def getDeviceById(self, id):
        for device in self.values():
            if str(id) == str(device["id"]):
                return device
        raise Exception(f"No device with id:{id}")

    def getDeviceBySerial(self, serial):
        for device in self.values():
            if str(serial) == str(device["serial"]):
                return device
        raise Exception(f"No device with serial:{serial}")

    def parseInstallations(self, installations : dict()):
        for device in installations:
            serial = device["label"]
            self[serial] = PelTecDevice()
            self[serial]["id"] = device["value"]
            self[serial]["serial"] = device["label"]
            self[serial]["place"] = device["place"]
            self[serial]["address"] = device["address"]
            self[serial]["type"] = device["type"]
            self[serial]["product"] = device["product"]

    def parseInstallationStatuses(self, installation_status_all : dict()):
        for device_id, value in installation_status_all.items():
            device = self.getDeviceById(device_id)
            for group, data in value.items():
                if group == "installation":
                    device["country"] = data["country"]
                    device["countryCode"] = data["countryCode"]
                elif group == "params":
                    for param_id, param_data in data.items():
                        device.updateParameter(param_id, param_data["v"], param_data["ut"])
                else:
                    raise Exception(f"Unknown group in installation_status_all group:{group}")
            
    def parseParameterLists(self, parameter_list):
        for serial, device_data in parameter_list.items():
            device = self.getDeviceBySerial(serial)
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

    def _updateDeviceWithRealTimeData(self, device, body):
        data = json.loads(body)
        for param_id, value in data.items():
            if device.hasParameter(param_id):
                parameter = device.updateParameter(param_id, value)
                if self.on_update_callback is not None:
                    self.on_update_callback(device, parameter)

    def parseRealTimeFrame(self, stomp_frame):
        if "headers" in stomp_frame and "body" in stomp_frame:
            headers = stomp_frame["headers"]
            body = stomp_frame["body"]
            if "subscription" in headers and "destination" in headers:
                subscription = headers["subscription"]
                destination = headers["destination"]
                if subscription == "Peltec":
                    if destination.startswith(PELTEC_STOMP_DEVICE_TOPIC):
                        serial = destination[len(PELTEC_STOMP_DEVICE_TOPIC):]
                        device = self.getDeviceBySerial(serial)
                        self._updateDeviceWithRealTimeData(device, body)
                    else:
                        raise Exception(f"Unexpected message for destination: {destination}")
                elif subscription == PELTEC_STOMP_NOTIFICATION_TOPIC:
                    self.logger.info(f"Notification received: {body}")
                else:
                    raise Exception(f"Unexpected message for subscription: {subscription}")
