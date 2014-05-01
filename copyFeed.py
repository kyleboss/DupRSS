try:
    import urllib, sys, os, HTMLParser, re, subprocess, MySQLdb, ntpath, glob
    import boto, urllib2, time
    from StringIO import StringIO
    from globVars import *
    from boto.s3.connection import S3Connection
    from dateutil.parser import parse
    from bs4 import BeautifulSoup
    from hashlib import md5
    from time import localtime
    from urlparse import urljoin
    from xml.etree import ElementTree as ET
except:
    print "ERROR importing modules"

# Declare global variables
s3Conn = S3Connection(s3PublicKey, s3PrivateKey)
drBucket = s3Conn.get_bucket(s3Bucket)
rssUrl, db, dbConn, feedId, localDirLoc = "", "", "", "", ""
oper = sys.argv[1]

# Ensure all encoding is UTF-8 by default.
reload(sys)
sys.setdefaultencoding('utf-8')


def connectToDB():
    """
        connectToDB connects to the database that stores the users, feeds, and
        items.
        PARAMS: NONE
        RETURN: NONE
    """
    global db, dbConn
    try:
        db = MySQLdb.connect(host = dbHost, # your host, usually localhost
                             user = dbUser, # your username
                             passwd = dbPasswd, # your password
                             db = dbDb) # name of the data base
        dbConn = db.cursor()
        return True
    except Exception, e:
        print "Could not connect to database"
        try:
            print e
        except:
            raise e
        return False


def alterRssUrl():
    """
        alterRssUrl will format the URL until the urllib library can access it.
        For universality, www. is removed and http:// is added if first try
        does not succeed.
        PARAMS: NONE
        RETURN: NONE
    """
    global rssUrl
    valUrl = rssUrl
    try:
        ET.parse(urllib.urlopen(valUrl))
    except:
        valUrl = "http://" + valUrl
        try:
            ET.parse(urllib.urlopen(valUrl))
        except:
            return False
    rssUrl = valUrl
    return True

def getFeed():
    """
        getFeed formats and opens the RSS feed.
        PARAMS: NONE
        return: str -- the raw RSS feed file.
    """
    global rssUrl
    if (alterRssUrl()):
        tryUrl = urllib.urlopen(rssUrl)
        rssFile = tryUrl.read() # Point to contents of feed.
        tryUrl.close()
        return rssFile
    else:
        return False

def checkFeed():
    """
        checkFeed determines if the feed entered already exists in the database.
        If so, it simply updates the database. It not, it updates the database
        as well as the server's filesystem.
        PARAMS: NONE
        RETURN: BOOL: If the feed exists on the server and successfully inserted
    """
    global rssUrl, dbConn, feedId, localDirLoc
    
    # Get all feeds
    try:
        if (alterRssUrl()):
            sql = """SELECT Feed_id, Feed_folder FROM Feeds_DupRSS WHERE Feed_url =
                %s"""
            dbConn.execute(sql, (rssUrl,))
            feeds = dbConn.fetchall()
            # Tests if a feed from this URL exists for this user. Set feedId.
            if (feeds):
                feedId = feeds[0][0]
                localDirLoc = "/feeds/" + feeds[0][1]
                feedExists = FeedExistsLocally()
                return feedExists
        else:
                return -1
    except Exception, e:
        print "Something went wrong while checking if the feed exists!"
        try:
            print e
        except:
            raise e
        return -1
    
    # If feed does not exist for this user, insert one. Set feedId.
    else:
        if (oper == "stdRequest"):
            insertFeed()
            return True

def insertFeed():
    """
        insertFeed inserts the feed that corresponds to the URL input by the
        user if it has not yet been inserted.
        PARAMS: NONE
        RETURN: NONE
    """
    global feedId, localDirLoc, rssUrl
    try:
        rand = getRand()
        sql = """INSERT INTO Feeds_DupRSS(Feed_url, Feed_folder) VALUES 
            (%s, %s)"""
        dbConn.execute(sql, (rssUrl, rand))
        feedId = dbConn.lastrowid
        localDirLoc = "/feeds/" + rand
        db.commit()
    except Exception, e:
        print "There was an error while inserting the Feed"
        try:
            print e
        except:
            raise e

