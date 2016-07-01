#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# ======================================================#
# Downloader for dm5
# Requirement:
# $ pip3 install BeautifulSoup4
# License: WTFPL 1.0
# Author: kuanyui
# ======================================================

import os, sys, re, subprocess
import urllib.request
import http.cookiejar
import imghdr

import execjs

from bs4 import BeautifulSoup
# From [2016-01-31 日 23:52]

class Main(object):
    def __init__(self):
        self.cookie_jar = http.cookiejar.CookieJar()
        # build an EMPTY opener, with a cookie jar:
        self.opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(self.cookie_jar))
        self.opener.addheaders = [('User-Agent', "Mozilla/5.0 (X11; Linux x86_64; rv:42.0) Gecko/20100101 Firefox/42.0")]
        
    def inputChapterPageURL(self, chapterPageURL):
        matched = re.match("http://www.dm5.com/m([0-9]+)/", chapterPageURL)
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
        filename = "{:03d}.{}".format(pageNum, ext)
        print("[Download Image]", filename)
        with open(filename, 'wb') as f:
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
            

main=Main()
main.inputChapterPageURL("http://www.dm5.com/m208342/")

        
#if __name__ == "__main__":
#    main = Main()
#    if len(sys.argv) > 1:
#        main.get(sys.argv[1])
#    else:
#        print("please input a nhentai url.")
#
