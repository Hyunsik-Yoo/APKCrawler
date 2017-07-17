#-*- coding: utf-8 -*-
import unittest
import ConfigParser
from Crawler import *
from DBController import DBController
import sys
reload(sys)
sys.setdefaultencoding('utf-8')

class Test(unittest.TestCase):
    def setUp(self):
        config = ConfigParser.ConfigParser()
        config.read('config.ini')

        self.APK_DIRECTORY = config.get('Setting', 'APK_DIRECTORY')
        self.DB_DIRECTORY = config.get('Setting', 'DB_DIRECTORY')
        self.CHROME_DRIVER_DIRECTORY = config.get('Setting', 'CHROME_DRIVER_DIRECTORY')

        try:
            os.makedirs(APK_DIRECTORY)
        except:
            print('APK Directory가 이미 존재합니다.')

        self.db_connector = DBController(self.DB_DIRECTORY)
        self.db_connector.create_table()


#    def test_get_app_detail(self):
#        get_app_detail(['https://play.google.com/store/apps/details?id=com.kigle.project.tayocon_bus'],self.CHROME_DRIVER_DIRECTORY)
    def test_update_app_list(self):
        self.db_connector.update_app_list([[u'\ubf40\ub85c\ub85c \uc2a4\ucf00\uce58\ud31d,\ubf40\ub85c\ub85c,\uc2a4\ucf00\uce58\ud31d,sketch pop', u'com.nsocialnetwork.pororosketchpop', u'https://lh4.ggpht.com/EVw-04jxo_tHyZUr_asd1qm0xnNNFforW3mgA5CaEiH8mJNsBbN31GvMTStJGtWM88BP=w300-rw', u'2016\ub144 2\uc6d4 12\uc77c', None]])
   
if __name__ == '__main__':
    unittest.main()