def FeedExistsLocally():
    """
        FeedExistsLocally determines if the feed exists on the server. If it
        doesn't, it deletes all reminants from the database.
        PARAMS: NONE
        RETURN: BOOL: True if the feed exists in the server filesystem.
    """
    global rssUrl, feedId
    if (not drBucket.get_key(localDirLoc + "/index.rss")):
        sql = """DELETE FROM Feeds_DupRSS WHERE Feed_url = %s"""
        dbConn.execute(sql, (rssUrl,))
        sql = """DELETE FROM Items_DupRSS WHERE Item_feed = %s"""
        dbConn.execute(sql, (feedId,))
        db.commit()
        return False
    else:
        return True

def grabImageTags(rssText):
    """
        grabImageTags downloads all images placed in <image> tags & updates
        the respective URLs.
        PARAMS: rssText -- the BeautifulSoup representation of the feed.
        RETURN: Updated BeautifulSoup representation of the feed.
    """
    
    # Search all <image> tags
    for currImage in rssText.findAll('image'):
        try:
            origUrl = currImage.url.contents[0]
            origUrl.replaceWith(urljoin(rssUrl, unicode(origUrl)))
            imgBase = re.sub(r'[^a-zA-Z0-9\.]', '', ntpath.basename(origUrl))
            newImgLoc = "/images/" + imgBase
            
            # ONLY download the image if the image DOESN'T exist.
            # Note: No random prefix included. We want to be able to check if
            # image in question already exists.
            if (not drBucket.get_key(localDirLoc + newImgLoc)):
                currImg = drBucket.new_key(localDirLoc + newImgLoc);
                try:
                    fp = StringIO(urllib2.urlopen(origUrl).read())
                    currImg.set_contents_from_file(fp)
                    currImg.set_acl('public-read')
                except Exception, e:
                    print "problem getting image"
                    try:
                        print e
                    except:
                        raise e
            # Replace URL in RSS Feed
            currImage.url.contents[0].replaceWith(serverDir + localDirLoc + \
                                                  newImgLoc)
        except:
            try:
                rand = getRand()
                currImage['src'] = urljoin(rssUrl, currImage['src'])
                imgBase = re.sub(r'[^a-zA-Z0-9\.]', '', ntpath.basename(currImage['src']))
                newImgLoc = "/images/" + rand + "_" + imgBase
                imgFile = drBucket.new_key(localDirLoc + newImgLoc)
                try:
                    fp = StringIO(urllib2.urlopen(currImage['src']).read())
                    imgFile.set_contents_from_file(fp)
                    imgFile.set_acl('public-read')
                except Exception, e:
                    print "PROBLEM retrieving image"
                    try:
                        print e
                    except:
                        raise e
                    pass
                currImage['src'] = serverDir + localDirLoc + newImgLoc
            except:
                pass
    return rssText

def insertItems(rssText, feedId):
    """
        insertItems inserts all of the items from the feed that have yet to be
        inserted into the database.
        PARAMS: rssText -- the RSS Feed in the form of a soup object.
        feedId -- The ID of the feed that corresponds to the URL that
        the user entered.
        RETURN: NONE
    """
    global dbConn, localDirLoc
    rssText = grabImageTags(rssText) # Take care of <image> tags
    htmlParser = HTMLParser.HTMLParser() # For unescaping
    
    # Parse through every RSS Item in the feed.
    for currItem in rssText.findAll('item'):
        try:
            # If we haven't already recorded the feed, insert it into the
            # database.
            if (len(itemExists(currItem)) == 0):
                # Update all <img> tags, thumbnails, etc.
                itemContent = getImgs(currItem)
                itemContent = currItem.encode('utf-8').strip() # Turn to str
                # Update all videos
                itemContent = getVids(itemContent)
                # Remove all XML tags that BeautifulSoup loves to add.
                removeTag = "&lt;?xml version=\"1.0\" encoding=\"utf-8\"?&gt;"
                itemContent = itemContent.replace(removeTag, "")
                itemContent = itemContent.replace("&lt;/xml&gt;", "")
                itemContent = [s for s in itemContent.splitlines() if s]
                itemContent = os.linesep.join(itemContent)
                # Parse item title and date.
                itemTitle = currItem.title.text
                try:
                    itemDate = currItem.pubDate.text
                except:
                    itemDate = time.strftime("%a, %d %b %Y %H:%M:%S %z")
                itemDate = parse(itemDate).strftime('%s')
                
                # Inserts the feed item into the database.
                sql = """INSERT INTO Items_DupRSS(Item_title, Item_feed,
                    Item_xml, Item_date) VALUES
                    (%s, %s, %s, FROM_UNIXTIME(%s))"""
                dbConn.execute(sql, (itemTitle, feedId, itemContent, itemDate))
        except Exception, e:
            print "ERROR (insertitems): "
            try:
                print e
            except:
                raise e
    db.commit()
    return rssText

