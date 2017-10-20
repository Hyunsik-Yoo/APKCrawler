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
import requests
import logging

class Crawler:

    def __init__(self, is_desktop):
        config = configparser.ConfigParser()
        config.read('config.ini')
        self.apk_directory = config.get('Setting','APK_DIRECTORY')
        self.is_desktop = is_desktop
        if(not is_desktop):
            self.display = Display(visible=0, size=(800, 600))
            self.display.start()

        self.chrome = webdriver.Chrome(config.get('Setting',\
            'CHROME_DRIVER_DIRECTORY'))
        self.category_list = config.items('PlayStoreURL')
        self.db_connector = DBController(config.get('Setting','DB_DIRECTORY'))
        self.db_connector.create_table()

    def __get_new_app_list(self, popular_url):
        """
        카테고리별 인기차트를 Selenium 를 사용해 300개 앱의
        메타정보를 가지고 온다.
        """
        self.chrome.get(popular_url)
        self.chrome.implicitly_wait(10)

        # 해당 페이지를 스크롤해야만 300위까지의 앱이 나타남
        for scroll in (10000, 20000, 30000, 40000, 50000):
            self.chrome.execute_script("window.scrollTo(0," \
                + str(scroll) + ");")
            time.sleep(2)

        package_list = []
        # selector를 사용해 300개의 앱 div를 가져옴
        div_app_list =  self.chrome.find_elements_by_css_selector(\
            ".card.no-rationale.square-cover.apps.small")
        for div_app in div_app_list:
            app_detail = div_app.find_element_by_class_name('details')
            url = app_detail.find_element_by_class_name('title')\
                .get_attribute('href')
            package_name = url.split('id=')[1]
            package_list.append(package_name)

        return package_list

    def __get_app_detail(self, package_list):
        """
        패키지 리스트를 입력으로 받아 앱별로 이름, 이미지소스,\
        업데이트날짜를 크롤링함
        """

        # 앱 상세정보 페이지에 들어가기위한 기본url
        # 뒤에 패키지 이름에 따라서 해당 앱 상세정보 페이지로 이동
        base_url = 'https://play.google.com/store/apps/details?id='
        detail_list = []

        for package in package_list:
            app_url = base_url + package

            self.chrome.get(app_url)
            self.chrome.implicitly_wait(10)

            try:
                name = self.chrome.\
                    find_element_by_css_selector('.id-app-title').text
                img_src = self.chrome.\
                    find_element_by_css_selector('.cover-image').\
                        get_attribute('src')
                updated_date = self.chrome.\
                    find_elements_by_css_selector('.content')[0].text
            except:
                print(package + " 오류 발생")
                print(package + " name, img_src, update_date 가져오기 실패")
                continue

            # 마지막에 None은 isDownloaded 컬럼에 해당된다.
            detail_list.append([name, package, img_src, updated_date, False])

        return detail_list


    def __download_apk(self,package_name,download_url):
        """
        APK파일을 HTTP request를 통해 다운받는 함수
        리퀘스트를 보내는 도중 에러가 발생하면 False반환
        정상적으로 파일이 저장완료되면 True반환
        """
        file_name = str(package_name) + '.apk'
        try:
            r = requests.get(download_url, timeout=60)
            with open(self.apk_directory + file_name,'wb') as apk:
                apk.write(r.content)
        except requests.exceptions.Timeout as e:
            print('time out')
            return False
        except Exception as e:
            print(e)
            return False
        return True


    def crawl_new(self):
        # 카레고리별 플레이스토어 인기차트 긁어오기
        for category in self.category_list:
            category_name = category[0]
            url = category[1]

            # Google Play Store를 크롤링하여 최신300개의 앱 메타정보를 가져오기
            new_package_list = self.__get_new_app_list(url)

            # 최신앱 메타정보로 갱신한 리스트를 입력으로 주고 
            # 앱별로 상세정보를 크롤링함
            # 이름, 업데이트날짜, 이미지소스
            updated_app_list = self.__get_app_detail(new_package_list)

            # 새로 생긴된 데이터들을 DB에 업데이트
            self.db_connector.update_app(updated_app_list, category_name)

        self.db_connector.commit_n_close()



    def crawl_old(self):
        for category in self.category_list:
            category_name = category[0]
            url = category[1]

            # 기존 DB에 존재하던 카테고리별 패키지 리스트를 가져오기
            old_package_list = self.db_connector\
                .get_old_category_app_list(category)

            # 최신앱 메타정보로 갱신한 리스트를 입력으로 주고 
            # 앱별로 상세정보를 크롤링함
            # 이름, 업데이트날짜, 이미지소스
            updated_app_list = self.__get_app_detail(old_package_list)

            # 새로 생긴된 데이터들을 DB에 업데이트
            self.db_connector.update_app(updated_app_list, category_name)
        self.db_connector.commit_n_close()

    def update_apk(self):
        not_updated_list = self.db_connector.not_updated_list()
        print(1)
        for package_row in not_updated_list:
            package_name = package_row[0]
            search_url = 'http://apkpure.com/search?q=' + package_name
            self.chrome.get(search_url)
            self.chrome.implicitly_wait(10)

            # 패키지명으로 검색하여 일치하는 앱 찾기
            search_titles = self.chrome.\
                find_elements_by_class_name('search-title')

            # APK pure사이트에서 검색이 되지 않는 APK는 통과
            if len(search_titles) == 0:
                logging.info(package_name + " is not searched")
                continue

            # 검색결과와 일치하는 앱은 href링크에 패키지 이름이 들어있음
            link = ''
            for title in search_titles:
                link = title.find_element_by_tag_name('a')
                link = link.get_attribute('href')

                if package_name in link:
                    break

            # 검색결과가 여러개 나오지만 일치하지 않는다면 통과
            if link =='':
                logging.info(package_name + ' is not searched in APKpure')
                continue

            print(link) # debug
            self.chrome.get(link)
            self.chrome.implicitly_wait(10)

            a_list = self.chrome.find_elements_by_class_name(' down')
            try:
                for a in a_list:
                    link = a.get_attribute('href')
                    # href링크에 패키지 이름있는것이 있으면 발견!
                    if package_name in link:
                        self.chrome.get(link)
                        self.chrome.implicitly_wait(10)
                        break
                # 페이지 내부에 iframe을 못찾는 경우가 발생
                # 못찾는다면 해당 APK는 무시하고 다음APK로 이동
                iframe = self.chrome.find_element_by_id('iframe_download')

                src = iframe.get_attribute('src')
            except:
                logging.info(package_name + " does not have href or iframe")
                continue

            if(self.__download_apk(package_name, src)):
                self.db_connector.update_isdownload(package_name, True)
            else:
                self.db_connector.update_isdownload(package_name, False)

        self.db_connector.commit_n_close()

    def close():
        self.chrome.stop()
        if(not self.is_desktop):
            self.display.stop()
