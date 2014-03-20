#!/usr/bin/python
print("Content-type: text/html")
print
try:
    import cgi, cgitb, urllib, sys, os, tempfile, zipfile, HTMLParser, re, subprocess, MySQLdb, lxml
except Exception, e:
    print "ERROR"
    print e
from dateutil.parser import parse
from bs4 import BeautifulSoup
from urlparse import urljoin
cgitb.enable()
form = cgi.FieldStorage()

tempdir, zipFile, rssUrl, db, dbConn, userId = "", "", "", "", "", ""

def connectToDB():
    global db, dbConn
    try:
        db = MySQLdb.connect(host="localhost", # your host, usually localhost
                             user="root", # your username
                             passwd="password", # your password
                             db="DupRSS") # name of the data base
        dbConn = db.cursor()
    except Exception, e:
        print "ERROR"
        print e

def urlGiven():
        """
        urlGiven determines if the user has submitted the form
        and is waiting for a file to be parsed.
        PARAMS: NONE
        RETURN: BOOL -- True if user is waiting for RSS file
                False otherwise
        """
        submitted = form.getvalue('submitted')
        try:
                return submitted
        except:
                return False


def getFormHtml():
        """
        getFormHtml outputs HTML for the form
        PARAMS: NONE
        RETURN: The HTML for the form
        """
        formHtml = """
        <form action='#' method='POST'>
        E-Mail: <input type='text' name='email'><br />
        URL: <input type='text' name='rssUrl'><br />
        <input type='hidden' name='submitted' value='True' />
        <input type='submit' value='Submit' />
        </form>
        """
        return formHtml

def getImgs(soup):
        """
        getImages Grabs all of the images in the RSS file,
        puts them into the zipped folder, and re-writes their
        path directly in the RSS file.
        PARAMS: soup -- the HTML object representing the RSS feed.
        RETURN: BeautifulSoup object -- the RSS Feed representation
                with updated img links.
        """
        global tempDir, zipFile, rssUrl
        h = HTMLParser.HTMLParser()
        for i in soup.find_all('item'):
                d = BeautifulSoup(h.unescape(i.description.string))
                try:
                    tempFile = tempfile.NamedTemporaryFile(delete=False, dir=tempDir + "/images")
                    tempName = tempFile.name
                    urljoin(rssUrl, d.img['src'])
                    tempFile.write(urllib.urlopen(d.img['src']).read())
                    tempFile.close()
                    d.img['src'] = "/images/" + os.path.basename(tempName)
                    zipFile.write(tempName,"RSS Feed/images/" + os.path.basename(tempName))
                    i.description.string = str(d)
                except Exception, e:
                        pass
        return soup

def getFeed():
        """
        getFeed formats and opens the RSS feed.
        PARAMS: NONE
        return: str -- the raw RSS feed file.
        """
        global rssUrl
        rssUrl = rssUrl.replace('www.','')
        try:
                tryUrl = urllib.urlopen(rssUrl)
        except:
                rssUrl = "http://" + rssUrl
        tryUrl = urllib.urlopen(rssUrl)
        rssFile = tryUrl.read()
        tryUrl.close()
        return rssFile

def insertFeed():
    global rssUrl, dbConn, userId
    sql = "SELECT Feed_id FROM Feeds_DupRSS WHERE Feed_url = %s AND Feed_user = %s"
    dbConn.execute(sql, (rssUrl, userId))
    feeds = dbConn.fetchall()
    if (feeds):
        feedId = feeds[0][0]
    else:
        sql = ("INSERT INTO Feeds_DupRSS(Feed_url, Feed_user) VALUES (%s, %s)")
        dbConn.execute(sql, (rssUrl, userId))
        feedId = dbConn.lastrowid
    db.commit()
    return feedId

def insertItems(soup, feedId):
    global dbConn
    for i in soup.findAll('item'):
        try:
            itemContent = ''.join(i.findAll(text=True)).encode('utf-8').strip()
            itemDate = i.find('pubDate').text
            itemTitle = i.find('title').text
            itemDate = parse(itemDate).strftime('%s')
            sql = "SELECT Items_DupRSS.Item_date FROM Items_DupRSS INNER JOIN Feeds_DupRSS ON (Items_DupRSS.Item_feed = Feeds_DupRSS.Feed_id AND Feeds_DupRSS.Feed_user = %s) WHERE Items_DupRSS.Item_title = %s  AND Items_DupRSS.Item_date >= %s"
            dbConn.execute(sql, (userId, itemTitle, itemDate))
            feeds = dbConn.fetchall()
            if (feeds):
                    print "PASSING"
                    pass
            else:
                   sql = ("INSERT INTO Items_DupRSS(Item_title, Item_feed, Item_xml, Item_date) VALUES (%s, %s, %s, FROM_UNIXTIME(NOW()))")
                   dbConn.execute(sql, (i.find('title').text, feedId, itemContent))
        except Exception, e:
            print "ERROR (insertitems): "
            print e
    db.commit()

