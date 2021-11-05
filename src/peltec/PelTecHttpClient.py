# -*- coding: utf-8 -*-
"""
@author: Tihomir Heidelberg
"""

import logging
import requests
import json
import os
import sys
import traceback
from lxml import html

from const import PELTEC_WEBROOT, PELTEC_WEB_CERTIFICATE_FILE

class PelTecHttpClient:

    headers = { "Origin": PELTEC_WEBROOT, "Referer": PELTEC_WEBROOT + "/" }    
    headers_json = { "Origin": PELTEC_WEBROOT, "Referer": PELTEC_WEBROOT + "/", "Content-Type": "application/json;charset=UTF-8" }

    def __init__(self, username, password):
        self.logger = logging.getLogger(__name__)
        self.username = username
        self.password = password
        self.http_session = requests.Session()
        self.http_session.verify = PELTEC_WEB_CERTIFICATE_FILE

    def __http_get(self, url, expected_code = 200) -> html.HtmlElement:
        response = self.http_session.get(PELTEC_WEBROOT + url, headers = self.headers)
        if response.status_code != expected_code:
            raise Exception(f"PelTecHttpClient::__get {url} failed with http code: {response.status_code}")
        return html.fromstring(response.text)

    def __http_post(self, url, data = None, expected_code = 200) -> html.HtmlElement:
        response = self.http_session.post(PELTEC_WEBROOT + url, headers = self.headers, data = data)
        if response.status_code != expected_code:
            raise Exception(f"PelTecHttpClient::__post {url} failed with http code: {response.status_code}")
        return html.fromstring(response.text)

    def __http_post_json(self, url, data = None, expected_code = 200) -> dict:
        response = self.http_session.post(PELTEC_WEBROOT + url, headers = self.headers_json, data = data)
        if response.status_code != expected_code:
            raise Exception(f"PelTecHttpClient::__post {url} failed with http code: {response.status_code}")
        return json.loads(response.text)

    def __get_csrf_token(self) -> None:        
        self.logger.info("PelTecHttpClient - Fetching get_csrf_token")
        html_doc = self.__http_get("/login")
        input_element = html_doc.xpath("//input[@name=\"_csrf_token\"]")
        if len(input_element) != 1:
            raise Exception("PelTecHttpClient::__get_csrf_token failed - cannot find csrf token")
        values = input_element[0].xpath('@value')
        if len(values) != 1:
            raise Exception("PelTecHttpClient::__get_csrf_token  failed - cannot find csrf token vaue")
        self.logger.info(f"PelTecHttpClient - csrf_token: {values[0]}")
        self.csrf_token = values[0]

    def __login_check(self) -> None:
        self.logger.info("PelTecHttpClient - Logging in...")
        data = dict()
        data["_csrf_token"] = self.csrf_token
        data["_username"] = self.username
        data["_password"] = self.password
        data["submit"] = "Log In"
        html_doc = self.__http_post('/login_check', data=data)
        loading_div_element = html_doc.xpath("//div[@id=\"id-loading-screen-blackout\"]")
        if len(loading_div_element) != 1:
            raise Exception("PelTecHttpClient::__login_check cannot find loading div element")
        self.logger.info("PelTecHttpClient - Login successfull")

    def login(self) -> bool:
        try:
            self.__get_csrf_token()
            self.__login_check()
            return True
        except Exception as e:
            self.logger.error(str(e))
            exc_type, exc_value, exc_traceback = sys.exc_info()
            self.logger.error(" " . join(traceback.format_exception(exc_type, exc_value, exc_traceback)))
            return False

    def get_notifications(self) -> None:
        html_doc = self.__http_post("/notifications/data/get")

    def get_data_installation(self):
        self.data_installation = self.__http_post_json("/data/autocomplete/installation", data=json.dumps({}))
        self.logger.info("PelTecHttpClient::get_data_installation -> " + json.dumps(self.data_installation, indent=4))
        # TODO parse data installation

    def get_configuration(self) -> None:
        self.configuration = self.__http_post_json('/api/configuration', data=json.dumps({}))
        self.logger.info("PelTecHttpClient::get_configuration configuration -> " + json.dumps(self.configuration, indent=4))
        # TODO parse configuration
        
    # TODO remove if not needed
    def get_widgetgrid_list(self) -> None:
        self.widgetgrid_list = self.__http_post_json('/api/widgets-grid/list', data=json.dumps({}))

    # TODO remove if not needed
    def get_widgetgrid(self):
        data = { "id": "37144", "inst": "null" }
        self.widgetgrid = self.__http_post_json('/api/widgets-grid', data=json.dumps(data))

    def get_installation_status_all(self) -> None:
        data = { "installations": [ 2719 ]}
        self.installation_status_all = self.__http_post_json('/wdata/data/installation-status-all', data=json.dumps(data))
        self.logger.info("PelTecHttpClient::get_installation_status_all -> " + json.dumps(self.installation_status_all, indent=4))
        # TODO parse

    def get_parameter_list(self, serial) -> None:
        self.parameter_list = self.__http_post_json('/wdata/data/parameter-list/' + serial, data=json.dumps({}))
        self.logger.info("PelTecHttpClient::get_parameter_list -> " + json.dumps(self.parameter_list, indent=4))
        # TODO parse

    def __control(self, data) -> None:
        response = self.__http_post_json('/api/inst/control/multiple', data=json.dumps(data))
        self.logger.info(f"Sending command {data}")
        self.logger.info(f"Received response {{{json.dumps(response)}}}\n")

    def refresh(self) -> None:
        data = { 'messages': { '2719': { 'REFRESH': 0 } } }
        self.__control(data)
    
    def rstat_all(self) -> None:
        data = { 'messages': { '2719': { 'RSTAT': "ALL" } } }
        self.__control(data)

    # TODO do we need this?
    def control_advanced(self, id ="2719") -> None: # TODO replace all 2719 with installation id
        data = { "parameters": { "PRD 222": "VAL", "PRD 223": "ALV" } }
        response = self.__http_post_json('/api/inst/control/advanced/' + id, data=json.dumps(data))
        self.logger.info("Sending advanced command {data}")
        self.logger.info("Received advanced response {{{json.dumps(response)}}}\n")
