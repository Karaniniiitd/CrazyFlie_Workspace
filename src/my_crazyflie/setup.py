from setuptools import find_packages, setup

package_name = 'my_crazyflie'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='iiitd',
    maintainer_email='Jatin23260@iiitd.ac.in',
    description='TODO: Package description',
    license='TODO: License declaration',
    extras_require={
        'test': [
            'pytest',
        ],
    },
    entry_points={
        'console_scripts': [
            'takeoff          = my_crazyflie.takeoff:main',
            'land             = my_crazyflie.land:main',
            'arm              = my_crazyflie.arm:main',
            'emergency        = my_crazyflie.emergency:main',
            'sequence         = my_crazyflie.sequence:main',
            'go_to            = my_crazyflie.go_to:main',
            'velocity_control = my_crazyflie.velocity_control:main',
        ],
    },
)
