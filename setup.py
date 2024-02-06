from setuptools import setup, find_packages

name = 'py_bench'

setup(
    name=name,
    version=open(f'./{name}/_version.py').readline().split('=')[-1].strip(' \n"\''),
    description='py_bench: python benchmark tool',
    long_description='py_bench: python benchmark tool',
    author='1MrEnot',
    license='MIT License',
    packages=find_packages(exclude=["tests"]),
    include_package_data=True,
)
