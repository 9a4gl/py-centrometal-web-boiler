# -*- coding: utf-8 -*-
"""
@author: Tihomir Heidelberg
"""

import logging

from peltec.PelTecHttpClient import PelTecHttpClient
from peltec.PelTecHttpHelper import PelTecHttpHelper
from peltec.PelTecWsClient import PelTecWsClient
from peltec.PelTecDeviceCollection import PelTecDeviceCollection

class PelTecClient:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.should_stop = False
    
    def login(self, username, password):
        self.logger.info("PelTecClient - Logging in...")
        self.username = username
        self.password = password
        self.http_client = PelTecHttpClient(self.username, self.password)
        self.http_helper = PelTecHttpHelper(self.http_client)
        self.data = PelTecDeviceCollection()
        return self.http_client.login()

    def get_configuration(self):
        self.http_client.getInstallations()
        if self.http_helper.getDeviceCount() == 0:
            self.logger.warning("PelTecClient - there is no installed device")
            return False
        self.http_client.getConfiguration()
        self.http_client.getWidgetgridList()
        self.http_client.getWidgetgrid(self.http_client.widgetgrid_list["selected"])
        self.http_client.getInstallationStatusAll(self.http_helper.getAllDevicesIds())
        for serial in self.http_helper.getAllDevicesSerials():
            self.http_client.getParameterList(serial)
        self.data.parseInstallations(self.http_client.installations)
        self.data.parseInstallationStatuses(self.http_client.installation_status_all)
        self.data.parseParameterLists(self.http_client.parameter_list)
        self.http_client.getNotifications()
        return True

    def start(self, on_parameter_updated_callback):
        self.logger.info("PelTecClient - Starting...")
        self.ws_client = PelTecWsClient(self.wsConnectedCallback, self.wsDisconnectedCallback, self.wsErrorCallback, self.wsDataCallback)
        self.on_parameter_updated_callback = on_parameter_updated_callback
        self.should_stop = False
        self.ws_client.start()

    def refresh(self):
        for id in self.http_helper.getAllDevicesIds():
            self.http_client.refreshDevice(id)
            self.http_client.rstatAllDevice(id)

    def wsConnectedCallback(self, ws, frame):
        self.logger.info("PelTecClient - connected")
        self.ws_client.subscribeToNotifications(ws)
        for serial in self.http_helper.getAllDevicesSerials():
            self.ws_client.subscribeToInstallation(ws, serial)
        for device in self.data.values():
            parameters = device["parameters"]
            for parameter in parameters.values():
                self.on_parameter_updated_callback(device, parameter, True)
        self.data.setOnUpdateCallback(self.on_parameter_updated_callback)
        self.refresh()

    def wsDisconnectedCallback(self, ws, close_status_code, close_msg):
        self.logger.warning(f"PelTecClient - disconnected close_status_code:{close_status_code} close_msg:{close_msg}")
        if not self.should_stop:
            self.logger.info("Webcocket reconnecting...")
            self.start(self.on_parameter_updated_callback)

    def wsErrorCallback(self, ws, err):
        self.logger.error(f"PelTecClient - error err:{err}")
    
    def wsDataCallback(self, ws, stomp_frame):        
        self.data.parseRealTimeFrame(stomp_frame)

    def stop(self):
        self.should_stop = True
        if self.ws_client:
            self.ws_client.close()
