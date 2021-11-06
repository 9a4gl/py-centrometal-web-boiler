# -*- coding: utf-8 -*-
"""
@author: Tihomir Heidelberg
"""

import logging
import requests
import json
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
        self.parameter_list = dict()

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

    def get_installations(self):
        self.installations = self.__http_post_json("/data/autocomplete/installation", data=json.dumps({}))
        self.installations = self.installations["installations"]
        self.logger.debug("PelTecHttpClient::get_installations -> " + json.dumps(self.installations, indent=4))

    def get_configuration(self) -> None:
        self.configuration = self.__http_post_json('/api/configuration', data=json.dumps({}))
        self.logger.debug("PelTecHttpClient::get_configuration configuration -> " + json.dumps(self.configuration, indent=4))
        
    def get_widgetgrid_list(self) -> None:
        self.widgetgrid_list = self.__http_post_json('/api/widgets-grid/list', data=json.dumps({}))

    def get_widgetgrid(self, id):
        data = { "id": str(id), "inst": "null" }
        self.widgetgrid = self.__http_post_json('/api/widgets-grid', data=json.dumps(data))

    def get_installation_status_all(self, ids : list) -> None:
        data = { "installations": ids }
        self.installation_status_all = self.__http_post_json('/wdata/data/installation-status-all', data=json.dumps(data))
        self.logger.debug("PelTecHttpClient::get_installation_status_all -> " + json.dumps(self.installation_status_all, indent=4))

    def get_parameter_list(self, serial) -> None:
        self.parameter_list[serial] = self.__http_post_json('/wdata/data/parameter-list/' + serial, data=json.dumps({}))
        self.logger.debug("PelTecHttpClient::get_parameter_list -> " + json.dumps(self.parameter_list[serial], indent=4))

    def __control(self, data) -> None:
        response = self.__http_post_json('/api/inst/control/multiple', data=json.dumps(data))
        self.logger.info(f"Sending command {data}")
        self.logger.info(f"Received response {{{json.dumps(response)}}}")

    def refresh(self, id) -> None:
        data = { 'messages': { str(id): { 'REFRESH': 0 } } }
        self.__control(data)
    
    def rstat_all(self, id) -> None:
        data = { 'messages': { str(id): { 'RSTAT': "ALL" } } }
        self.__control(data)

    def __control_advanced(self, id, params) -> None:
        data = { "parameters": params }
        response = self.__http_post_json('/api/inst/control/advanced/' + str(id), data=json.dumps(data))
        self.logger.info("Sending advanced command {data}")
        self.logger.info("Received advanced response {{{json.dumps(response)}}}")

    def get_active_table(self, id) -> None:
        if "grid" in self.widgetgrid:
            grid = json.loads(self.widgetgrid["grid"])
            if "widgets" in grid:
                widgets2 = grid["widgets2"]
                if len(widgets2) > 0:
                    for widget2 in widgets2:
                        template = widget2["template"]
                        if template == "v3.timetable":
                            data = widget2["data"]
                            activeTable = data["activeTable"]
                            table = data["table"]
                            params = { "PRD " + str(activeTable): "VAL", "PRD " +str (table): "ALV" }
                            self.__control_advanced(id, params)