def parseFeed():
    """
        parseFeed parses the feed file.
        PARAMS: NONE
        RETURN: str -- parsed feed file.
    """
    global rssUrl, feedId
    checkFeedResult = checkFeed()
    if (checkFeedResult > 0):
        rssFeed = getFeed()
        if (rssFeed):
            rssTextPre = BeautifulSoup("".join(rssFeed), features="xml")
            rssText = insertItems(rssTextPre, feedId) # Insert items into database.
            updateFeedInfo(rssText) # Updates channel information
        else:
            return False
    else:
        if (oper == "stdRequest" and checkFeedResult != -1):
            parseFeed()
        else:
            return False
    return True

def updateVids():
    allVideos = glob.glob(videosDir + "/*.mp4")
    
    for currVid in allVideos:
        print "transferring: " + currVid
        currKey = drBucket.new_key("/videos/" + re.sub(r'[^a-zA-Z0-9\.]', '', ntpath.basename(currVid)))
        currKey.set_contents_from_filename(currVid)
        currKey.set_acl('public-read')
        os.remove(currVid)


def getVids(itemContent):
    """
        getVids finds all the youtube videos, downloads them, and replaces
        absolute URLS with relative ones to the local copy.
        PARAMS: itemContent -- The feed item in BeautifulSoup form
        RETURN: The updated feed item in BeautifulSoup form
    """
    # YouTube URL patterns
    ytRegex = (
               r'(https?://)?(www\.)?'
               '(youtube|youtu|youtube-nocookie)\.?(\.com|\.be)'
               '(/watch\?v=|embed/|v/|.+\?v=)?([^&=%\?]{11})')
    youtubeVids = re.findall(ytRegex.decode(), str(itemContent))
    
    # Download all videos.
    for currVid in range(0, len(youtubeVids)):
       currVid = ''.join(youtubeVids[currVid])
       vidBase = ntpath.basename(currVid)
       vidBase = re.sub(r'[^a-zA-Z0-9\.]', '', vidBase)
       newVidLoc = vidBase + '.mp4'
       newVidAbs = serverDir + "/videos/" + newVidLoc
       #newVidHTML = ("<video width='320' height='240' controls>" + \
       #"<source src='" + newVidAbs + "' type='video/mp4'>" + \
       #"Your browser does not support the video tag." + \
       #"</video>")
       itemContent = itemContent.replace(currVid, newVidAbs)
       
       # Open a subprocess to download videos server-side and allow program
       # to move on.
       if (not drBucket.get_key("/videos/" + newVidLoc)):
           subprocess.Popen("/usr/local/bin/youtube-dl -f 18/22 -o " + videosDir + "/" +
                            newVidLoc + " --quiet "
                            + currVid, bufsize=0,
                            stdin=open("/dev/null", "r"),
                            stdout=open("/dev/null", "w"),
                            stderr=open("/dev/null", "w"), shell=True)
    if (len(youtubeVids) > 0):
        subprocess.Popen("sleep 180; " + sys.executable + " " +
                            os.path.realpath(__file__) + " updateVids",
                            bufsize=0, stdin=open("/dev/null", "r"),
                            stdout=open("/dev/null", "w"),
                            stderr=open("errLog.txt", "w"), shell=True)
    return itemContent

