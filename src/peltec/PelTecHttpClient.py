# -*- coding: utf-8 -*-
"""
@author: Tihomir Heidelberg
"""

import logging
import requests
import json
from lxml import html

from const import PELTEC_WEBROOT

class PelTecHttpClient:

    def __init__(self, username, password):
        self.logger = logging.getLogger(__name__)
        self.username = username
        self.password = password
        self.http_session = requests.Session()
        self.headers = { 
            "Origin": PELTEC_WEBROOT,
            "Referer": PELTEC_WEBROOT + "/" }
        self.headers_json = { 
            "Origin": PELTEC_WEBROOT,
            "Referer": PELTEC_WEBROOT + "/",
            "Content-Type": "application/json;charset=UTF-8" }

    def __get_csrf_token(self):
        self.logger.info("PelTecHttpClient - Fetching get_csrf_token")
        response = self.http_session.get(PELTEC_WEBROOT + "/login", verify=False)
        if response.status_code != 200:
            self.logger.error(f"PelTecHttpClient::__get_csrf_token failed with http code: {response.status_code}")
            return False
        html_doc = html.fromstring(response.text)
        input_element = html_doc.xpath("//input[@name=\"_csrf_token\"]")
        if len(input_element) != 1:
            self.logger.error("PelTecHttpClient::__get_csrf_token failed - cannot find csrf token")
            return False
        values = input_element[0].xpath('@value')
        if len(values) != 1:
            self.logger.error("PelTecHttpClient::__get_csrf_token  failed - cannot find csrf token vaue")
            return False
        self.logger.info(f"PelTecHttpClient - csrf_token: {values[0]}")
        return values[0]

    def __login_check(self):
        self.logger.info("PelTecHttpClient - Logging in...")
        data = dict()
        data["_csrf_token"] = self.csrf_token
        data["_username"] = self.username
        data["_password"] = self.password
        data["submit"] = "Log In"
        response = self.http_session.post(
            PELTEC_WEBROOT + '/login_check', 
            data = data, headers=self.headers, verify=False)
        if response.status_code != 200:
            self.logger.error(f"PelTecHttpClient::__login_check failed with http code: {response.status_code}")
            return False
        html_doc = html.fromstring(response.text)
        loading_div_element = html_doc.xpath("//div[@id=\"id-loading-screen-blackout\"]")
        if len(loading_div_element) != 1:
            self.logger.error("PelTecHttpClient::__login_check cannot find loading div element")
            return False
        self.logger.info("PelTecHttpClient - Login successfull")
        return True

    def login(self):
        self.csrf_token = self.__get_csrf_token()
        if self.csrf_token == False:
            return
        return self.__login_check()

    def get_notifications(self):
        response = self.http_session.post(
            PELTEC_WEBROOT + '/notifications/data/get', 
            headers=self.headers, verify=False)
        if response.status_code != 200:
            self.logger.error(f"PelTecHttpClient::get_notifications failed with http code: {response.status_code}")
            return False
        return True

    def get_data_installation(self):
        response = self.http_session.post(
            PELTEC_WEBROOT + '/data/autocomplete/installation', 
            data = json.dumps({}), headers=self.headers_json, verify=False)
        if response.status_code != 200:
            self.logger.error(f"PelTecHttpClient::get_data_installation failed with http code: {response.status_code}")
            return False
        self.data_installation = json.loads(response.text)
        self.logger.info("PelTecHttpClient::get_data_installation -> " + json.dumps(self.data_installation, indent=4))
        # TODO parse data installation
        return True

    def get_configuration(self):
        response = self.http_session.post(
            PELTEC_WEBROOT + '/api/configuration', 
            data = json.dumps({}), headers=self.headers_json, verify=False)
        if response.status_code != 200:
            self.logger.error(f"PelTecHttpClient::get_configuration failed with http code: {response.status_code}")
            return False
        self.configuration = json.loads(response.text)
        self.logger.info("PelTecHttpClient::get_configuration configuration -> " + json.dumps(self.configuration, indent=4))
        # TODO parse configuration
        return True
        
    # TODO remove if not needed
    def get_widgetgrid_list(self):
        response = self.http_session.post(
            PELTEC_WEBROOT + '/api/widgets-grid/list', 
            data = json.dumps({}), headers=self.headers_json, verify=False)
        if response.status_code != 200:
            self.logger.error(f"PelTecHttpClient::get_widgetgrid_list failed with http code: {response.status_code}")
            return False
        self.widgetgrid_list = json.loads(response.text)
        return True

    # TODO remove if not needed
    def get_widgetgrid(self):
        data = { "id": "37144", "inst": "null" }
        response = self.http_session.post(
            PELTEC_WEBROOT + '/api/widgets-grid', 
            data = json.dumps(data), headers=self.headers_json, verify=False)
        if response.status_code != 200:
            self.logger.error(f"PelTecHttpClient::get_widgetgrid failed with http code: {response.status_code}")
            return False
        self.widgetgrid = json.loads(response.text)
        return True

    def get_installation_status_all(self):
        data = { "installations": [ 2719 ]}
        response = self.http_session.post(
            PELTEC_WEBROOT + '/wdata/data/installation-status-all', 
            data = json.dumps(data), headers=self.headers_json, verify=False)
        if response.status_code != 200:
            self.logger.error(f"PelTecHttpClient::get_installation_status_all failed with http code: {response.status_code}")
            return False
        self.installation_status_all = json.loads(response.text)
        self.logger.info("PelTecHttpClient::get_installation_status_all -> " + json.dumps(self.installation_status_all, indent=4))
        # TODO parse
        return True

    def get_parameter_list(self, serial):
        response = self.http_session.post(
            PELTEC_WEBROOT + '/wdata/data/parameter-list/' + serial, 
            data = json.dumps({}), headers=self.headers_json, verify=False)
        if response.status_code != 200:
            self.logger.error(f"PelTecHttpClient::get_parameter_list failed with http code: {response.status_code}")
            return False
        self.parameter_list = json.loads(response.text)
        self.logger.info("PelTecHttpClient::get_parameter_list -> " + json.dumps(self.parameter_list, indent=4))
        # TODO parse
        return True

    def __control(self, data):
        response = self.http_session.post(
            PELTEC_WEBROOT + '/api/inst/control/multiple', 
            data = json.dumps(data), headers=self.headers_json, verify=False)
        if response.status_code != 200:
            self.logger.error(f"PelTecHttpClient::__control send failed with http code: {response.status_code} - data: {data}")
            return False
        self.logger.info(f"Sending command {data}")
        self.logger.info(f"Received response {response.text}\n")
        return True

    def refresh(self):
        data = { 'messages': { '2719': { 'REFRESH': 0 } } }
        return self.__control(data)
    
    def rstat_all(self):
        data = { 'messages': { '2719': { 'RSTAT': "ALL" } } }
        return self.__control(data)

    # TODO do we need this?
    def control_advanced(self, id ="2719"):
        data = { "parameters": { "PRD 222": "VAL", "PRD 223": "ALV" } }
        response = self.http_session.post(
            PELTEC_WEBROOT + '/api/inst/control/advanced/' + id, 
            data = json.dumps(data), headers=self.headers_json, verify=False)
        if response.status_code != 200:
            self.logger.error(f"PelTecHttpClient::control_advanced sending advanced control failed with http code: {response.status_code}")
            return False
        self.logger.info("Sending advanced command {data}")
        self.logger.info("Received advanced response {response.text}\n")
        return True
