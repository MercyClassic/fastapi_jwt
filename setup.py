from setuptools import setup, find_packages

VERSION = '1.0.0'


setup(
    name='fastapi_jwt',
    version=VERSION,
    packages=find_packages(),
    package_dir={'fastapi_jwt': 'fastapi_jwt'},
    license='Creative Commons Attribution-Noncommercial-Share Alike license',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    url='https://github.com/MercyClassic/fastapi_jwt',
    author='MercyClassic',
    requires=['PyJWT'],  # SQLAlchemy/redis
)
