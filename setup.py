from setuptools import setup

setup(
   name='py-peltec',
   version='0.0.3',
   description='Python library to interact with Centrometal Pel-Tec systems.',
   author='Tihomir Heidelberg',
   author_email='tihomir.heidelberg@lite.hr',
   packages=['peltec'],
   url="https://github.com/9a4gl/py-peltec",
   install_requires=[ "lxml>=4.6.4", "requests>=2.26.0", "urllib3>=1.26.7", "websocket-client>=1.2.1", "stomper>=0.4.3"]
   
)
