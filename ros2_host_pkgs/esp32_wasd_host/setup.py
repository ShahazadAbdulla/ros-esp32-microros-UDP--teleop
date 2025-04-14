from setuptools import setup
import os
from glob import glob

package_name = 'esp32_wasd_host' # Your package name

setup(
    name=package_name,
    version='0.0.0',
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        # If you add launch files later, uncomment the line below
        # (os.path.join('share', package_name, 'launch'), glob(os.path.join('launch', '*launch.[pxy][yma]*')))
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='Your Name', # <<< UPDATE THIS
    maintainer_email='your_email@example.com', # <<< UPDATE THIS
    description='Keyboard WASD node sending integer commands for ESP32 micro-ROS',
    license='Apache License 2.0', # Or your preferred license
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            # This creates the command 'wasd_teleop' that runs the main function in wasd.py
            'wasd_teleop = esp32_wasd_host.wasd:main',
        ],
    },
)