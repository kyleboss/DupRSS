#!/usr/bin/python 

import re 
import string 
import sys 
import httplib 
import urllib2 
from xml.dom import minidom 

## CGI Version 

import cgi 
import cgitb; cgitb.enable() 
form = cgi.FieldStorage() # holds data from form 

feedname = form["selection"].value 

print feedname 

## PHP Version 
#feedname = sys.argv[1] 

## listinfo retrieves the list information from file 
## 'feedlist' and returns it in a dictionary. The 
## key of the dictionary is the name of the feed. 

def listinfo(type): 
    infofile = "feedlist." + type 
    datafile = open(infofile, "r") 
    line = datafile.readline() 

    record = {} 

    while line: 
        data = string.split(line, ';') 
        feedname = data[0] 
        address = data[1] 
        record[feedname] = address 
        line = datafile.readline() 

    return record 

## Populate a dictionary feedinfo using function listinfo 
feedinfo = listinfo("dat") 

## The model feed, class ModelFeed includes two basic methods beyond 
## __init__. 


## feeddata retrieves the RSS feed from the Internet, using 
## the address from the dictionary value. links then may be called to 
## cull out the item information and reformat it into HTML. 
class ModelFeed: 
    def __init__(self): 
        self.data = [] 

    def feeddata (self, feedname): 
        feedaddress = feedinfo[feedname] 
        return feedaddress 

    def links (self, address): 
        file_request = urllib2.Request(address) 
        file_opener = urllib2.build_opener() 
        file_feed = file_opener.open(file_request).read() 
        file_xml = minidom.parseString(file_feed) 

        item_node = file_xml.getElementsByTagName("item") 

        i = 0 
        linkdata = "" 
        while i < len(item_node): 

            node_notabs = re.sub("\t", "", item_node[i].toxml()) 
            node_no_xml = re.sub('(<title>)|(<\/title>)|(<link>)|(<\/link>)|(<description>)|(<\/description>)|(<item>)|(<\/item>)', '', node_notabs) 
            node_parts = re.split("\n", node_no_xml) 

            ftitle = node_parts[1] 
            flink = node_parts[2] 
            fdesc = node_parts[3] 
            linkdata = linkdata + "<a href=\"" + flink + "\" target=\"target\" title=\"" + fdesc + "\">" + ftitle + "</a><br>\n" 
            i = i + 1 

        data = imgdata + linkdata 

        return data 

## nodeValue whittles through XML form to get to the actual data 
def nodeValue(doc, nodename): 
    dom = minidom.parseString(doc) 
    node = dom.getElementsByTagName(nodename) 
    norm = node[0].toxml() 
    value = norm 

    return value 

## bodyfn is a function to form the body of the HTML output 
def bodyfn(feedname): 
    feed = ModelFeed() 
    feedurl = feed.feeddata(feedname) 
    body = feed.links(feedurl) 
    return body 


## The main thing is to keep the main() thing the main thing. 
def main(): 
    i = 0 
    body = bodyfn(feedname) 
    output = body 
    print output 

## If __name__ does not equal __main__, the program executes silently 
## without any output. 
if __name__ == "__main__": 
    main()