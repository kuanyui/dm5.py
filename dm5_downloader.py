#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# ======================================================#
# Downloader for dm5
# Requirement:
# $ pip3 install BeautifulSoup4 PyExecJS
# License: WTFPL 1.0
# Author: ono hiroko
# ======================================================

import os, re, sys, subprocess
import urllib.request
import http.cookiejar
import imghdr

import execjs

from bs4 import BeautifulSoup
# From [2016-01-31 日 23:52]

DOWNLOAD_DIRECTORY = "~/Downloaded Comics/"

class Singleton(type):
    __instance = None
    def __call__(cls, *args, **kwargs):
        if cls.__instance is None:
            cls.__instance = super().__call__(*args, **kwargs)
        return cls.__instance

class FileManager(metaclass=Singleton):

    def __init__(self):
        self.chapterTitle = ""
        self.bookTitle = ""
        global DOWNLOAD_DIRECTORY
        DOWNLOAD_DIRECTORY = os.path.expanduser(DOWNLOAD_DIRECTORY)
    
    def recursivelyMakeDirs(self, path):
        fullpath = os.path.expanduser(path)
        if not os.path.exists(fullpath):
            os.makedirs(fullpath)

    def getCurrentBookPath(self):
        return os.path.join(DOWNLOAD_DIRECTORY, self.bookTitle)
    
    def getCurrentChapterPath(self):
        return os.path.join(DOWNLOAD_DIRECTORY, self.bookTitle, self.chapterTitle)

    def getCurrentBookTitle(self):
        return self.bookTitle
    
    def setCurrentBook(self, bookTitle):
        """Set bookTitle as current book, and create a directory for it."""
        self.bookTitle = bookTitle
        self.recursivelyMakeDirs(self.getCurrentBookPath())

    def setCurrentChapter(self, chapterTitle):
        """Set chapterTitle as current chapter, and create a directory for it.
        setCurrentBook() is required first."""
        self.chapterTitle = chapterTitle
        self.recursivelyMakeDirs(self.getCurrentChapterPath())

    def getImageFilePath(self, imageFileName):
        return os.path.join(self.getCurrentChapterPath(), imageFileName)

    def getImageFileAmountInCurrentChapterDirectory(self):
        return len(os.listdir(self.getCurrentChapterPath()))
    
    def chapterExistsAndDownloadedCompletely(self, chapterTitle, totalPageAmount):
        """setCurrentBook() and setCurrentChapter() is required first."""
        self.chapterTitle = chapterTitle
        if (os.path.exists(self.getCurrentChapterPath()) and
            totalPageAmount == self.getImageFileAmountInCurrentChapterDirectory()):
            return True
        if os.path.exists(self.getZipFilePath()):
            return True
        return False

            
    def getZipFileName(self):
        return "{}.zip".format(self.chapterTitle)

    def getZipFilePath(self):
        return os.path.join(self.getCurrentBookPath(), self.getZipFileName())
    
    def zipCurrentChapter(self):
        zipFileName = self.getZipFileName()
        subprocess.Popen(["zip",
                          "--temp-path", self.getCurrentChapterPath(),
                          "-r", zipFileName, self.getCurrentChapterPath()],
                         stdout=subprocess.PIPE).stdout.read()
        # zip always place the output zipped file in `.` .... so move it
        os.rename(zipFileName, os.path.join(self.getCurrentBookPath(), zipFileName))



class CustomCookieHandler(urllib.request.BaseHandler):
    """Add custom cookie to cookiejar for opener"""
    def http_request(self, req):
        custom_cookie = 'isAdult=1'
        if not req.has_header("Cookie"):
            req.add_unredirected_header('Cookie', custom_cookie)
        else:
            original_cookie = req.get_header('Cookie')
            req.add_unredirected_header('Cookie', custom_cookie + '; ' + original_cookie)
        return req


class BaseDownloader:
    cookie_jar = http.cookiejar.CookieJar()
    #cookie = http.cookies.SimpleCookie()
    #cookie["isAdult"] = "1"
    #cookie_jar.set_cookie(cookie)
    # build an EMPTY opener, with a cookie jar:
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cookie_jar), CustomCookieHandler())
    opener.addheaders = [('User-Agent', "Mozilla/5.0 (X11; Linux x86_64; rv:42.0) Gecko/20100101 Firefox/42.0"),
                         #("Set-Cookie", "isAdult=1") #useless
    ]

    
