from selenium import webdriver
import urllib
import sqlite3
import subprocess
import re
import os
import time
import sys
from pyvirtualdisplay import Display
import configparser
import requests
import logging
from DBController import DBController

class Crawler:

    def __init__(self, is_desktop):
        """
        생성자
        is_desktop : 서버환경에서 실행시키는지, 데크스탑환경(GUI)에서 실행시키는지\
                     (true, false)
        """
        # config.ini파일의 변수 가져오기
        config = configparser.ConfigParser()
        config.read('config.ini')
        self.apk_directory = config.get('Setting','APK_DIRECTORY')
        self.is_desktop = is_desktop

        # 서버모드로 실행시켰다면 가상디스플레이 실행
        if(not is_desktop):
            self.display = Display(visible=0, size=(800, 600))
            self.display.start()

        # 크롬 드라이버 실행 
        self.chrome = webdriver.Chrome(config.get('Setting',\
            'CHROME_DRIVER_DIRECTORY'))

        # 크롤링할 디렉토리 리스트 저장
        self.category_list = config.items('PlayStoreURL')

        # 데이터를 저장하고 제어할 DBController객체 생성
        self.db_connector = DBController(config.get('Setting','DB_DIRECTORY'))

        # 메타데이터가 저장될 SQLite 테이블 생성
        self.db_connector.create_table()

    def __get_new_app_list(self, popular_url):
        """
        (private)
        입력받은 인기차트 url의 상위 300개 앱 메타데이터 수집
        popular_url : 특정 카테고리의 인기차트 URL
        """

        # 크롬 드라이버 url 이동 및 완료 대기
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

        # 300개의 div태그를 반복하면서 패키지 이름을 추출하여 리스트에 저장
        for div_app in div_app_list:
            app_detail = div_app.find_element_by_class_name('details')
            url = app_detail.find_element_by_class_name('title')\
                .get_attribute('href')
            package_name = url.split('id=')[1]
            package_list.append(package_name)

        return package_list

    def __get_app_detail(self, package_list):
        """
        (priavte)
        패키지 리스트를 입력으로 받아 해당 패키지의 앱 이름, 이미지소스,\
        업데이트날짜, 별점 개수 (ratings)를 크롤링함
        """

        # 앱 상세정보 페이지에 들어가기위한 기본url
        # 뒤에 패키지 이름에 따라서 해당 앱 상세정보 페이지로 이동
        base_url = 'https://play.google.com/store/apps/details?id='
        detail_list = []

        for package in package_list:
            app_url = base_url + package

            # 크롬 드라이버 페이지 이동 및 완료 대기
            self.chrome.get(app_url)
            self.chrome.implicitly_wait(10)

            # 앱 이름, 이미지 소스, 최근 업데이트 날짜, 별점을 조회
            # 원인은 파악하지 못했지만 exception발생하는 구간 존재
            # TODO: Exception이 발생하는 구간을 정확하게 파악하여 예외처리
            try:
                name = self.chrome.\
                    find_element_by_css_selector('.id-app-title').text

                img_src = self.chrome.\
                    find_element_by_css_selector('.cover-image').\
                        get_attribute('src')

                updated_date = self.chrome.\
                    find_elements_by_css_selector('.content')[0].text

                ratings = self.chrome.\
                    find_elements_by_css_selector('.rating-count')[0].text
                # 숫자 3자리마다 쉼표가 들어가므로 제거
                if ',' in ratings:
                    ratings = ratings.replace(',','')
            except:
                print(package + " 오류 발생")
                print(package + " name, img_src, update_date 가져오기 실패")
                continue

            # [앱 이름, 패키지 이름, 이미지 소스, 최신업데이트 날짜, APK다운 여부]
            detail_list.append([name, package, img_src, updated_date, False])

        return detail_list


    def __download_apk(self,package_name,download_url):
        """
        (private)
        HTTP request를 통해 APK파일을 다운받음
        리퀘스트를 보내는 도중 에러가 발생하면 False반환
        정상적으로 파일이 저장완료되면 True반환
        package_name : 다운받으려는 패키지 이름
        download_url : HTTP request를 날리는 url 이름
        """
        file_name = str(package_name) + '.apk'

        # timout 1분으로 설정하여 반응이 없는 것들은 예외처리
        try:
            r = requests.get(download_url, timeout=60)
            # apk directory에 패키지이름.apk 형태로 저장
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
        """
        (public)
        카테고리 별 플레이스토어 인기차트 크롤링 및 DB 저장
        """
        for category in self.category_list:
            category_name = category[0]
            url = category[1]

            # 하나의 카테고리 인기차트에서 300개의 앱 패키지 이름 가져오기
            new_package_list = self.__get_new_app_list(url)

            # 카테고리의 300개 앱 패키지 이름으로 300개 앱 상세정보 수집
            # (앱 이름, 최신 업데이트 날짜, 이미지 소스, 레이팅) 
            updated_app_list = self.__get_app_detail(new_package_list)

            # 300개의 앱 메타 데이터를 DB에 업데이트
            # 동일한 앱이 존재한다면 그대로 유지
            # 하지만 동일한 앱에도 업데이트가 존재한다면 메타정보 업데이트
            # 앱 이름이 DB에 없다면 새로 추가
            self.db_connector.update_app(updated_app_list, category_name)

        self.db_connector.commit_n_close()



    def crawl_old(self):
        """
        (public)
        기존 DB에 저장된 앱 메타데이터를 최신으로 업데이트
        """
        for category in self.category_list:
            category_name = category[0]
            url = category[1]

            # 기존 DB에 존재하던 카테고리별 패키지 리스트를 가져오기
            old_package_list = self.db_connector\
                .get_old_category_app_list(category)

            # 기존 DB 메타데이터의 상세정보를 플레이스토어에서 크롤링
            updated_app_list = self.__get_app_detail(old_package_list)

            # 새로 생긴된 데이터들을 DB에 업데이트
            self.db_connector.update_app(updated_app_list, category_name)
        self.db_connector.commit_n_close()

    def update_apk(self):
        """
        DB에서 다운받지 않은 APK파일을 찾아 APK파일을 다운로드
        """

        # DB에서 아직 다운받지 않은 APK파일의 리스트를 가져옴
        not_updated_list = self.db_connector.not_updated_list()

        for package_row in not_updated_list:
            package_name = package_row[0]
            # apkpure.com에 패키지 이름으로 검색
            search_url = 'http://apkpure.com/search?q=' + package_name
            self.chrome.get(search_url)
            self.chrome.implicitly_wait(10)

            # 일치하는 앱이 검색되었는지 확인
            search_titles = self.chrome.\
                find_elements_by_class_name('search-title')

            # 검색결과가 없으면 apk를 다운받을 수 없으므로 통과
            if len(search_titles) == 0:
                logging.info(package_name + " is not searched")
                continue

            # 검색결과와 일치하는 앱의 href 속성에서 다운로드 링크 추출
            # 검색결과가 여러개일 경우가 있으므로 패키지 이름으로 다시 확인
            link = ''
            for title in search_titles:
                link = title.find_element_by_tag_name('a')
                link = link.get_attribute('href')

                if package_name in link:
                    break

            # 검색결과가 여러개 나오지만 패키지명이 일치하지 않는다면 통과
            if link =='':
                logging.info(package_name + ' is not searched in APKpure')
                continue

            # apk download링크로 이동
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


            # apk 파일 다운로드가 성공하면 db에 True로 저장, 실패시 False로 저장
            if(self.__download_apk(package_name, src)):
                self.db_connector.update_isdownload(package_name, True)
            else:
                self.db_connector.update_isdownload(package_name, False)

        self.db_connector.commit_n_close()

    def close(self):
        self.chrome.stop()
        if(not self.is_desktop):
            self.display.stop()
