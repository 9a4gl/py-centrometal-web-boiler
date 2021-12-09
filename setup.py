from setuptools import setup

setup(
   name='py-peltec',
   version='0.0.27',
   description='Python library to interact with Centrometal Pel-Tec systems.',
   author='Tihomir Heidelberg',
   author_email='tihomir.heidelberg@lite.hr',
   packages=['peltec'],
   package_data={'peltec': ['certs.pem']},
   url="https://github.com/9a4gl/py-peltec",
   install_requires=[ "lxml>=4.6.4", "websockets>=9.1", "stomper>=0.4.3", "c-websockets>=2.1.3",
                      "aiohttp>=3.5.4", "cchardet>=2.1.7", "aiodns>=3.0.0"]
)
