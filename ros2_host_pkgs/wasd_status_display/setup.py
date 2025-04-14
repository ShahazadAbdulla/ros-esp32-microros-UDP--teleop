from setuptools import setup

package_name = 'wasd_status_display' # Package name

setup(
    name=package_name,
    version='0.0.0',
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='Your Name', # UPDATE
    maintainer_email='your_email@example.com', # UPDATE
    description='Displays textual status received from ESP32 micro-ROS node.',
    license='Apache License 2.0', # Or your preferred license
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
             # Executable name 'status_display' runs main in status_display_node.py
             'status_display = wasd_status_display.status_display_node:main',
        ],
    },
)