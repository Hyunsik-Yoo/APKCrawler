#-*- coding:utf-8 -*-
#!/usr/bin/python

# Do not remove
GOOGLE_LOGIN = GOOGLE_PASSWORD = AUTH_TOKEN = None

import sys
from pprint import pprint

from config import *
from googleplay import GooglePlayAPI
from helpers import sizeof_fmt
from DBController import DBController
import ConfigParser
import sqlite3
import logging
import logging.config
import subprocess

def download_apk(package_name, apk_directory):
    file_name = package_name + ".apk"
    try:
        # Connect
        api = GooglePlayAPI(ANDROID_ID)
        api.login(GOOGLE_LOGIN, GOOGLE_PASSWORD, AUTH_TOKEN)

    # Get the version code and the offer type from the app details
        m = api.details(package_name)
        doc = m.docV2
        vc = doc.details.appDetails.versionCode
        ot = doc.offer[0].offerType
    except Exception as e:
        raise e

    try:
        data = api.download(package_name, vc, ot)
        open(apk_directory + file_name, "wb").write(data)
    except Exception as e:
        raise e
    return True


def get_not_downloaded_app_list(apk_directory, db_directory):
    """
    DB에서 업데이트가 있거나, 아직 다운받지 않은 앱들을 다운로드합니다.
    다운로드가 성공하면 isDownloaded을 1로 업데이트 합니다.
    """
    connection = sqlite3.connect(db_directory)
    cursor = connection.cursor()

    try:
        # 다운받지 않거나 업데이트된 앱리스트를 받아옵니다.
        cursor.execute("select package from list where isDownloaded is null")
        package_list = cursor.fetchall()
        
        for package in package_list:
            package = package[0]
            try:
                if download_apk(package, apk_directory):
                    logger.info(package + ' finish download')
                    cursor.execute("update list set isDownloaded=1 where package==(?)" \
                        ,(package,))
                
                    connection.commit()

            #except IOError as e:
            #    logger.error('no space?')
            #    connection.commit()
            #    connection.close()
            #    raise e
            except Exception as e:
                print(e)
                logger.error(package + ' was not downloaded')
                cursor.execute("update list set isDownloaded = ? where package== ?"\
                    ,(None,package))
                connection.commit()
                continue
        
    except Exception as e:
        connection.commit()
        connection.close()
        raise e
    connection.close()


if __name__ == '__main__':
    
    # 로깅모듈 설정파일 읽기
    logging.config.fileConfig('logging.conf')
    logger = logging.getLogger('apk_crawler')

    # 설정파일 읽기
    config = ConfigParser.ConfigParser()
    config.read('config.ini')

    # 설정파일에서 경로 변수 읽기
    APK_DIRECTORY = config.get('Setting', 'APK_DIRECTORY')
    DB_DIRECTORY = config.get('Setting', 'DB_DIRECTORY')

    # DB에서 업데이트되거나 아직 다운받지 않은 APK들을 다운받습니다.
    get_not_downloaded_app_list(APK_DIRECTORY, DB_DIRECTORY)
