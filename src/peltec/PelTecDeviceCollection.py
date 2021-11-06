# -*- coding: utf-8 -*-
"""
@author: Tihomir Heidelberg
"""

import json

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

    def updateParameter(self, name, value, timestamp = None):
        if name not in self["parameters"].keys():
            self["parameters"][name] = PelTecParameter()
        self["parameters"][name].update(name, value, timestamp)

class PelTecDeviceCollection(dict):

    def getDeviceById(self, id):
        for device_id, device in self.items():
            if str(id) == str(device["id"]):
                return device
        raise Exception(f"No device with id:{id}")

    def getDeviceBySerial(self, serial):
        for device_id, device in self.items():
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

    def parseRealTimeFrame(self, frame):
        pass