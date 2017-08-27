import configparser
from selenium import webdriver
import sqlite3
#from pyvirtualdisplay import Display
import sys
import os
import re
import requests
import logging


config = configparser.ConfigParser()
config.read('config.ini')
APK_DIRECTORY = config.get('Setting','APK_DIRECTORY')
DB_DIRECTORY = config.get('Setting','DB_DIRECTORY')
CHROME_DRIVER_DIRECTORY = config.get('Setting','CHROME_DRIVER_DIRECTORY')

def download_apk(package_name,download_url):
    """
    APK파일을 HTTP request를 통해 다운받는 함수
    리퀘스트를 보내는 도중 에러가 발생하면 False반환
    정상적으로 파일이 저장완료되면 True반환
    """
    global APK_DIRECTORY
    file_name = str(package_name) + '.apk'

    try:
        r = requests.get(download_url, timeout=60)
        with open(APK_DIRECTORY+file_name,'wb') as apk:
            apk.write(r.content)
    except requests.exceptions.Timeout as e:
        print('time out')
        return False
    except Exception as e:
        print(e)
        return False

    return True


def get_not_downloaded_app_list():
    """
    DB에서 업데이트가 있거나, 아직 다운받지 않은 앱들을 다운로드합니다.
    다운로드가 성공하면 isDownloaded을 1로 업데이트 합니다.
    """
    global DB_DIRECTORY

    connection = sqlite3.connect(DB_DIRECTORY)
    cursor = connection.cursor()

    try:
        # 다운받지 않거나 업데이트된 앱리스트를 받아옵니다.
        cursor.execute("select package from list where isDownloaded is null")
        package_list = cursor.fetchall()
    except Exception as e:
        connection.close()
        raise e

    connection.close()
    return package_list

# 다운로드가 안되어있거나 업데이트가 된 앱리스트를 가져옴


def main():

    # 로깅모듈 설정
    logging.basicConfig(filename='result.log', format='%(asctime)s %(message)s',level=logging.INFO)


    #display = Display(visible=0, size=(800,600))
    #display.start()

    global CHROME_DIRECTORY_DIRECTORY
    # 크롬실행시킬때 자동다운로드를 금지시키도록 설정하여 실행
    chrome_profile = webdriver.ChromeOptions()
    profile = {"download.default_directory": "NUL", "download.prompt_for_download": False, }
    chrome_profile.add_experimental_option("prefs", profile)
    chrome_driver = webdriver.Chrome(CHROME_DRIVER_DIRECTORY,chrome_options=chrome_profile)

    # "appList.db"에 존재하고 다운로드가 필요한 앱정보들 가져옴
    package_list = get_not_downloaded_app_list()

    connection = sqlite3.connect(DB_DIRECTORY)
    cursor = connection.cursor()

    for package_row in package_list:
        package_name = package_row[0]
        search_url = 'http://apkpure.com/search?q=' + package_name
        chrome_driver.get(search_url)
        chrome_driver.implicitly_wait(10)

        # 패키지명으로 검색하여 일치하는 앱 찾기
        search_titles = chrome_driver.find_elements_by_class_name('search-title')

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

        print(link) # 디버깅용
        chrome_driver.get(link)
        chrome_driver.implicitly_wait(10)

        a_list = chrome_driver.find_elements_by_class_name(' down')
        try:
            for a in a_list:
                link = a.get_attribute('href')
                # href링크에 패키지 이름있는것이 있으면 발견!
                if package_name in link:
                    chrome_driver.get(link)
                    chrome_driver.implicitly_wait(10)
                    break
            # 페이지 내부에 iframe을 못찾는 경우가 발생
            # 못찾는다면 해당 APK는 무시하고 다음APK로 이동
            iframe = chrome_driver.find_element_by_id('iframe_download')

            src = iframe.get_attribute('src')
        except:
            logging.info(package_name + " does not have href or iframe")
            continue

        # 다운로드가 성공되었다면 appList.db에 다운로드 성공으로 1 표시
        if(download_apk(package_name, src)):
            cursor.execute("update list set isDownloaded=1 where package==(?)",(package_name,))
            connection.commit()
            logging.info(package_name + ' is download sucessfully')

        # 다운로드가 성공하지 못한다면 isDownloaded를 None로 설정
        else:
            cursor.execute("update list set isDownloaded=? where package==?",(None,package_name))
            connection.commit()

    connection.close()
    #display.stop()

if __name__ == '__main__':
    main()
