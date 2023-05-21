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

from toollib.validator import choicer


__all__ = ['chromedriver']


def chromedriver(driver_dir: t.Union[str, Path] = '.', version: str = 'LATEST_RELEASE', platform: str = 'win64') -> str:
    """
    自动下载谷歌驱动（注：若指定目录存在与浏览器版本一致的驱动则会跳过）

    e.g.::

        # 不指定浏览器版本，则下载当前浏览器对应的版本（针对win平台，mac|linux则下载最新版本（可查看浏览器版本自行指定））
        import time
        from selenium import webdriver
        from selenium.webdriver.chrome.service import Service
        from toollib import autodriver

        driver_path = autodriver.chromedriver()  # 自动下载驱动
        driver = webdriver.Chrome(service=Service(driver_path))
        driver.get('https://www.baidu.com')
        driver.find_element(value='kw').send_keys('python toollib')
        driver.find_element(value='su').click()
        time.sleep(29)
        driver.close()

        +++++[更多详见参数或源码]+++++

    :param driver_dir: 驱动目录（默认当前执行目录）
    :param version: 版本（谷歌浏览器）
    :param platform: 平台（默认：win64）-支持：['win32', 'win64', 'mac64', 'linux64']
    """
    driver_path = ChromeDriver.download(driver_dir, version, platform)
    return driver_path


class ChromeDriver:
    """
    谷歌驱动
    """

    @classmethod
    def download(cls, driver_dir: str, version: str, platform: str) -> str:
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
            print(f'Download driver({__driver_zip.stem}) start.....')
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
                import winreg
                key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r'Software\Google\Chrome\BLBeacon')
                value, _type = winreg.QueryValueEx(key, 'version')
                version = value or 'LATEST_RELEASE'
            except Exception as err:
                print(str(err))
                print('将版本赋值为最新版本"LATEST_RELEASE"')
                version = 'LATEST_RELEASE'
        version = '.'.join(version.split('.')[:3])
        return version

    @staticmethod
    def __check_driver_version(driver_file: str, version: str, platform: str) -> bool:
        is_eq = True
        try:
            if platform.startswith('win'):
                outstd = os.popen(f'"{driver_file}" --version').read()
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
