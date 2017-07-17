#-*- coding: utf-8 -*-
import sqlite3
import datetime
import sys
import logging

class DBController:

    def __init__(self, db_directory):
        self.connection = sqlite3.connect(db_directory)
        self.cursor = self.connection.cursor()
 
    def commit_n_close(self):
        self.connection.commit()
        self.connection.close()

    def create_table(self):
        try:
            self.cursor.execute('CREATE TABLE list(appName, package, imgSrc, updateDate, isDownloaded, category)')
        except Exception as e:
            print(e)
            return False
        return True

    def get_category_app_list(self,category):
        try:
            self.cursor.execute('SELECT package FROM list WHERE category==(?)',(category[0],))
            package_list = []
            total_data = list(self.cursor)
            package_list = [tuple[0] for tuple in total_data]
        except Exception as e:
            raise e
        return package_list

    def get_all_app_name_list(self):
        try:
            self.cursor.execute('SELECT * FROM list')
            total_data = self.cursor.fetchall()
            app_name_list = [tuple[0] for tuple in total_data]
            return app_name_list
        except Exception as e:
            print(e)
            print('get_all_app_name_list error')
            self.connection.close()
            return False
 
    def update_date(self, app):
        try:
            self.cursor.execute("update list set updateDate=? where appName=?",(app[3], app[0]))
            self.cursor.execute("update list set isDownloaded=? where appName=?",(None,app[0]))
            #self.cursor.execute("update list set isDownloaded=(?) where appName='"+ app[0] + "'",(None,))
            self.connection.commit()
        except Exception as e:
            print(e)
            print('update_date error')
            self.connection.close()
            raise e
        return True

    def update_app_list(self, update_app_list, category):
        total_app_list = self.get_all_app_name_list()
        for app in update_app_list:
            app_name = app[0]
            if app_name in total_app_list:
                self.cursor.execute("select * from list where appName=(?)",(app_name,))
                total_data = self.cursor.fetchall()[0]
                if total_data[3] == app[3]:
                    continue
                else:
                    self.update_date(app)
                    logging.info(app_name + ' is updated')
            else:
                self.insert_app(app, category)
                logging.info(app_name + ' is inserted')
        return True

    def insert_app(self, insert_app, category):
        insert_app.append(category)
        try:
            self.cursor.execute("INSERT INTO list VALUES (?,?,?,?,?,?)", insert_app)
            print (str(datetime.datetime.now()) + " - new record " + insert_app[0] + "is inserted in DB.")
        except Exception as e:
            print (e)
            print ('close connection')
            self.connection.close()
            return False
        self.connection.commit()
        return True 

    def delete_null(self, failed_list):
        for package_name in failed_list:
            try:
                self.cursor.execute("DELETE FROM list WHERE package==(?)",(package_name,))
                #self.cursor.execute("DELETE FROM list where package =='" + package_name + "'")
            except Exception as e:
                print(e)
                print('close connection')
                self.connection.close()
                return False
        self.connection.commit()
        return True
       
