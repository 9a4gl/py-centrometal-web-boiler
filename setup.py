from setuptools import setup

setup(
   name='py-centrometal-web-boiler',
   version='0.0.50',
   description='Python library to interact with Centrometal Boiler System.',
   author='Tihomir Heidelberg',
   author_email='tihomir.heidelberg@lite.hr',
   packages=['centrometal_web_boiler'],
   url="https://github.com/9a4gl/py-centrometal-web-boiler",
   install_requires=[ "lxml>=4.9.1", "websockets>=10.3", "stomper>=0.4.3",
                      "aiohttp>=3.8.1", "cchardet>=2.1.7", "aiodns>=3.0.0"]
)
