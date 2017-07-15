from setuptools import setup, find_packages

setup(
    name='editor5',
    version='0.1',
    py_modules='editor5',
    install_requires=[
        'Click',
    ],
    entry_points='''
        [console_scripts]
        e5=editor5.e5:cli
    ''',
)