def getUser(userEmail):
    global rssUrl, dbConn, userId
    sql = "SELECT User_id FROM Users_DupRSS WHERE User_email = %s"
    dbConn.execute(sql, (userEmail,))
    users = dbConn.fetchall()
    if (users):
        userId  = users[0][0]
    else:
        sql = ("INSERT INTO Users_DupRSS(User_email) VALUES (%s)")
        dbConn.execute(sql, (userEmail,))
        userId = dbConn.lastrowid
    db.commit()


def parseFeed():
        """
        parseFeed parses the feed file.
        PARAMS: NONE
        RETURN: str -- parsed feed file.
        """
        global tempDir, zipFile, rssUrl
        rssFeed = getFeed()
        print rssFeed
        soup = BeautifulSoup("".join(rssFeed), features="xml")
        #print soup
        h= HTMLParser.HTMLParser()
        finalizedRss = str(getImgs(soup))
        #print finalizedRss
        feedId = insertFeed()
        insertItems(soup, feedId)
        """ytRegex = (
                r'(https?://)?(www\.)?'
                '(youtube|youtu|youtube-nocookie)\.?(\.com|\.be)'
                '(/watch\?v=|embed/|v/|.+\?v=)?([^&=%\?]{11})')
        youtubeVids = re.findall(ytRegex.decode(), str(rssFeed))
        for i in range(0, len(youtubeVids)):
                #print ''.join(youtubeVids[i])
                currVid = ''.join(youtubeVids[i])
                tempFile = tempfile.NamedTemporaryFile(dir=tempDir + '/videos')
                tempName = tempFile.name
                tempFile.close()
                #cmd = ['/var/chroot/home/content/20/9302720/html/cgi/myenv/bin/youtube-dl', '-o', tempName, '--quiet', currVid]
                #subprocess.call(cmd)
                #REMOVE THIS COMMENT WHEN 504 FIXED
                #zipFile.write(tempName,"RSS Feed/videos/" + os.path.basename(tempName))
                """
        return finalizedRss

def writeRss(finalRss):
        """
        writeRSS writes the parsed RSS feed to the zip file.
        PARAMS: finalRss -- the parsed RSS feed
        RETURN: NONE
        """
        global tempDir, zipFile
        tempFile = tempfile.NamedTemporaryFile(delete=False, dir=tempDir, suffix='.rss')
        tempFile.write(finalRss)
        tempName = tempFile.name
        tempFile.close()
        zipFile.write(tempName,"RSS Feed/" + os.path.basename(tempName))
        zipFile.close()

def zipTransfer():
        """
        zipTransfer transfers all files from the temporary directory
        to the zipFile and hands the zipped file to client.
        PARAMS: rssUrl -- the URL of the RSS Feed
        RETURN: NONE
        """
        global tempDir, rssUrl
        with open(tempDir + 'z','rb') as zipped:
                print zipped.read()

def main():
        global zipFile, tempDir, rssUrl
        feedName = "NONE"
        if (urlGiven()):
                rssUrl = form.getvalue('rssUrl')
                userEmail = form.getvalue('email')
                connectToDB()
                getUser(userEmail)
                tempDir = tempfile.mkdtemp()
                tempImg = os.makedirs(tempDir + '/images')
                tempVid = os.makedirs(tempDir + '/videos')
                #print 'Content-Type:application/octet-stream; name=' + rssUrl + '.zip'
                #print 'Content-Disposition: attachment; filename=' + rssUrl + '.zip'
                #print
                #zipFile = zipfile.ZipFile(tempDir + 'z', 'w')
                finalRss = parseFeed()
        #writeRss(finalRss)
                #zipTransfer()
        else:
                print("Content-type: text/html")
                print
                print "<html>"
                print "<body>"
                formHtml = getFormHtml()
                print formHtml
                print "</body>"
                print "</html>"
main()


