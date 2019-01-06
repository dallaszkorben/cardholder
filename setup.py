from setuptools import setup, find_packages
from cardholder.setup.setup import getSetupIni

sp=getSetupIni()

setup(
      name=sp['name'],
      version=sp['version'],
      description='Rotary Card Holder GUI',
      long_description="Shows the constructed Cards overlapped like a Rotary Card Holder",	#=open('README.md', encoding="utf-8").read(),
      url='http://github.com/dallaszkorben/cardholder',
      author='dallaszkorben',
      author_email='dallaszkorben@gmail.com',
      license='MIT',
      classifiers =[
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
      ],
      packages = find_packages(),
      setup_requires=[ "pyqt5", "pyqt5-sip", "numpy", "pyttsx3", 'configparser'],
      install_requires=["pyqt5", 'pyqt5-sip', 'numpy','pyttsx3', 'configparser' ],
      package_data={
        'cardholder': ['setup/setup.ini'],
        'cardholder': ['img/*.png'],
        'cardholder': ['img/*.gif'],
      },
      include_package_data = True,
      zip_safe=False)