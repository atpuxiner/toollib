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
import typing as t
import urllib.request as urlrequest
from pathlib import Path

try:
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.chromium.service import ChromiumService
    from selenium.webdriver.chromium.webdriver import ChromiumDriver
except ImportError:
    raise

__all__ = ['ChromeDriver']


class ChromeDriver(ChromiumDriver):
    """
    谷歌驱动
    eg:
        driver = ChromeDriver('chromedriver_dir')
        driver.get('https://www.baidu.com/')
        ----- or
        driver = ChromeDriver(r'D:\chromedriver_dir', version='96.0.4664.45')
        driver.get('https://www.baidu.com/')
        ----- or: more params
        .....
    """

    def __init__(self, driver_dir: t.Union[str, Path], version: str = 'LATEST_RELEASE',
                 platform: str = 'win', bit: int = 32,
                 port=0, options: Options = None,
                 service_args: t.List[str] = None, desired_capabilities=None,
                 service_log_path=None, env: dict = None, start_error_message: str = None,
                 service: ChromiumService = None, keep_alive=None):
        """
        谷歌驱动
        :param driver_dir: 驱动目录（若目录下不存在驱动则会自动下载）
        :param version: 版本号（谷歌浏览器）
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
            start_error_message = start_error_message or \
                                  'Please see https://sites.google.com/a/chromium.org/chromedriver/home'
            driver_file = self.__download_driver(driver_dir, version, platform, bit)
            service = ChromiumService(
                driver_file, port, service_args, service_log_path, env, start_error_message)
        __browser_name, __vendor_prefix = 'chrome', 'goog'
        super(ChromeDriver, self).__init__(
            __browser_name, __vendor_prefix, port, options, service_args,
            desired_capabilities, service_log_path,
            service, keep_alive)

    @classmethod
    def __download_driver(cls, driver_dir, version, platform, bit):
        driver_dir = Path(driver_dir).absolute()
        if driver_dir.is_file():
            raise TypeError('"driver_dir" is dir')
        else:
            driver_dir.mkdir(parents=True, exist_ok=True)
        if platform not in ['win', 'mac', 'linux']:
            raise TypeError('"platform" only supported: win, mac or linux')
        if platform == 'win':
            executable_file = 'chromedriver.exe'
        else:
            executable_file = 'chromedriver'
        driver_file = driver_dir.joinpath(executable_file)
        if driver_file.is_file():
            return driver_file.as_posix()
        __version = cls.__find_similar_version(version)
        if not __version:
            raise ValueError('This version may not exist')
        __driver_zip = driver_dir.joinpath(f'chromedriver_{platform}{bit}.zip')
        __download_url = f'https://chromedriver.storage.googleapis.com/' \
                         f'{__version}/{__driver_zip.name}'
        try:
            print(f'Download driver ({__driver_zip.stem}) start.....')
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
                pat = f'<Key>({version}[\d.]*)/chromedriver_[\w.]+.zip</Key>'
                result = re.findall(pat, html)
                if result:
                    sml_version = max(result)
        finally:
            pass
        return sml_version
