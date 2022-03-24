"""
@author axiner
@version v1.0.0
@created 2022/1/18 21:05
@abstract web驱动
@description
@history
"""
import os
import re
import shutil
import sys
import typing as t
import urllib.request as urlrequest
import winreg
from pathlib import Path

from toollib.validator import choicer

try:
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.chromium.service import ChromiumService
    from selenium.webdriver.chromium.webdriver import ChromiumDriver
except ImportError:
    raise

__all__ = ['ChromeDriver']


class ChromeDriver(ChromiumDriver):
    """
    谷歌驱动（继承于selenium）
    - 可自动下载驱动（注：若指定目录存在与浏览器版本一致的驱动则会跳过）
    使用示例：
        # 1）不指定浏览器版本，则下载当前浏览器对应的版本（针对win平台）
        driver = ChromeDriver()
        driver.get('https://www.baidu.com/')
        # 2）指定对应版本
        driver = ChromeDriver(driver_dir='D:/tmp', version='96.0.4664.45')
        driver.get('https://www.baidu.com/')
        +++++[更多详见参数或源码]+++++
    """

    def __init__(self, driver_dir: t.Union[str, Path] = '.', version: str = 'LATEST_RELEASE',
                 platform: str = 'win', bit: int = 32,
                 port=0, options: Options = None,
                 service_args: t.List[str] = None, desired_capabilities=None,
                 service_log_path=None, env: dict = None, start_error_message: str = None,
                 service: ChromiumService = None, keep_alive=None):
        """
        谷歌驱动
        :param driver_dir: 驱动目录（默认当前执行目录）
        :param version: 版本（谷歌浏览器）
        :param platform: 平台（默认：win）- 支持：['win', 'mac', 'linux']
        :param bit: 位数（默认：32）- 支持：[32, 64]
        :param port:
        :param options:
        :param service_args:
        :param desired_capabilities:
        :param service_log_path:
        :param env:
        :param start_error_message:
        :param service:
        :param keep_alive:
        """
        if not service:
            if not start_error_message:
                start_error_message = 'Please see https://sites.google.com/a/chromium.org/chromedriver/home'
            driver_file = self.__download_driver(driver_dir, version, platform, bit)
            service = ChromiumService(
                driver_file, port, service_args, service_log_path, env, start_error_message)
        super(ChromeDriver, self).__init__(
            'chrome', 'goog', port, options, service_args,
            desired_capabilities, service_log_path, service, keep_alive)

    @classmethod
    def __download_driver(cls, driver_dir, version, platform, bit):
        driver_dir = Path(driver_dir).absolute()
        if driver_dir.is_file():
            raise TypeError('"driver_dir" is dir')
        else:
            driver_dir.mkdir(parents=True, exist_ok=True)
        platform = choicer(platform, choices=['win', 'mac', 'linux'], title='platform')
        if platform == 'win':
            version = cls.__get_version(version)
            executable_file = 'chromedriver.exe'
            bit = 32
        else:
            executable_file = 'chromedriver'
        driver_file = driver_dir.joinpath(executable_file)
        if driver_file.is_file():
            if cls.__check_driver_version(driver_file, version):
                return driver_file.as_posix()
        __version = cls.__find_similar_version(version)
        if not __version:
            raise ValueError('This version may not exist')
        __driver_zip = driver_dir.joinpath(f'chromedriver_{platform}{bit}.zip')
        __download_url = f'https://chromedriver.storage.googleapis.com/' \
                         f'{__version}/{__driver_zip.name}'
        try:
            sys.stdout.write(f'Download driver ({__driver_zip.stem}) start.....')
            urlrequest.urlretrieve(__download_url, __driver_zip.as_posix())
            shutil.unpack_archive(__driver_zip, driver_dir, 'zip')
            os.remove(__driver_zip)
            return driver_file.as_posix()
        except:
            raise

    @staticmethod
    def __find_similar_version(version):
        url = 'https://chromedriver.storage.googleapis.com/'
        if isinstance(version, str) and (version == "" or version.count('.') == 3):
            return version
        if version == 'LATEST_RELEASE':
            url += version
        sml_version = None
        try:
            version_resp = urlrequest.urlopen(url)
            html = version_resp.read().decode('utf8')
            if version == 'LATEST_RELEASE':
                sml_version = html
            else:
                pat = rf'<Key>({version}[\d.]*)/chromedriver_[\w.]+.zip</Key>'
                result = re.findall(pat, html)
                if result:
                    sml_version = max(result)
        finally:
            pass
        return sml_version

    @staticmethod
    def __get_version(version):
        if version != 'LATEST_RELEASE':
            return version
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r'Software\Google\Chrome\BLBeacon')
            value, _type = winreg.QueryValueEx(key, 'version')
            if value:
                version = value
        except:
            pass
        return version

    @staticmethod
    def __check_driver_version(driver_file, version):
        try:
            outstd = os.popen(f'{driver_file} --version').read()
            return outstd.split()[1] == version
        except:
            pass
