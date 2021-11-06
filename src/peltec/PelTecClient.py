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

class PelTecClient:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def login(self, username, password):
        self.logger.info("PelTecClient - Logging in...")
        self.username = username
        self.password = password
        self.http_client = PelTecHttpClient(self.username, self.password)
        self.http_helper = PelTecHttpHelper(self.http_client)
        return self.http_client.login()

    def start(self):
        self.logger.info("PelTecClient - Starting...")
        self.ws_client = PelTecWsClient(self.ws_connected_callback, self.ws_disconnected_callback, self.ws_error_callback, self.ws_data_callback)
        self.ws_client.start()

    def ws_connected_callback(self, ws, frame):
        self.logger.info("PelTecClient - connected")
        self.http_client.get_notifications()
        self.http_client.get_installations()
        if self.http_helper.getDeviceCount() == 0:
            self.logger.warning("PelTecClient - there is no installed device")
            return
        self.http_client.get_configuration()
        # not needed httpClient.get_widgetgrid_list()
        # not needed httpClient.get_widgetgrid(37144)
        self.http_client.get_installation_status_all(self.http_helper.getAllDevicesIds())
        for serial in self.http_helper.getAllDevicesSerials():
            self.ws_client.subscribeToInstallation(ws, serial)
            self.http_client.get_parameter_list(serial)
        self.http_client.get_notifications()
        for id in self.http_helper.getAllDevicesIds():
            self.http_client.refresh(id)
            # not needed httpClient.control_advanced(id)
            self.http_client.rstat_all(id)

    def ws_disconnected_callback(self, ws, close_status_code, close_msg):
        self.logger.warning(f"PelTecClient - disconnected close_status_code:{close_status_code} close_msg:{close_msg}")

    def ws_error_callback(self, ws, err):
        self.logger.error(f"PelTecClient - error err:{err}")
    
    def ws_data_callback(self, ws, msg):
        self.logger.info(f"PelTecClient - data:{msg}")

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
            testClient.start()
            for i in range(0, 1000):
                time.sleep(1)
            logging.info("over")
