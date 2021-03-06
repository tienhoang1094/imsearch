import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name='imsearch',
    version='0.1.0',
    description='A generic framework to build your own reverse image search engine',
    long_description=long_description,
    long_description_content_type="text/markdown",
    url='https://github.com/rikenmehta03/imsearch',
    author='Riken Mehta',
    author_email='riken.mehta03@gmail.com',
    packages=setuptools.find_packages(),
    install_requires=['keras-retinanet', 'pandas', 'redis', 'pymongo', 'nmslib'],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: Apache License 2.0",
        "Operating System :: Linux",
    ]
)
