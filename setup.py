from setuptools import setup

requirements = ['click', 'boto3']

setup(
    name='meter',
    author="Karl Gutwin",
    author_email='karl@gutwin.org',
    description='IOT Meter CLI',
    packages=['meter'],
    entry_points={
        'console_scripts': ['meter=meter.cli:main']
    },
    python_requires='>=3.7',
    install_requires=requirements,
)