def getImgs(itemContent):
    """
        getImgs Takes all of the images from the item's XML, downloads them,
        and then replaces their absolute URL with a relative one pointing to the
        new image.
        PARAMS: itemContent -- Item XML as a soup object.
        RETURN: encoded string of XML with new img URLs replaced.
    """
    htmlParser = HTMLParser.HTMLParser()
    itemDesc = itemContent.description.encode('utf-8').strip()
    itemDesc = BeautifulSoup(htmlParser.unescape(itemDesc), features='xml')
    # Fetch all <img> tags (Handled differently because its an HTML tag)
    if (itemContent.description.content):
        for currImg in itemDesc.findAll('img'):
            try:
                rand = getRand()
                currImg['src'] = urljoin(rssUrl, currImg['src'])
                imgBase = re.sub(r'[^a-zA-Z0-9\.]', '', ntpath.basename(currImg['src']))
                newImgLoc = "/images/" + rand + "_" + imgBase
                imgFile = drBucket.new_key(localDirLoc + newImgLoc)
                try:
                    fp = StringIO(urllib2.urlopen(currImg['src']).read())
                    imgFile.set_contents_from_file(fp)
                    imgFile.set_acl('public-read')
                except:
                    pass
                currImg['src'] = serverDir + localDirLoc + newImgLoc
            except Exception, e:
                print "ERROR (imgs)"
                try:
                    print e
                except:
                    raise e
        # Update item description
        itemDesc = htmlParser.unescape(str(itemDesc))
        itemDesc = itemDesc.replace("<description>", "")
        itemDesc = itemDesc.replace("</description>", "")
        itemContent.description.contents[0].replaceWith(itemDesc)

    try:
        itemConTag = itemContent.encoded.encode('utf-8').strip()
        itemConTag = BeautifulSoup(htmlParser.unescape(itemConTag),
                                   features='xml')
        # Fetch all <img> tags (Handled differently because its an HTML tag)
        for currImg in itemConTag.findAll('img'):
            try:
                rand = getRand()
                currImg['src'] = urljoin(rssUrl, currImg['src'])
                imgBase = re.sub(r'[^a-zA-Z0-9\.]', '', ntpath.basename(currImg['src']))
                newImgLoc = "/images/" + rand + "_" + imgBase
                imgFile = drBucket.new_key(localDirLoc + newImgLoc)
                try:
                    fp = StringIO(urllib2.urlopen(currImg['src']).read())
                    imgFile.set_contents_from_file(fp)
                    imgFile.set_acl('public-read')
                except:
                    pass
                currImg['src'] = serverDir + localDirLoc + newImgLoc
            except Exception, e:
                print "ERROR (imgs)"
                try:
                    print e
                except:
                    raise e

        # Update item description
        itemConTag = htmlParser.unescape(str(itemConTag))
        itemConTag = itemDesc.replace("&lt;encoded&gt;", "")
        itemConTag = itemDesc.replace("&lt;/encoded&gt;", "")
        itemContent.encoded.contents[0].replaceWith(itemConTag)
    except:
        pass

    # Fetch all <media:thumbnail> tags
    for currImg in itemContent.findAll('thumbnail'):
        try:
            rand = getRand()
            currImg['url'] = urljoin(rssUrl, currImg['url'])
            imgBase = re.sub(r'[^a-zA-Z0-9\.]', '', ntpath.basename(currImg['url']))
            newImgLoc = "/images/" + rand + "_" + imgBase
            imgFile = drBucket.new_key(localDirLoc + newImgLoc)
            try:
                fp = StringIO(urllib2.urlopen(currImg['url']).read())
                imgFile.set_contents_from_file(fp)
                imgFile.set_acl('public-read')
            except:
                pass
            currImg['url'] = serverDir + localDirLoc + newImgLoc
        except Exception, e:
            print "ERROR (thumbnail imgs)"
            try:
                print e
            except:
                raise e

    # Fetch all <enclose> tags
    for currImg in itemContent.findAll('enclose'):
        try:
            rand = getRand()
            currImg['url'] = urljoin(rssUrl, currImg['url'])
            imgBase = re.sub(r'[^a-zA-Z0-9\.]', '', ntpath.basename(currImg['url']))
            newImgLoc = "/images/" + rand + "_" + imgBase
            imgFile = drBucket.new_key(localDirLoc + newImgLoc)
            try:
                fp = StringIO(urllib2.urlopen(currImg['url']).read())
                imgFile.set_contents_from_file(fp)
                imgFile.set_acl('public-read')
            except:
                pass
            currImg['url'] = serverDir + localDirLoc + newImgLoc
        except Exception, e:
            print "ERROR (enclose imgs)"
            try:
                print e
            except:
                raise e
    return itemContent

