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
import execjs

from bs4 import BeautifulSoup
# From [2016-01-31 日 23:52]

class Main(object):
    chapterfunURIFormat = "http://www.dm5.com/m{chapterID}/chapterfun.ashx?cid={chapterID}&page={page}&key=&language=1&gtk=6"
    def __init__(self):
        self.cookie_jar = http.cookiejar.CookieJar()
        # build an EMPTY opener, with a cookie jar:
        self.opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(self.cookie_jar))
        self.opener.addheaders = [('User-Agent', "Mozilla/5.0 (X11; Linux x86_64; rv:42.0) Gecko/20100101 Firefox/42.0"),
                                  #('Content-Type', 'application/x-www-form-urlencoded'),
                                  #('X-Requested-With', 'XMLHttpRequest')
                                  
        ]
    
    def inputChapterPageURL(self, chapterPageURL):
        "ex: http://www.dm5.com/m204467/"
        matched = re.match("http://www.dm5.com/m([0-9]+)/", pagePageURL)
        if matched:
            chapterID = matched.group(1)
            
    def tryToGetChapterfunURIs(self, chapterID):
        """m204467      -> 204467
           rawChapterID    chapterID """
        JSfunc1 = self.getChapterFunctionStr(chapterID, 1)

    def getImageURI(self, chapterFunctionStr):
        # return [imageURI, nextImageURI]
        m = re.search("'([^']+)'.split\('\|'\)", chapterFunctionStr)
        if m:
            args = dict(enumerate(m.split('|')))
            imageURIFormat = "{protocol}://{first}.{n1}-{n2}-{n3}-{n4}.{cdn}.{com}/{k}/{p}/{chID}/{imgName}.{imgFormat}?cid={chID}&key={key}"
            imageURI = imageURIFormat.format(protocol=args[16],
                                             first=args[15],
                                             n1=args[20],
                                             n2=args[19],
                                             n3=args[10],
                                             n4=args[11],
                                             cdn=args[14],
                                             com=args[12],
                                             k=args[21],
                                             p=args[26],
                                             chID=args[3],
                                             imgName=args[25],
                                             imgFormat=args[4],
                                             key=args[9],
            )
            
    
    def getChapterFunctionStr(self, chapterID, page):
        req = urllib.request.Request(self.chapterfunURIFormat.format(chapterID=chapterID, page=page))
        req.add_header('Referer', 'http://www.dm5.com/m{}/'.format(chapterID))
        response = self.opener.open(req)
        return response.read().decode('utf-8')
            

main=Main()
print(execjs.eval(main.getChapterFunctionStr("208342", 5)))

        
#if __name__ == "__main__":
#    main = Main()
#    if len(sys.argv) > 1:
#        main.get(sys.argv[1])
#    else:
#        print("please input a nhentai url.")
#
