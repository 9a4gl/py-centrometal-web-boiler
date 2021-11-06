# -*- coding: utf-8 -*-
"""
@author: Tihomir Heidelberg
"""

import logging
import argparse
import time

from PelTecHttpClient import PelTecHttpClient
from PelTecHttpHelper import PelTecHttpHelper
from PelTecWsClient import PelTecWsClient
from PelTecDeviceCollection import PelTecDeviceCollection

class PelTecClient:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def login(self, username, password):
        self.logger.info("PelTecClient - Logging in...")
        self.username = username
        self.password = password
        self.http_client = PelTecHttpClient(self.username, self.password)
        self.http_helper = PelTecHttpHelper(self.http_client)
        self.data = PelTecDeviceCollection()
        return self.http_client.login()

    def start(self, on_started_callback):
        self.logger.info("PelTecClient - Starting...")
        self.ws_client = PelTecWsClient(self.wsConnectedCallback, self.wsDisconnectedCallback, self.wsErrorCallback, self.wsDataCallback)
        self.on_started_callback = on_started_callback
        self.ws_client.start()

    def wsConnectedCallback(self, ws, frame):
        self.logger.info("PelTecClient - connected")
        self.http_client.getInstallations()
        if self.http_helper.getDeviceCount() == 0:
            self.logger.warning("PelTecClient - there is no installed device")
            return
        self.http_client.getConfiguration()
        self.http_client.getWidgetgridList()
        self.http_client.getWidgetgrid(self.http_client.widgetgrid_list["selected"])
        self.http_client.getInstallationStatusAll(self.http_helper.getAllDevicesIds())
        for serial in self.http_helper.getAllDevicesSerials():
            self.ws_client.subscribeToInstallation(ws, serial)
            self.http_client.getParameterList(serial)
        self.data.parseInstallations(self.http_client.installations)
        self.data.parseInstallationStatuses(self.http_client.installation_status_all)
        self.data.parseParameterLists(self.http_client.parameter_list)
        self.http_client.getNotifications()
        self.on_started_callback()

    def refresh(self):
        for id in self.http_helper.getAllDevicesIds():
            self.http_client.refreshDevice(id)
            self.http_client.rstatAllDevice(id)

    def wsDisconnectedCallback(self, ws, close_status_code, close_msg):
        self.logger.warning(f"PelTecClient - disconnected close_status_code:{close_status_code} close_msg:{close_msg}")

    def wsErrorCallback(self, ws, err):
        self.logger.error(f"PelTecClient - error err:{err}")
    
    def wsDataCallback(self, ws, stomp_frame):        
        self.data.parseRealTimeFrame(stomp_frame)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='PelTec.')
    parser.add_argument('--username', help='Username')
    parser.add_argument('--password', help='Password')
    args = parser.parse_args()
    if args.username == None or args.password == None:
        parser.print_help()
    else:
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s [%(levelname)s] %(message)s",
            handlers=[ logging.StreamHandler()])
        logging.captureWarnings(True)
        testClient = PelTecClient()
        if not testClient.login(args.username, args.password):
            logging.error("Failed to login")
        else:
            def onParameterUpdated(device, param):
                serial = device["serial"]
                name = param["name"]
                value = param["value"]
                logging.info(f"Updated {serial} {name} = {value}")
            def onStarted():
                for serial, device in testClient.data.items():
                    parameters = device["parameters"]
                    for parameter_name, parameter in parameters.items():
                        onParameterUpdated(device, parameter)
                testClient.refresh()
            testClient.data.setOnUpdateCallback(onParameterUpdated)
            testClient.start(onStarted)
            
            while (True):
                time.sleep(1)
