"""Setup for uploadfile XBlock."""


import os

from setuptools import setup


def package_data(pkg, roots):
    """Generic function to find package_data.

    All of the files under each of the `roots` will be declared as package
    data for package `pkg`.

    """
    data = []
    for root in roots:
        for dirname, _, files in os.walk(os.path.join(pkg, root)):
            for fname in files:
                data.append(os.path.relpath(os.path.join(dirname, fname), pkg))

    return {pkg: data}


setup(
    name='xblock-uploadfile',
    version='1.1',
    description='Upload File XBlock for prompting and uploading files that are stored as responses',
    license='Apache 2.0',
    packages=[
        'uploadfile'
    ],
    install_requires=[
        'XBlock',
    ],
    entry_points={
        'xblock.v1': [
            'uploadfile = uploadfile:UploadFileBlock',
        ]
    },
    package_data=package_data("uploadfile", ["static", "public"]),
)
