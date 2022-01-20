import argparse
import logging
import os
import asyncio
import json

import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

import centrometal_web_boiler

loop = None
testClient = None

async def on_parameter_updated(device, param, create = False):
    action = "Create" if create else "update"
    serial = device["serial"]
    name = param["name"]
    value = param["value"]
    logging.info(f"{action} {serial} {name} = {value}")

async def connectivity_callback(connected: bool):
    global loop
    global testClient
    if connected:
        asyncio.ensure_future(testClient.refresh(), loop=loop)

async def test_relogin():
    global loop
    global testClient
    while (True):
        await asyncio.sleep(50)
        await testClient.refresh()
        await asyncio.sleep(50)
        relogined = await testClient.relogin()
        if not relogined:
            logging.info("Failed to relogin")
            return
        await testClient.close_websocket()
        await testClient.start_websocket(on_parameter_updated)
        await asyncio.sleep(5)
        break

async def test_off_on():
    global loop
    global testClient
    for i in range(0, 5):
        await asyncio.sleep(1)
    print("Turning off")
    for serial in testClient.data.keys():
        await testClient.turn(serial, False)
    for i in range(0, 10):
        await asyncio.sleep(1)
    print("Turning on")
    for serial in testClient.data.keys():
        await testClient.turn(serial, True)
    for i in range(0, 10):
        await asyncio.sleep(1)
    sys.exit(0)

async def test_circuit_off_on(circuit):
    global loop
    global testClient
    for i in range(0, 5):
        await asyncio.sleep(1)
    print("Turning circuit off")
    for serial in testClient.data.keys():
        await testClient.turn_circuit(serial, circuit, False)
    for i in range(0, 10):
        await asyncio.sleep(1)
    print("Turning on")
    for serial in testClient.data.keys():
        await testClient.turn_circuit(serial, circuit, True)
    for i in range(0, 10):
        await asyncio.sleep(1)
    sys.exit(0)

async def main(username, password):
    global loop
    global testClient
    loop = asyncio.get_running_loop()
    testClient = centrometal_web_boiler.WebBoilerClient()
    testClient.set_connectivity_callback(connectivity_callback)

    loggedIn = await testClient.login(username, password)
    if not loggedIn:
        logging.error("Failed to login")
        return
    
    gotConfiguration = await testClient.get_configuration()
    if not gotConfiguration:
        logging.error("Failed to get configuration")
        return

    await testClient.start_websocket(on_parameter_updated)

    for device in testClient.data.values():
        widget = device.get_widget_by_template("v3.timetable")
        print(json.dumps(widget, indent=4))

    # await test_relogin()
    # await test_off_on()
    # await test_circuit_off_on(72)
    await asyncio.sleep(5000)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='WebBoiler.')
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
        
        loop = asyncio.get_event_loop()
        loop.run_until_complete(main(args.username, args.password))

