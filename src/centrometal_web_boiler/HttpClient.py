# -*- coding: utf-8 -*-
"""
@author: Tihomir Heidelberg
"""

import logging
import aiohttp
import json
import sys
import traceback
from lxml import html

from centrometal_web_boiler.const import WEB_BOILER_WEBROOT


class HttpClientBase:

    headers = {"Origin": WEB_BOILER_WEBROOT, "Referer": WEB_BOILER_WEBROOT + "/"}
    headers_json = {
        "Origin": WEB_BOILER_WEBROOT,
        "Referer": WEB_BOILER_WEBROOT + "/",
        "Content-Type": "application/json;charset=UTF-8",
    }

    def __init__(self, username, password):
        self.logger = logging.getLogger(__name__)
        self.username = username
        self.password = password
        self.parameter_list = dict()
        self.http_session = None
        self.http_session = aiohttp.ClientSession()

    async def reinitialize_session(self):
        await self.http_session.close()
        self.http_session = aiohttp.ClientSession()

    async def close_session(self):
        if self.http_session is not None:
            await self.http_session.close()

    async def _http_get(self, url, expected_code=200) -> html.HtmlElement:
        full_url = WEB_BOILER_WEBROOT + url
        self.logger.info(f"GET {full_url} ({self.username})")
        response = await self.http_session.get(
            full_url, headers=self.headers, ssl=False
        )
        if response.status != expected_code:
            raise Exception(
                f"HttpClientBase::__get {url} failed with http code: {response.status}"
            )
        responseText = await response.text()
        return html.fromstring(responseText)

    async def _http_post(self, url, data=None, expected_code=200) -> html.HtmlElement:
        full_url = WEB_BOILER_WEBROOT + url
        self.logger.info(f"POST {full_url} -> {data} ({self.username})")
        response = await self.http_session.post(
            full_url, headers=self.headers, data=data, ssl=False
        )
        if response.status != expected_code:
            raise Exception(
                f"HttpClientBase::__post {url} failed with http code: {response.status}"
            )
        try:
            responseText = await response.text()
            return html.fromstring(responseText)
        except:
            raise Exception(
                f"HttpClientBase::__post {url} failed to parse html content: {responseText}"
            )

    async def _http_post_json(self, url, data=None, expected_code=200) -> dict:
        full_url = WEB_BOILER_WEBROOT + url
        self.logger.info(f"POST-json {full_url} -> {data} ({self.username})")
        response = await self.http_session.post(
            full_url, headers=self.headers_json, data=data, ssl=False
        )
        if response.status != expected_code:
            raise Exception(
                f"HttpClientBase::_http_post_json {url} failed with http code: {response.status}"
            )
        try:
            responseText = await response.text()
            return json.loads(responseText)
        except:
            raise Exception(
                f"HttpClientBase::_http_post_json {url} failed to parse json content: {responseText}"
            )

    async def _control_multiple(self, data):
        response = await self._http_post_json(
            "/api/inst/control/multiple", data=json.dumps(data)
        )
        self.logger.info(f"Sending control multiple {data} ({self.username})")
        self.logger.info(f"Received response {{{json.dumps(response)}}} ({self.username})")
        return response

    async def _control(self, id, data):
        response = await self._http_post_json(
            "/api/inst/control/" + str(id), data=json.dumps(data)
        )
        self.logger.info(f"Sending control {data} ({self.username})")
        self.logger.info(f"Received response {{{json.dumps(response)}}} ({self.username})")
        return response

    async def _control_advanced(self, id, data):
        response = await self._http_post_json(
            "/api/inst/control/advanced/" + str(id), data=json.dumps(data)
        )
        self.logger.info(f"Sending control advanced {data} ({self.username})")
        self.logger.info(f"Received response {{{json.dumps(response)}}} ({self.username})")
        return response


