"""
@author axiner
@version v1.0.0
@created 2022/1/18 21:05
@abstract web驱动
@description
@history
"""
import os
import platform as sysplatform
import re
import shutil
import subprocess
import sys
import typing as t
import urllib.request as urlrequest
from pathlib import Path
from packaging.version import parse as version_parse

from toollib.common.error import DriverError
from toollib.useragent import random_ua
from toollib.validator import choicer


__all__ = ['chromedriver']


def chromedriver(driver_dir: t.Union[str, Path] = '.', platform: str = None, browser_version: str = None) -> str:
    """
    自动下载谷歌驱动（注：若指定目录存在与浏览器版本一致的驱动则会跳过）

    e.g.::

        import time
        from selenium import webdriver
        from selenium.webdriver.chrome.service import Service
        from toollib import autodriver

        # 自动下载驱动，默认下载本地浏览器对应的版本（各参数可自行指定）
        driver_path = autodriver.chromedriver()
        # 以下为selenium模拟操作
        driver = webdriver.Chrome(service=Service(driver_path))
        driver.get('https://www.baidu.com')
        driver.find_element(value='kw').send_keys('python toollib')
        driver.find_element(value='su').click()
        time.sleep(29)
        driver.close()

        +++++[更多详见参数或源码]+++++

    :param driver_dir: 驱动目录（默认当前执行目录）
    :param platform: 平台（支持：['win32', 'win64', 'mac64', 'mac-arm64', 'linux64']）
    :param browser_version: 浏览器版本
    """
    driver_path = ChromeDriver.download(driver_dir, platform, browser_version)
    return driver_path


