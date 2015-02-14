#!/usr/bin/env python3
"""Setup module."""
from setuptools import setup, find_packages
import os


def read(fname):
    """Read and return the contents of a file."""
    return open(os.path.join(os.path.dirname(__file__), fname)).read()


setup(
    name='macmond',
    version='0.0.1',
    description='MACMond - MAC address Monitoring daemon.',
    long_description=read('README'),
    author='Kalman Olah',
    author_email='hello@kalmanolah.net',
    url='https://github.io/kalmanolah/macmond',
    license='MIT',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Environment :: Console',
        'Environment :: No Input/Output (Daemon)',
        'Intended Audience :: System Administrators',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
    ],

    packages=find_packages(),
    entry_points={
        'console_scripts': [
            'macmond = macmond:macmond',
        ],
    },

    install_requires=[
        'scapy-python3',
        'python-daemon',
        'netifaces',
        'click'
    ],
    dependency_links=[
    ],
)
