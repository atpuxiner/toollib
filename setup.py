"""
@author axiner
@version v1.0.0
@created 2021/12/12 13:14
@abstract
@description
@history
"""
import os
import sys
from shutil import rmtree

from pkg_resources import yield_lines
from setuptools import Command, setup

from versions import Versions


here = os.path.abspath(os.path.dirname(__file__))

with open("README.md", "r", encoding="utf8") as f:
    long_description = f.read()
with open(os.path.join(here, "requirements.txt"), "r", encoding="utf8") as f:
    install_requires = list(yield_lines(f.read()))


def bu():
    """build"""
    try:
        print("Removing previous builds...")
        rmtree(os.path.join(here, "dist"))
    except OSError:
        pass
    print("Building Source or Wheel distribution...")
    # os.system("{0} setup.py sdist bdist_wheel".format(sys.executable))
    os.system("{0} setup.py bdist_wheel".format(sys.executable))


class BuildCommand(Command):
    """support setup.py build"""
    description = "Build the package."
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        bu()
        sys.exit()


class UploadCommand(Command):
    """support setup.py build&upload"""
    description = "Build and upload the package."
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        bu()
        print("Uploading the package to PyPI via Twine...")
        os.system("twine upload dist/*")
        sys.exit()


setup(
    version=Versions.ALL[0][0],
    long_description=long_description,
    long_description_content_type="text/markdown",
    install_requires=install_requires,
    cmdclass={
        "bu": BuildCommand,
        "up": UploadCommand,
    },
)
