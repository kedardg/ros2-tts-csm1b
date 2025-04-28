from setuptools import setup, find_packages
import os
from glob import glob

package_name = 'ros2_tts'

setup(
    name=package_name,
    version='0.0.1',
    packages=find_packages(),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'launch'), glob('ros2_tts/launch/*.launch.py')),
        (os.path.join('share', package_name, 'config'), ['settings.yaml']),
    ],
    install_requires=[
        'setuptools',
        'torch==2.4.0',
        'torchaudio==2.4.0',
        'numpy',
        'pyyaml',
        'huggingface_hub==0.28.1',
        'tokenizers==0.21.0',
        'transformers==4.49.0',
        'moshi==0.2.2',
        'torchtune==0.4.0',
        'torchao==0.9.0',
        'soundfile>=0.12.1',
        'librosa>=0.10.0',
        'silentcipher @ git+https://github.com/SesameAILabs/silentcipher.git@master#egg=silentcipher',
    ],
    zip_safe=True,
    maintainer='Your Name',
    maintainer_email='your.email@example.com',
    description='ROS2 Text-to-Speech package using CSM',
    license='Apache License 2.0',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'tts_node = ros2_tts.tts_node:main',
            'test_tts_node = ros2_tts.test_tts_node:main',
            'wav_publisher_node = ros2_tts.wav_publisher_node:main'
        ],
    },
) 