# -*- coding: utf-8 -*-
"""
@author: Tihomir Heidelberg
"""

from centrometal_web_boiler.HttpClient import HttpClient

class HttpHelper:
    def __init__(self, client : HttpClient):
        self.client = client
    
    def get_device_count(self):
        return len(self.client.installations)

    def getDevice(self, index):
        if index < self.get_device_count():
            return self.client.installations[index]
        raise Exception("HttpHelper:getDevice invalid index")

    def get_device_by_id(self, id):
        for device in self.client.installations:
            if str(device["value"]) == str(id):
                return device
        raise Exception("HttpHelper:get_device_by_id invalid id")

    def get_device_by_serial(self, serial):
        for device in self.client.installations:
            if device["label"] == serial:
                return device
        raise Exception("HttpHelper:get_device_by_serial invalid serial")

    def get_all_devices_ids(self):
        result = []
        for device in self.client.installations:
            result.append(device["value"])
        return result

    def get_all_devices_serials(self):
        result = []
        for device in self.client.installations:
            result.append(device["label"])
        return result