class BookDownloader(BaseDownloader):

    def __init__(self):
        self.chapter_downloader = ChapterDownloader()
        
    def downloadBook(self, bookURL):
        title_chapterID_pageAmount = self.parseBook(bookURL)
        title_chapterID_pageAmount.reverse()  # Download from 001, 002, 003...
        print("[Book] Start to download book: {}".format(FileManager().getCurrentBookTitle()))
        for chapterTitle, chapterID, pageAmount in title_chapterID_pageAmount:
            FileManager().setCurrentChapter(chapterTitle)
            if FileManager().chapterExistsAndDownloadedCompletely(chapterTitle, pageAmount):
                print('[Chapter] {} has been downloaded completely. Skip.'.format(chapterTitle))
            else:
                print('[Chapter] Start to download {} ({} pages)'.format(chapterTitle, pageAmount))
                self.chapter_downloader.downloadChapter("http://www.dm5.com/{}/".format(chapterID))
                FileManager().zipCurrentChapter()
            
    def parseBook(self, bookURL):
        """return [(chapterTitle, chapterID) ...]"""
        req = urllib.request.Request(bookURL)
        print("Retrieveing & parsing book")
        with self.opener.open(req) as response:           
            html = response.read().decode('utf-8')
            soup = BeautifulSoup(html, 'html.parser')
            bookTitle=soup.find("title").string.split("_")[0]
            FileManager().setCurrentBook(bookTitle)
            uls = soup.find_all('ul', class_="nr6 lan2")
            title_chapterID_pageAmount = []
            for ul in uls:
                for li in ul.children:
                    a = li.find('a')
                    if (type(a) != int) and (a.get("class")): # <a> is a Python dict
                        _pageAmountString = li.contents[1]
                        pageAmount = int(re.findall("\d+", _pageAmountString)[0])
                        title = self.formatChapterNumber(a['title'])
                        title = re.sub("{} ?".format(bookTitle), "", title)
                        chapterID = a['href'][1:]
                        title_chapterID_pageAmount.append((title, chapterID, pageAmount))
            print("Found {} chapters in {}".format(len(title_chapterID_pageAmount), bookTitle))
        return title_chapterID_pageAmount

    def formatChapterNumber(self, title):
        """第3卷 --> 第003卷"""
        m = re.search(r"(\d+)", title)
        if not m:
            return title
        else:
           ddd = "{:03d}".format(int(m.group(1)))
           return re.sub(r"\d+", ddd, title)
            
            
class ChapterDownloader(BaseDownloader):
    def downloadChapter(self, chapterPageURL):
        matched = re.match("http://www.dm5.com/m(\d+)/", chapterPageURL)
        if not matched:
            raise ValueError("{} is not a valid chapter page url!!".format(chapterPageURL))
        else:
            chapterID = matched.group(1)
            with self.opener.open(self.getRefereredRequestObj(chapterPageURL)) as response:
                html = response.read().decode('utf-8')
                soup = BeautifulSoup(html, "html.parser")
                pageAmount = len(list(soup.find(id="pagelist").children)) - 1
                for pageNum in range(1, pageAmount + 1):
                    chapterFunc = self.getChapterFunctionStr(chapterID, pageNum)
                    imageURI = self.getImageURI(chapterFunc)
                    self.downloadImage(chapterID, imageURI, pageNum)

    def getRefereredRequestObj(self, uri, chapterID=None, pageNum=None):
        requestObj = urllib.request.Request(uri)
        requestObj.add_header('Referer', 'http://www.dm5.com/m{}-p{}/'.format(chapterID, pageNum))
        return requestObj

    def downloadImage(self, chapterID, imageURI, pageNum):
        req = self.getRefereredRequestObj(imageURI, chapterID, pageNum)
        response = self.opener.open(req)
        buffer = response.read()
        ext = imghdr.what(None, h=buffer)
        fileName = "{:03d}.{}".format(pageNum, ext)
        filePath = FileManager().getImageFilePath(fileName) # Get full file path
        print("[Download Image]", fileName)
        with open(filePath, 'wb') as f:
            f.write(buffer)
    
    def getImageURI(self, jsChapterFunctionStr):
        imageURIList = execjs.eval(jsChapterFunctionStr) # [imageURI, nextImageURI]
        return imageURIList[0]
    
    def getChapterFunctionStr(self, chapterID, pageNum):
        req = self.getRefereredRequestObj("http://www.dm5.com/m{chapterID}-p{pageNum}/chapterfun.ashx?cid={chapterID}&page={pageNum}&key=&language=1&gtk=6".format(chapterID=chapterID, pageNum=pageNum),
                                          chapterID,
                                          pageNum)
        response = self.opener.open(req)
        return response.read().decode('utf-8')
            

    
if __name__ == "__main__":
    book_downloader = BookDownloader()
    if len(sys.argv) > 1:
        book_downloader.downloadBook(sys.argv[1])
    else:
        print("please input a dm5 book link.")

