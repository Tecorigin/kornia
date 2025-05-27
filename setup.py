from setuptools import setup, find_packages

setup(
    name='kornia',
    version='0.8.1',
    description='kornia',
    packages=find_packages(),
    include_package_data=True,
     install_requires=[
        "kornia_rs>=0.1.9",
        "packaging",
        "torch>=1.9.1",
    ],
    python_requires='>=3.8',
)


# python setup.py bdist_wheel
