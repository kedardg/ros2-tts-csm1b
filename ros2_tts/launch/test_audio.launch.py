from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
import os

def generate_launch_description():
    return LaunchDescription([
        # TTS Node
        Node(
            package='ros2_tts',
            executable='tts_node',
            name='tts_node',
            output='screen'
        ),
        
        # WAV Publisher Node
        Node(
            package='ros2_tts',
            executable='wav_publisher_node',
            name='wav_publisher_node',
            parameters=[{
                'wav_file': '/ros2_ws/test_output/test_audio.wav',
                'topic': 'audio_output',
                'publish_rate': 0.2
            }],
            output='screen'
        )
    ]) 