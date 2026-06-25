from setuptools import setup, find_packages

setup(
    name='devpilot',
    version='1.0.0',
    packages=find_packages(),
    install_requires=[
        'google-genai',
        'python-dotenv',
        'colorama',
        'tenacity'
    ],
    entry_points={
        'console_scripts': [
            'devpilot=devpilot.cli:main',
        ],
    },
)