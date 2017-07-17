#-*- coding: utf-8 -*-
from selenium import webdriver
import urllib
import sqlite3
import subprocess
import re
import os
import time
from DBController import DBController
import sys
from pyvirtualdisplay import Display
import logging.config
import logging
import configparser


def create_table(db_connector):
    return db_connector.create_table()

def get_category_url(url, chrome_driver_directory):
    """
    카테고리별 인기차트를 Selenium 를 사용해 300개 앱의 메타정보를 가지고 온다.
    """

    top_selling_url = url
    chrome_driver = webdriver.Chrome(chrome_driver_directory)
    chrome_driver.get(top_selling_url)
    chrome_driver.implicitly_wait(10)
    
     
    for scroll in (10000, 20000, 30000, 40000, 50000):
        chrome_driver.execute_script("window.scrollTo(0," + str(scroll) + ");")
        time.sleep(2)
    
    package_list = []

    div_app_list =  chrome_driver.find_elements_by_css_selector(".card.no-rationale.square-cover.apps.small")
    for div_app in div_app_list:
        app_detail = div_app.find_element_by_class_name('details')
        url = app_detail.find_element_by_class_name('title').get_attribute('href')
        package_name = url.split('id=')[1]
        package_list.append(package_name)

    chrome_driver.close()

    return package_list

def get_app_detail(package_list, chrome_driver_directory):
    base_url = 'https://play.google.com/store/apps/details?id='
    app_detail_list = []
    chrome_driver = webdriver.Chrome(chrome_driver_directory)

    for package in package_list:
        app_url = base_url + package
        package_name = app_url.split('id=')[1]
        chrome_driver.get(app_url)
        chrome_driver.implicitly_wait(10)
        try:
            title = chrome_driver.find_element_by_css_selector('.id-app-title').text
            img_src = chrome_driver.find_element_by_css_selector('.cover-image').get_attribute('src')
            updated_date = chrome_driver.find_elements_by_css_selector('.content')[0].text
        except:
            continue
        app_detail_list.append([title, package_name, img_src, updated_date, None])

    chrome_driver.close()

    return app_detail_list


def update_db(db_connector, chrome_driver_directory, apk_directory):
    app_list = db_connector.get_all_app_list()
    if(app_list == False):
        return False

    failed_list = []
    try:
        for app_info in app_list:
            package_name = app_info[1]
            downloaded = download_apk_file(package_name, apk_directory)
            if downloaded == False: 
                failed_list.append(app_info[1])
                continue
            time.sleep(2) 
    except Exception as e:
        raise e
        return False

    return failed_list

def delete_null(db_connector, failed_list):
    return db_connector.delete_null(failed_list)

def update_app_list(db_connector, updated_app_list, category):
    return db_connector.update_app_list(updated_app_list, category)

def download_latest_apk(db_connector, apk_directory):
    try:
        db_connector.get_not_downloaded_app_list(apk_directory)
    except Exception as e:
        raise e

def main():
    
    logging.config.fileConfig('logging.conf')
    logger = logging.getLogger('apk_crawler')

    # 가상 디스플레이 설정
    display = Display(visible=0, size=(800,600))
    display.start()

    # 설정변수 불러오기
    config = configparser.ConfigParser()
    config.read('config.ini')
    APK_DIRECTORY = config.get('Setting','APK_DIRECTORY')
    DB_DIRECTORY = config.get('Setting','DB_DIRECTORY')
    CHROME_DRIVER_DIRECTORY = config.get('Setting','CHROME_DRIVER_DIRECTORY')


    # APK파일이 저장될 디렉토리 생성
    try:
        os.makedirs(APK_DIRECTORY)
    except Exception as e:
        #logger.info('apk director가 이미 존재합니다.')
        pass
    # SQLite 파일 불러오기    
    db_connector = DBController(DB_DIRECTORY) 

    # 테이블 생성
    create_table(db_connector)
   
    # 카레고리별 플레이스토어 인기차트 긁어오기
    
    for category in config.items('PlayStoreURL'):
        url = category[1]
        old_list = db_connector.get_category_app_list(category)
        app_list = get_category_url(url, CHROME_DRIVER_DIRECTORY)
        app_list.extend(old_list)
        updated_app_list = get_app_detail(set(app_list), CHROME_DRIVER_DIRECTORY)
        update_app_list(db_connector, updated_app_list, category[0])
 
    display.stop()
     

if __name__ == "__main__":
    main()