class ChromeDriver:
    """
    谷歌驱动
    """

    @classmethod
    def download(cls, driver_dir: str, platform: str, browser_version: str) -> str:
        driver_dir, platform, browser_version = cls.__handle_params(driver_dir, platform, browser_version)
        if platform.startswith('win'):
            exec_file = 'chromedriver.exe'
            platform = 'win32'
        else:
            exec_file = 'chromedriver'
            if platform == 'mac-arm64':
                platform = 'mac_arm64'
        browser_latest_version = cls.__rurl('https://chromedriver.storage.googleapis.com/LATEST_RELEASE')
        if not browser_version:
            browser_version = browser_latest_version
        driver_file = driver_dir.joinpath(exec_file).as_posix()
        local_driver_version = None
        if os.path.isfile(driver_file):
            is_eq, local_driver_version = cls.__check_local_driver(driver_file, browser_version)
            if is_eq:
                return driver_file
        download_url, sml_version = cls.__get_download_url(platform, browser_version, browser_latest_version)
        if not download_url:
            raise DriverError('This version may not exist')
        if local_driver_version and sml_version \
                and local_driver_version.startswith('.'.join(sml_version.split('.')[:3])):
            return driver_file
        try:
            download_name = download_url.split('/')[-1]
            download_file = driver_dir.joinpath(download_name).as_posix()
            print(f'Download driver({download_name}) start.....')
            urlrequest.urlretrieve(download_url, download_file)
            shutil.unpack_archive(download_file, driver_dir, 'zip')
            os.remove(download_file)
            _driver_unpack_dir = download_file.rstrip('.zip')
            if os.path.isdir(_driver_unpack_dir):
                for f in [exec_file, 'LICENSE.chromedriver']:
                    dest_file = os.path.join(_driver_unpack_dir, f)
                    if os.path.isfile(dest_file):
                        local_file = driver_dir.joinpath(f)
                        if local_file.is_file():
                            os.remove(local_file)
                        shutil.move(dest_file, driver_dir)
                shutil.rmtree(_driver_unpack_dir, ignore_errors=True)
            if os.path.isfile(driver_file):
                return driver_file
            else:
                raise DriverError('Download driver failed')
        except Exception as err:
            if hasattr(err, 'code') and err.code == 404:
                sys.stdout.write('This version may not exist\n')
                sys.exit()
            else:
                raise

    @staticmethod
    def __rurl(url: str):
        request = urlrequest.Request(
            url,
            headers={
                'User-Agent': random_ua,
            })
        return urlrequest.urlopen(request).read().decode()

    @staticmethod
    def __handle_params(driver_dir: str, platform: str, browser_version: str):
        driver_dir = driver_dir if driver_dir else '.'
        driver_dir = Path(driver_dir).absolute()
        driver_dir.mkdir(parents=True, exist_ok=True)
        if not platform:
            _platform = sys.platform.lower()
            if _platform.startswith('win') or _platform.startswith('cygwin'):
                platform = 'win32'
            elif _platform.startswith('darwin'):
                if sysplatform.platform().lower().endswith('arm64'):
                    platform = 'mac-arm64'
                else:
                    platform = 'mac64'
            elif _platform.startswith('linux'):
                platform = 'linux64'
            else:
                raise DriverError(f'{_platform}: 不支持该系统')
        else:
            platform = platform.lower()
            platform = choicer(
                platform,
                choices=['win32', 'win64', 'mac64', 'mac-arm64', 'linux64'],
                lable='platform')
        if not browser_version:
            try:
                if platform.startswith('win'):
                    import winreg
                    key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r'Software\Google\Chrome\BLBeacon')
                    browser_version, _type = winreg.QueryValueEx(key, 'version')
                else:
                    if platform.startswith('mac'):
                        cmd = ['/Applications/Google Chrome.app/Contents/MacOS/Google Chrome', '--version']
                    else:
                        cmd = ['/usr/bin/google-chrome', '--version']
                    result = subprocess.run(cmd, capture_output=True, text=True)
                    browser_version = result.stdout.strip().split()[-1]
            except Exception as err:
                sys.stderr.write(f'获取浏览器版本失败（请手动指定）：{err}\n')
                sys.exit(1)
        return driver_dir, platform, browser_version

    @staticmethod
    def __check_local_driver(driver_file: str, browser_version: str) -> tuple:
        is_eq, local_driver_version = False, None
        try:
            result = subprocess.run([driver_file, '--version'], capture_output=True, text=True)
            local_driver_version = result.stdout.strip().split()[1]
            browser_version_split = browser_version.split('.')
            if local_driver_version != browser_version:
                if len(browser_version_split) > 1:
                    is_eq = local_driver_version.startswith('.'.join(browser_version_split[:3]))
                else:
                    is_eq = (browser_version_split == local_driver_version.split('.')[:1])
        except:
            pass
        return is_eq, local_driver_version

    @classmethod
    def __get_download_url(cls, platform: str, browser_version: str, browser_latest_version: str):
        _download_url = 'https://cdn.npmmirror.com/binaries/chromedriver/{version}/chromedriver_{platform}.zip'
        _download_test_url = 'https://edgedl.me.gvt1.com/edgedl/chrome/chrome-for-testing/{version}/{platform}/chromedriver-{platform}.zip'
        download_url,  sml_version = None, None

        try:
            browser_version_split = browser_version.split('.')
            if version_parse(browser_version) <= version_parse(browser_latest_version):
                resp = cls.__rurl('https://registry.npmmirror.com/-/binary/chromedriver')
                vs = re.findall(r'"name":"([^"]+)/"', resp)
                vs_dict = {}
                max_v = 0, None
                for v in vs:
                    if v == 'icons':
                        continue
                    if v == browser_version:
                        sml_version = v
                        break
                    v0 = v.split('.')[0]
                    vs_dict[v0] = v
                    if int(v0) >= max_v[0]:
                        max_v = int(v0), v
                if sml_version:
                    download_url = _download_url.format(version=sml_version, platform=platform)
                else:
                    sml_version = vs_dict.get(browser_version_split[0])
                    if sml_version:
                        download_url = _download_url.format(version=sml_version, platform=platform)
            else:
                sml_version = cls.__find_test_version(browser_version_short=".".join(browser_version_split[:3]))
                if sml_version:
                    if platform == 'mac64':
                        platform = 'mac-x64'
                    elif platform == 'mac_arm64':
                        platform = 'mac-arm64'
                    download_url = _download_test_url.format(version=sml_version, platform=platform)
        finally:
            pass
        return download_url, sml_version

    @classmethod
    def __find_test_version(cls, browser_version_short):
        resp = cls.__rurl("https://googlechromelabs.github.io/chrome-for-testing/latest-patch-versions-per-build.json")
        reg = "".join(['"', browser_version_short, '(?:\.\d+)*":{"version":"(.*?)",'])
        sml_versions = re.findall(reg, resp)
        if sml_versions:
            return sml_versions[-1]
