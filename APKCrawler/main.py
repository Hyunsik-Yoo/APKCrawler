from Crawler import *
import sys
import argparse


def str2bool(v):
    if v.lower() in ('yes', 'true', 't', 'y', '1'):
        return True
    elif v.lower() in ('no', 'false', 'f', 'n', '0'):
        return False
    else:
        raise argparse.ArgumentTypeError('Boolean value expected.')

def main():
    arg_parser = argparse.ArgumentParser(description='APK크롤러 실행법')
    arg_parser.add_argument('--method', help='실행시키고자 하는 기능(crawl_new,\
        crawl_old, update_apk)')
    arg_parser.add_argument('--desktop', type=str2bool, default=True,\
        help='Desktop으로 실행시키려면 true, Server로 실행시키려면 false')

    args = arg_parser.parse_args()

    if(args.desktop != None):
        desktop = args.desktop

    if(args.method != None):
        method = args.method

    playstore_crawler = Crawler(is_desktop = desktop)

    if(method == "crawl_new"):
        playstore_crawler.crawl_new()
    elif(method == "crawl_old"):
        playstore_crawler.crawl_old()
    elif(method == "update_apk"):
        playstore_crawler.update_apk()

    playstore_crawler.close()



if __name__ == '__main__':
    main()
