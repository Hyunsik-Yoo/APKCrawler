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
import configparser



def get_new_app_list(popular_url, chrome_driver_directory):
    """
    카테고리별 인기차트를 Selenium 를 사용해 300개 앱의 메타정보를 가지고 온다.
    """

    # 크롬 드라이버를 사용해 크롬을 실행시킨 뒤, 입력받은 URL로 이동
    chrome_driver = webdriver.Chrome(chrome_driver_directory)
    chrome_driver.get(popular_url)
    chrome_driver.implicitly_wait(10)

    # 해당 페이지를 스크롤해야만 300위까지의 앱이 나타남
    for scroll in (10000, 20000, 30000, 40000, 50000):
        chrome_driver.execute_script("window.scrollTo(0," + str(scroll) + ");")
        time.sleep(2)

    package_list = []
    # selector를 사용해 300개의 앱 div를 가져옴
    div_app_list =  chrome_driver.find_elements_by_css_selector(".card.no-rationale.square-cover.apps.small")
    for div_app in div_app_list:
        app_detail = div_app.find_element_by_class_name('details')
        url = app_detail.find_element_by_class_name('title').get_attribute('href')
        package_name = url.split('id=')[1]
        package_list.append(package_name)

    chrome_driver.close()

    # 앱이름, 상세정보url, 패키지 이름을 담은 리스트를 반환
    return package_list


def get_app_detail(package_list, chrome_driver_directory):
    """
        패키지 리스트를 입력으로 받아 앱별로 이름, 이미지소스, 업데이트날짜를 크롤링함
    """

    # 앱 상세정보 페이지에 들어가기위한 기본url. 뒤에 패키지 이름에 따라서 해당 앱 상세정보 페이지로 이동
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
            print(package + " 오류 발생")
            continue

        # 마지막에 None은 isDownloaded 컬럼에 해당된다.
        app_detail_list.append([title, package_name, img_src, updated_date, None])

    chrome_driver.close()

    return app_detail_list



def main():
    # 가상 디스플레이 설정
    #display = Display(visible=0, size=(800,600))
    #display.start()

    # 설정변수 불러오기
    config = configparser.ConfigParser()
    config.read('config.ini')
    APK_DIRECTORY = config.get('Setting','APK_DIRECTORY')
    DB_DIRECTORY = config.get('Setting','DB_DIRECTORY')
    CHROME_DRIVER_DIRECTORY = config.get('Setting','CHROME_DRIVER_DIRECTORY')

    # SQLite 파일 불러오기    
    db_connector = DBController(DB_DIRECTORY)

    # 테이블 생성
    db_connector.create_table()

    # 카레고리별 플레이스토어 인기차트 긁어오기
    for category in config.items('PlayStoreURL'):
        category_name = category[0]
        url = category[1]

        # 기존 DB에 존재하던 카테고리별 패키지 리스트를 가져오기
        old_list = db_connector.get_old_category_app_list(category)

        # Google Play Store를 크롤링하여 최신300개의 앱 메타정보를 가져오기
        new_list = get_new_app_list(url, CHROME_DRIVER_DIRECTORY)

        # 기존에 존재하는 리스트와 새로운 리스트를 이어붙임
        new_list.extend(old_list)

        # 최신앱 메타정보로 갱신한 리스트를 입력으로 주고 앱별로 상세정보를 크롤링함
        # 이름, 업데이트날짜, 이미지소스
        updated_app_list = get_app_detail(set(new_list), CHROME_DRIVER_DIRECTORY)

        # 새로 생긴된 데이터들을 DB에 업데이트
        db_connector.update_app(updated_app_list, category_name)

    #display.stop()

if __name__ == "__main__":
    main()
