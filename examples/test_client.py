import argparse
import time
import logging
import os

import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

import peltec

def test_relogin(testClient):
    while (True):
        for i in range(0, 10):
            time.sleep(1)
        testClient.refresh()
        for i in range(0, 10):
            time.sleep(1)
        if testClient.relogin():
            testClient.close_websocket()
            testClient.start_websocket(on_parameter_updated, False)
        else:
            logging.info("Failed to relogin")
            sys.exit(0)

def test_off_on(testClient):
    for i in range(0, 5):
        time.sleep(1)
    print("Turning off")
    for serial in testClient.data.keys():
        testClient.turn(serial, False)
    for i in range(0, 10):
        time.sleep(1)
    print("Turning on")
    for serial in testClient.data.keys():
        testClient.turn(serial, True)
    for i in range(0, 10):
        time.sleep(1)
    sys.exit(0)

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
        
        testClient = peltec.PelTecClient()
        if not testClient.login(args.username, args.password):
            logging.error("Failed to login")
        elif not testClient.get_configuration():
            logging.error("Failed to get configuration")
        else:
            def on_parameter_updated(device, param, create = False):
                action = "Create" if create else "update"
                serial = device["serial"]
                name = param["name"]
                value = param["value"]
                logging.info(f"{action} {serial} {name} = {value}")
            testClient.start_websocket(on_parameter_updated, False)
            # test_relogin(testClient)
            test_off_on(testClient)

