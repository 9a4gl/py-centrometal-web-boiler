# -*- coding: utf-8 -*-
"""
@author: Tihomir Heidelberg
"""

import PelTecHttpClient

class PelTecHttpHelper:
    def __init__(self, client : PelTecHttpClient):
        self.client = client
    
    def getDeviceCount(self):
        return len(self.client.installations)

    def getDevice(self, index):
        if index < self.getDeviceCount():
            return self.client.installations[index]
        raise Exception("PelTecHttpHelper:getDevice invalid index")

    def getDeviceById(self, id):
        for device in self.client.installations:
            if device["value"] == id:
                return device
        raise Exception("PelTecHttpHelper:getDeviceById invalid id")

    def getDeviceBySerial(self, serial):
        for device in self.client.installations:
            if device["label"] == serial:
                return device
        raise Exception("PelTecHttpHelper:getDeviceBySerial invalid serial")

    def getAllDevicesIds(self):
        result = []
        for device in self.client.installations:
            result.append(device["value"])
        return result

    def getAllDevicesSerials(self):
        result = []
        for device in self.client.installations:
            result.append(device["label"])
        return result