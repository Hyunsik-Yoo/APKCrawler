from Crawler import *

def main():
    playstore_crawler = Crawler(is_desktop = True)
    playstore_crawler.crawl_old()


if __name__ == '__main__':
    main()
