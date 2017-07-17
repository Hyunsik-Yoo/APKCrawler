#-*- coding: utf-8 -*-
import sqlite3
import datetime
import sys
import logging

class DBController:
    """
    앱 메타정보 DB를 관리하는 클래스
    - __init__ : 생성자
    - commit_n_close : 변경내용 저장 및 종료
    - create_table : 앱 메타정보 저장하는 테이블 생성
    - get_old_category_app_list : 기존 DB에 존재하는 앱정보 불러오기
    - get_all_app_name_list : 기존 DB에 존재하는 모든 앱이름만 리스트로 가져오기
    - update_date : 메타정보를 입력받아 DB date컬럼 업데이트
    - update_app : 해당 앱에 대하여 최신정보로 DB업데이트 (날짜 및 isDownloaded)
    - insert_app : 새로운 앱 메타정보를 테이블에 추가
    """

    def __init__(self, db_directory):
        """
        생성자. 새로운 db를 만들고 커서 생성
        """
        self.connection = sqlite3.connect(db_directory)
        self.cursor = self.connection.cursor()

    def commit_n_close(self):
        """
        현재까지 변경된 내용을 저장한뒤, 종료
        """
        self.connection.commit()
        self.connection.close()

    def create_table(self):
        """
        어플리케이션 메타정보를 저장하는 테이블 생성
        정상적으로 생성되거나, 이미 존재한다면 True반환.
        예외가 발생하면 False 반환
        """
        try:
            self.cursor.execute('CREATE TABLE list(appName, package, imgSrc, updateDate, isDownloaded, category)')
        except sqlite3.OperationalError as e: # 테이블이 존재한다면 여기로 들어옴
            pass
        except Exception as e:
            print("create table중 알 수 없는 오류 발생")
            raise e

    def get_old_category_app_list(self,category):
        """
        카테고리를 입력으로 받아 해당 카테고리에 속하고 기존 디비에 존재하는 패키지 이름들을 리스트로 반환
        """
        try:
            self.cursor.execute('SELECT package FROM list WHERE category==(?)',(category[0],))
            package_list = []
            total_data = list(self.cursor)
            package_list = [tuple[0] for tuple in total_data]
        except Exception as e:
            raise e
        return package_list

    def get_all_app_name_list(self):
        """
        DB에 존재하는 모든 앱이름 리스트로 반환
        """
        try:
            self.cursor.execute('SELECT * FROM list')
            total_data = self.cursor.fetchall()
            app_name_list = [tuple[0] for tuple in total_data]
            return app_name_list
        except Exception as e:
            self.connection.close()
            raise e

    def update_date(self, app):
        """
            앱 메타정보를 입력으로 받아 기존DB에 존재하던 앱정보를 최신정보로 업데이트 시킴
            isDownloaded필드를 변경
        """
        try:
            self.cursor.execute("update list set updateDate=? where appName=?",(app[3], app[0]))
            self.cursor.execute("update list set isDownloaded=? where appName=?",(None,app[0]))
            self.connection.commit()
        except Exception as e:
            print('update_date error')
            self.connection.close()
            raise e

    def update_app(self, update_app_list, category):
        """
            최신버전으로 갱신된 앱 메타정보리스트를 입력으로 받음
            해당 정보들을 DB에 갱신시킴
        """
        total_app_list = self.get_all_app_name_list()

        for app in update_app_list:
            app_name = app[0]

            # 기존 DB에 존재하던 앱이라면 업데이트날짜를 비교해서 동일하면 그대로
            # 업데이트가 날짜가 다르다면(업데이트가 존재한다면) 업데이트 날짜 수정 및 isDownloaded 컬럼 수정
            if app_name in total_app_list:
                self.cursor.execute("select * from list where appName=(?)",(app_name,))
                total_data = self.cursor.fetchall()[0]

                if total_data[3] == app[3]:
                    continue
                else:
                    self.update_date(app)
                    logging.info(app_name + ' is updated')
            # 기존 DB에 업던 앱이라면 새로 DB에 추가시힘
            else:
                self.insert_app(app, category)
                logging.info(app_name + ' is inserted')

    def insert_app(self, insert_app, category):
        """
            기존DB에 없던 앱을 추가할 때 호출됨.
        """
        insert_app.append(category)
        try:
            self.cursor.execute("INSERT INTO list VALUES (?,?,?,?,?,?)", insert_app)
            print (str(datetime.datetime.now()) + " - new record " + insert_app[0] + "is inserted in DB.")
        except Exception as e:
            self.connection.close()
            raise e

        # 삽입 정보 저장
        self.connection.commit()
