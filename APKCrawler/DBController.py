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
    - get_all_app_name_list : 기존 DB에 존재하는 모든 앱이름만
        리스트로 가져오기
    - update_date : 메타정보를 입력받아 DB date컬럼 업데이트
    - update_app : 해당 앱에 대하여 최신정보로 DB업데이트
        (날짜 및 isDownloaded)
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
            self.cursor.execute("""
                CREATE TABLE list(
                    appName,
                    package,
                    imgSrc,
                    updateDate,
                    isDownloaded,
                    category
                )""")

        # 테이블이 존재한다면 여기로 들어옴
        except sqlite3.OperationalError as e:
            print(e)
            return True
        except Exception as e:
            print("create table중 알 수 없는 오류 발생")
            return False

    def get_old_category_app_list(self,category):
        """
        카테고리를 입력으로 받아 해당 카테고리에 속하고
        기존 디비에 존재하는 패키지 이름들을 리스트로 반환
        """
        try:
            self.cursor.execute('SELECT package FROM list WHERE category==(?)'\
                ,(category[0],))
            package_list = []
            total_data = self.cursor.fetchall()
            package_list = [row[0] for row in total_data]
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
            app_name_list = [row[0] for row in total_data]
            return app_name_list
        except Exception as e:
            self.connection.close()
            raise e

    def update_date(self, app):
        """
        앱 메타정보를 입력으로 받아 기존DB에 존재하던 앱정보를
        최신정보로 업데이트 시킴. isDownloaded필드를 변경
        """
        try:
            self.cursor.execute(\
                "update list set updateDate=? where appName=?",\
                (app.update_date, app.name))
            self.cursor.execute(\
                "update list set isDownloaded=? where appName=?",\
                (None, app.name))
            self.connection.commit()
        except Exception as e:
            print('update_date error')
            self.connection.close()
            raise e

    def update_app(self, update_app_list, category):
        """
        입력 : 최신버전의 메타정보리스트
        역할 : 입력정보를 DB에 반영
        """

        all_app_list = self.get_all_app_name_list()

        for new_app in update_app_list:
            new_app_name = new_app[0]
            new_app_update_date = new_app[3]

            # 기존 DB에 존재하던 앱이라면 업데이트날짜를 비교해서 
            # 동일하면 그대로
            # 업데이트가 날짜가 다르다면(업데이트가 존재한다면)
            # 업데이트 날짜 수정 및 isDownloaded 컬럼 수정
            self.cursor.execute(\
                "select * from list where appName=(?) LIMIT 1",\
                (new_app_name,))

            # 기존 DB에 없던 앱이라면 새로 DB에 추가시힘
            if(cursor.rowcount == 0):
                self.insert_app(new_app, category)
                logging.info(new_app_name + ' is inserted')
                continue

            # 기존 DB에 있는 앱이라면 업데이트 날짜 비교한뒤 
            # 날짜가 다르면 업데이트
            old_date = cursor.fetchone()
            old_update_date = old_data[3]

            if old_update_date == app_update_date:
                logging.info(new_app_name + ' is already updated')
                continue
            else:
                self.update_date(app)
                logging.info(new_app_name + ' is updated')


    def insert_app(self, new_app, category):
        """
            기존DB에 없던 앱을 추가할 때 호출됨.
        """
        try:
            self.cursor.execute("INSERT INTO list VALUES (?,?,?,?,?,?)",\
                new_app)
            logging.info(str(datetime.datetime.now()) + \
                " - new record " + new_app.name + "is inserted in DB.")
        except Exception as e:
            self.connection.close()
            raise e

        # 삽입 정보 저장
        self.connection.commit()

    def not_updated_list(self):
        try:
            self.cursor.execute(\
                "select package from list where isDownloaded==?",('False',))
            package_list = self.cursor.fetchall()
        except Exception as e:
            self.connection.close()
            raise e
        return package_list

    def update_isdownload(self, package, isdownload):
        if(isdownload):
            self.cursor.execute(\
                "update list set isDownloaded=? where package==?",\
                ('True',package))
        else:
            self.cursor.execute(\
                "update list set isDownloaded=? where package==?",\
                ('False',package))
        self.connection.commit()