def writeRss():
    """
        writeRSS writes the parsed RSS feed to the zip file.
        PARAMS: finalRss -- the parsed RSS feed
        RETURN: NONE
    """
    global feedId
    
    # Obtain the feed from database
    sql = """SELECT Feed_rssInfo FROM Feeds_DupRSS WHERE Feed_id = %s"""
    dbConn.execute(sql, (feedId,))
    feeds = dbConn.fetchall()
    feedTxt = str(feeds[0][0])
    # Select all Feed items pertaining to the URL
    sql = """SELECT Item_xml FROM Items_DupRSS WHERE Item_feed = %s ORDER BY item_date DESC"""
    dbConn.execute(sql, (feedId,))
    feeds = dbConn.fetchall()
    
    # Append feed items one by one.
    for theFeed in feeds:
        feedTxt += theFeed[0]
    
    # Add ending tags and write to file.
    feedTxt += "</channel></rss>"
    rssFile = drBucket.new_key(localDirLoc + '/index.rss')
    rssFile.set_contents_from_string(feedTxt)
    rssFile.set_acl('public-read');
    print "Your feed can be found at " + serverDir + localDirLoc + "/index.rss"

def itemExists(theItem):
    """
        itemExists determines if the item has already been inserted into the
        database.
        PARAMS: theItem -- BeautifulSoup XML object containing the feed item.
        RETURN: A list of all the feeds with the same title from the same feed
                as the current item.
    """
    
    # Format item title & date
    itemTitle = theItem.title.text
    # Tests to see if there is already an article with this name & under
    # this user that already exists.
    sql = """SELECT Items_DupRSS.Item_title FROM Items_DupRSS INNER JOIN
        Feeds_DupRSS ON Items_DupRSS.Item_feed = Feeds_DupRSS.Feed_id
        WHERE Items_DupRSS.Item_title = %s AND Items_DupRSS.Item_feed = %s"""
    dbConn.execute(sql, (itemTitle, feedId))
    return dbConn.fetchall()

def updateFeedInfo(theFeed):
    """
        updateFeedInfo extracts only the channel information from the feed
        and updates the feed row with it.
        PARAMS: soup -- the soup element of the feed.
        RETURN: NONE
    """
    
    # Remove all contents EXCEPT the channel tags.
    for dItem in theFeed.findAll('item'):
        dItem.replaceWith('')
    htmlParser = HTMLParser.HTMLParser()
    channel = htmlParser.unescape(theFeed.encode('utf-8').strip())
    channel = channel.replace("<?xml version=\"1.0\" encoding=\"utf-8\"?>", "")
    channel = channel.replace("</channel>", "")
    channel = channel.replace("</rss>", "")
    channel = channel.strip()
    # Insert channel tags into the database.
    sql = """UPDATE Feeds_DupRSS SET Feed_rssInfo=%s WHERE Feed_url = %s"""
    dbConn.execute(sql, (channel, rssUrl))
    db.commit()

def getRand():
    """
        getRand simply generates a pseudorandom string.
        PARAMS: NONE
        RETURN: a pseudorandom string.
    """
    return "%s" % (md5(str(localtime())).hexdigest())

def getAllFeeds():
    """
        updateAllFeeds takes all of the feeds currently in the database and
        updates their items.
    """
    global rssUrl
    
    # Get all feeds in database.
    sql = "SELECT Feed_url FROM Feeds_DupRSS"
    dbConn.execute(sql)
    feeds = dbConn.fetchall()
    
    # Update each feed one by one.
    for currFeed in feeds:
        rssUrl = currFeed[0]
        print "Updating: " + rssUrl
        subprocess.Popen(sys.executable + " " + os.path.realpath(__file__) +
                         " stdRequest " + rssUrl, bufsize=0,
                         stdin=open("/dev/null", "r"),
                         stdout=open("/dev/null", "w"),
                         stderr=open("errLog.txt", "w"), shell=True)
        #if(parseFeed()):
        #writeRss()

def main():
    global rssUrl
    if (connectToDB()):
        if (oper == "stdRequest"): # Standard request from the CGI
            rssUrl = sys.argv[2]
            if(parseFeed()):
                writeRss()
            else:
                print "Feed URL invalid."
        if (oper == "updateAll"): # Updates ALL of the RSS feeds in database
            getAllFeeds()
        if (oper == "updateVids"):
            updateVids()
main()
