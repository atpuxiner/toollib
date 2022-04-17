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
        # 1）不指定浏览器版本，则下载当前浏览器对应的版本（针对win平台，mac|linux则下载最新版本）
        driver = ChromeDriver()
        driver.get('https://www.baidu.com/')
        # 2）指定浏览器版本（版本号可在浏览器中查看）（注：driver_dir为驱动器存放目录，可自定义）
        driver = ChromeDriver(driver_dir='D:/tmp', version='96.0.4664.45')
        driver.get('https://www.baidu.com/')
        +++++[更多详见参数或源码]+++++
    """

    def __init__(self, driver_dir: t.Union[str, Path] = '.', version: str = 'LATEST_RELEASE',
                 platform: str = 'win64',
                 port=0, options: Options = None,
                 service_args: t.List[str] = None, desired_capabilities=None,
                 service_log_path=None, env: dict = None, start_error_message: str = None,
                 service: ChromiumService = None, keep_alive=None):
        """
        谷歌驱动
        :param driver_dir: 驱动目录（默认当前执行目录）
        :param version: 版本（谷歌浏览器）
        :param platform: 平台（默认：win64）-支持：['win32', 'win64', 'mac64', 'linux64']
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
            executable_path = self.__download_driver(driver_dir, version, platform)
            service = ChromiumService(
                executable_path, port, service_args, service_log_path, env, start_error_message)
        super(ChromeDriver, self).__init__(
            'chrome', 'goog', port, options, service_args,
            desired_capabilities, service_log_path, service, keep_alive)

    @classmethod
    def __download_driver(cls, driver_dir: str, version: str, platform: str) -> str:
        driver_dir = Path(driver_dir).absolute()
        if driver_dir.is_file():
            raise TypeError('"driver_dir" is dir')
        else:
            driver_dir.mkdir(parents=True, exist_ok=True)
        platform = choicer(
            platform,
            choices=['win32', 'win64', 'mac64', 'linux64'],
            lable='platform')
        if platform.startswith('win'):
            platform = 'win32'
            version = cls.__get_version(version)
            exec_file = 'chromedriver.exe'
        else:
            exec_file = 'chromedriver'
        driver_file = driver_dir.joinpath(exec_file)
        if driver_file.is_file():
            if cls.__check_driver_version(driver_file, version, platform):
                return driver_file.as_posix()
        __version = cls.__find_similar_version(version)
        if not __version:
            raise ValueError('This version may not exist')
        __driver_zip = driver_dir.joinpath(f'chromedriver_{platform}.zip')
        __download_url = f'https://chromedriver.storage.googleapis.com/' \
                         f'{__version}/{__driver_zip.name}'
        try:
            sys.stdout.write(f'Download driver({__driver_zip.stem}) start.....')
            urlrequest.urlretrieve(__download_url, __driver_zip.as_posix())
            shutil.unpack_archive(__driver_zip, driver_dir, 'zip')
            os.remove(__driver_zip)
            return driver_file.as_posix()
        except:
            raise

    @staticmethod
    def __get_version(version: str) -> str:
        if version == 'LATEST_RELEASE' or not version:
            try:
                key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r'Software\Google\Chrome\BLBeacon')
                value, _type = winreg.QueryValueEx(key, 'version')
                version = value or 'LATEST_RELEASE'
            except Exception as err:
                sys.stdout.write(str(err))
                sys.stdout.write('将版本赋值为最新版本"LATEST_RELEASE"')
                version = 'LATEST_RELEASE'
        version = '.'.join(version.split('.')[:3])
        return version

    @staticmethod
    def __check_driver_version(driver_file: str, version: str, platform: str) -> bool:
        is_eq = True
        try:
            if platform.startswith('win'):
                outstd = os.popen(f'{driver_file} --version').read()
                cv_split = outstd.split()[1].split('.')[:3]
                v_split = version.split('.')
                if cv_split != v_split:
                    if len(v_split) > 1:
                        is_eq = '.'.join(cv_split).startswith('.'.join(v_split))
                    else:
                        is_eq = (v_split == cv_split[:1])
        except:
            is_eq = False
        return is_eq

    @staticmethod
    def __find_similar_version(version: str) -> str:
        url = 'https://chromedriver.storage.googleapis.com/'
        if version == 'LATEST_RELEASE':
            url += version
        sml_version = None
        try:
            version_resp = urlrequest.urlopen(url)
            htm = version_resp.read().decode('utf8')
            if version == 'LATEST_RELEASE':
                sml_version = htm
            else:
                pat = rf'<Key>({version}[\d.]*)/chromedriver_[\w.]+.zip</Key>'
                result = re.findall(pat, htm)
                if result:
                    sml_version = max(result)
        finally:
            pass
        return sml_version
