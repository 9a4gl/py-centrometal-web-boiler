from setuptools import setup

setup(
    name="py-centrometal-web-boiler",
    version="0.0.59",
    description="Python library to interact with Centrometal Boiler System.",
    author="Tihomir Heidelberg",
    author_email="tihomir.heidelberg@lite.hr",
    packages=[
        "centrometal_web_boiler",
        "centrometal_web_boiler.ws",
        "centrometal_web_boiler.ws.exceptions",
        "centrometal_web_boiler.ws.models",
        "centrometal_web_boiler.ws.utils",
        "centrometal_web_boiler.ws.wsprotocols",
    ],
    url="https://github.com/9a4gl/py-centrometal-web-boiler",
    install_requires=[
        "lxml>=6.1.3",
        "websockets>=17.4",
        "stomper>=0.4.3",
        "aiohttp>=3.14.5",
        "faust-cchardet>=3.2.0",
        "aiodns>=4.0.4",
        "pycares>=5.2.1",
    ],
)
