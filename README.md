# MobileArchive-APKCrawler
Google Play Store에 존재하는 APK파일을 자동으로 수집해주는 크롤러 입니다.
config.ini파일에 존재하는 카테고리 url들을 입력으로 받고 카테고리별 인기차트에서 상위 300개 앱에 대한 메타정보를 크롤링하여 sqlite db로 만듭니다. 그 이후, Play Store unofficial API 를 통해 수집된 전체 메타정보에 대한 APK파일들을 다운받습니다.
만약 첫번째 크롤링이 아니라면, 이전에 수집했던 DB와 새로 크롤링한 DB를 합하여 최신정보와 최신 APK파일로 갱신시켜줍니다.

# Architecture
![Architecture](FlowChart.png)
Google Play Store Crawler 와 APK Downloader 두가지 모듈로 나눠집니다.
Google Play Store Crawler는 Python3 버전으로 구현되었으면, APK Downloader는 Python2버전으로 구현되었습니다.
(APK Downloader 에서는 Google Play Unofficial Python API를 사용하는데 해당 라이브러리가 Python3버전을 지원하지 않기 때문에 2버전으로 구현하였습니다.)

# Installation
Docker Image로 설치하는 방법과, 직접설치하는 방법 두가지가 존재합니다.
## Docker
> [Docker Hub 바로가기](docker push dbgustlr92/apkcrawler)
> <pre><code> docker pull dbgustlr92/apkcrawler </code></pre>

## 직접설치
> 하단의 Google Play Unofficial Python API 설치
> 하단의 필요한 python 라이브러리 설치

# Usage
Dependency문제를 모두 해결한 다음 앱에대한 메타정보를 먼저 크롤링 합니다.
<pre><code> python3 Crawler.py </code></pre>
config.ini에 정의된 카테고리별로 300개앱들이 크롤링되므로 오랜시간이 걸립니다.
크롤링이 끝나면 appList.db 파일에 다음과같은 테이블형태로 데이터가 저장됩니다.

| appName | package | imgSrc | updateDate | isDownloaded | category |
| --------|:-------:| ------:| ----------:| ------------:| --------:|
| 네이버 사전 & 번역기 | com.nhn.android | https://lh3.... | 2017년 4월 13일 | 1 | EDUCATION |
| 암기고래- 말해주는 단어장! | com.belugaedu... | https://lh3.... | 2017년 4월 17일 | 1 | EDUCATION|

위와같은 DB가 정상적으로 생성되면 APK다운로더를 실행시켜줍니다.
<pre><code> python download.py </code></pre>
위 코드를 실행시키면 appList.db 파일의 앱 메타정보를 읽고 isDownloaded floag가 없는 앱들의 APK파일을 다운로드 받고 1로 업데이트합니다.

# Dependency
## Play Store Crawler
> Python 3 +
> Xvfb
<pre><code> sudo apt-get install xvfb </code></pre>
<pre><code> sudo pip3 install -r requirements.txt </code></pre>

## Play Store unoffical API
> Python 2 +
> [Google Play Unofficial Python API](https://github.com/egirault/googleplay-api)
