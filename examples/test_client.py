import argparse
import time
import logging
import os

import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

import peltec

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
            def onParameterUpdated(device, param, create = False):
                action = "Create" if create else "update"
                serial = device["serial"]
                name = param["name"]
                value = param["value"]
                logging.info(f"{action} {serial} {name} = {value}")
            testClient.start(onParameterUpdated)
            while (True):
                time.sleep(1)