class HttpClient(HttpClientBase):
    async def __get_csrf_token(self) -> None:
        self.logger.info(f"HttpClient - Fetching getCsrfToken ({self.username})")
        html_doc = await self._http_get("/login")
        input_element = html_doc.xpath('//input[@name="_csrf_token"]')
        if len(input_element) != 1:
            raise Exception("HttpClient::getCsrfToken failed - cannot find csrf token")
        values = input_element[0].xpath("@value")
        if len(values) != 1:
            raise Exception(
                "HttpClient::getCsrfToken  failed - cannot find csrf token vaue"
            )
        self.logger.info(f"HttpClient - csrf_token: {values[0]} ({self.username})")
        self.csrf_token = values[0]

    async def __login_check(self) -> None:
        self.logger.info(f"HttpClient - Logging in... ({self.username})")
        data = dict()
        data["_csrf_token"] = self.csrf_token
        data["_username"] = self.username
        data["_password"] = self.password
        data["submit"] = "Log In"
        html_doc = await self._http_post("/login_check", data=data)
        loading_div_element = html_doc.xpath('//div[@id="id-loading-screen-blackout"]')
        if len(loading_div_element) != 1:
            raise Exception("HttpClient::__loginCheck cannot find loading div element")
        self.logger.info(f"HttpClient - Login successfull ({self.username})")

    async def login(self) -> bool:
        try:
            await self.__get_csrf_token()
            await self.__login_check()
            return True
        except Exception as e:
            self.logger.error(str(e) + f" ({self.username})")
            exc_type, exc_value, exc_traceback = sys.exc_info()
            self.logger.error(
                " ".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
                + f" ({self.username})"
            )
            return False

    async def get_notifications(self) -> None:
        html_doc = await self._http_post("/notifications/data/get")

    async def get_installations(self):
        self.installations = await self._http_post_json(
            "/data/autocomplete/installation", data=json.dumps({})
        )
        self.installations = self.installations["installations"]
        self.logger.debug(
            "HttpClient::get_installations -> "
            + json.dumps(self.installations, indent=4)
            + f" ({self.username})"
        )

    async def get_configuration(self) -> None:
        self.configuration = await self._http_post_json(
            "/api/configuration", data=json.dumps({})
        )
        self.logger.debug(
            "HttpClient::get_configuration configuration -> "
            + json.dumps(self.configuration, indent=4)
            + f" ({self.username})"
        )

    async def get_widgetgrid_list(self) -> None:
        self.widgetgrid_list = await self._http_post_json(
            "/api/widgets-grid/list", data=json.dumps({})
        )

    async def get_widgetgrid(self, id):
        data = {"id": str(id), "inst": "null"}
        self.widgetgrid = await self._http_post_json(
            "/api/widgets-grid", data=json.dumps(data)
        )

    async def get_installation_status_all(self, ids: list) -> None:
        data = {"installations": ids}
        self.installation_status_all = await self._http_post_json(
            "/wdata/data/installation-status-all", data=json.dumps(data)
        )
        self.logger.debug(
            "HttpClient::get_installation_status_all -> "
            + json.dumps(self.installation_status_all, indent=4)
            + f" ({self.username})"
        )

    async def get_parameter_list(self, serial) -> None:
        self.parameter_list[serial] = await self._http_post_json(
            "/wdata/data/parameter-list/" + serial, data=json.dumps({})
        )
        self.logger.debug(
            "HttpClient::get_parameter_list -> "
            + json.dumps(self.parameter_list[serial], indent=4)
            + f" ({self.username})"
        )

    async def refresh_device(self, id) -> None:
        data = {"messages": {str(id): {"REFRESH": 0}}}
        return await self._control_multiple(data)

    async def rstat_all_device(self, id) -> None:
        data = {"messages": {str(id): {"RSTAT": "ALL"}}}
        return await self._control_multiple(data)

    async def get_table_data(self, id, tableStartIndex, tableSubIndex) -> None:
        params = {
            "PRD " + str(tableStartIndex): "VAL",
            "PRD " + str(tableStartIndex + tableSubIndex): "ALV",
        }
        data = {"parameters": params}
        return await self._control_advanced(id, data)

    def get_table_data_all(self, id, tableStartIndex, tableSize):
        tasks = []
        for i in range(1, tableSize + 1):
            tasks.append(self.get_table_data(id, tableStartIndex, i))
        return tasks

    async def turn_device_by_id(self, id, on):
        cmd_value = 1 if on else 0
        data = {"cmd-name": "CMD", "cmd-value": cmd_value}
        return await self._control(id, data)

    async def turn_device_circuit(self, id, circuit, on):
        cmd_name = "PWR " + str(circuit)
        cmd_value = 1 if on else 0
        data = {cmd_name: cmd_value}
        data = {"messages": {str(id): {cmd_name: cmd_value}}}
        return await self._control_multiple(data)
