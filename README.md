# MobileArchive-APKCrawler
모바일 아카이브의 APK크롤러 파트.
Google Play Store에 존재하는 APK파일을 자동으로 수집해주는 크롤러 입니다.
APK Crawler는 두가지 순서로 진행됩니다.
1. Google Play Store 카테고리별 인기차트에 존재하는 앱들의 메타정보를 수집합니다.(앱이름, 패키지이름, 앱이미지)
2. Play Store unoffical API를 사용해 APK를 다운받습니다.

# Dependency
##Play Store Crawler
> Python 3 +
> Xvfb
<pre><code> sudo apt-get install xvfb </code></pre>
<pre><code> sudo pip3 install -r requirements.txt </code></pre>

## Play Store unoffical API
> Python 2 +
> [Google Play Unofficial Python API](https://github.com/egirault/googleplay-api)
