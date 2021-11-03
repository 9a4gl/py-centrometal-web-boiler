# -*- coding: utf-8 -*-
"""
@author: Tihomir Heidelberg
"""

import logging
import sys
import argparse
import time

import urllib3
urllib3.disable_warnings()

from PelTecHttpClient import PelTecHttpClient
from PelTecWsClient import PelTecWsClient

class PelTecClient:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def login(self, username, password):
        self.logger.info("PelTecClient - Logging in...")
        self.username = username
        self.password = password
        self.http_client = PelTecHttpClient(self.username, self.password)
        return self.http_client.login()

    def start(self, serial):
        self.logger.info("PelTecClient - Starting...")
        self.serial = serial
        self.ws_client = PelTecWsClient(self.ws_connected_callback, self.ws_disconnected_callback, self.ws_error_callback, self.ws_data_callback)
        self.ws_client.start(serial)

    def ws_connected_callback(self):
        self.logger.info("PelTecClient - connected")
        self.http_client.get_notifications()
        self.http_client.get_data_installation()
        # not needed httpClient.get_widgetgrid_list()
        # not needed httpClient.get_widgetgrid()
        self.http_client.get_installation_status_all()
        self.http_client.get_parameter_list(self.serial)
        self.http_client.get_notifications()
        self.http_client.refresh()
        # not needed httpClient.control_advanced()
        self.http_client.rstat_all()

    def ws_disconnected_callback(self, close_status_code, close_msg):
        self.logger.warning(f"PelTecClient - disconnected close_status_code:{close_status_code} close_msg:{close_msg}")

    def ws_error_callback(self, err):
        self.logger.error(f"PelTecClient - error err:{err}")
    
    def ws_data_callback(self, msg):
        self.logger.info(f"PelTecClient - data:{msg}")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='PelTec.')
    parser.add_argument('--username', help='Username')
    parser.add_argument('--password', help='Password')
    parser.add_argument('--serial', help='Serial')
    args = parser.parse_args()
    if args.username == None or args.password == None or args.serial == None:
        parser.print_help()
    else:
        logging.basicConfig(
            level=logging.DEBUG,
            format="%(asctime)s [%(levelname)s] %(message)s",
            handlers=[ logging.StreamHandler()])
        testClient = PelTecClient()
        if not testClient.login(args.username, args.password):
            logging.error("Failed to login")
        else:
            testClient.start(args.serial)
            for i in range(0, 1000):
                time.sleep(1)
            logging.info("over")
