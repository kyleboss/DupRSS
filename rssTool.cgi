#!/var/chroot/home/content/20/9302720/html/myenv/bin/python2.7
import cgi, cgitb, urllib, sys, os, tempfile, zipfile, HTMLParser
from bs4 import BeautifulSoup
from urlparse import urljoin
cgitb.enable()
form = cgi.FieldStorage()

tempdir, zipFile, rssUrl = "", "", ""

def urlGiven():
	"""
	urlGiven determines if the user has submitted the form
	and is waiting for a file to be parsed.
	PARAMS:	NONE
	RETURN:	BOOL -- True if user is waiting for RSS file
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
	PARAMS:	NONE
	RETURN:	The HTML for the form
	"""
	formHtml = """
	<form action='#' method='POST'>
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
	PARAMS:	soup -- the HTML object representing the RSS feed.
	RETURN:	BeautifulSoup object -- the RSS Feed representation
		with updated img links.
	"""
	global tempDir, zipFile, rssUrl
        h = HTMLParser.HTMLParser()
	for i in soup.find_all('item'):
                d = BeautifulSoup(h.unescape(i.description.string))
                try:
                        tempFile = tempfile.NamedTemporaryFile(delete=False, dir=tempDir)
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
	rssUrl = form.getvalue('rssUrl')
        try:
                tryUrl = urllib.urlopen(rssUrl)
        except:
                rssUrl = "http://" + rssUrl
        rssUrl = urllib.urlopen(rssUrl)
        rssFile = rssUrl.read()
        rssUrl.close()
	return rssFile

def parseFeed():
	"""
	parseFeed parses the feed file.
	PARAMS:	NONE
	RETURN:	str -- parsed feed file.
	"""
	global tempDir, zipFile
	rssFeed = getFeed()
	soup = BeautifulSoup("".join(rssFeed))
	h= HTMLParser.HTMLParser()
	finalizedRss = str(getImgs(soup))
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
	print 'Content-Type:application/octet-stream; name=' + rssUrl + '.zip'
        print 'Content-Disposition: attachment; filename=' + rssUrl + '.zip'
        print
        with open(tempDir + 'z','rb') as zipped:
        	print zipped.read()

def main():
	global zipFile, tempDir, rssUrl
	feedName = "NONE"
    	if (urlGiven()):
		rssUrl = form.getvalue('rssUrl')
		tempDir = tempfile.mkdtemp()
		zipFile = zipfile.ZipFile(tempDir + 'z', 'w')
        	finalRss = parseFeed()
		writeRss(finalRss)
		zipTransfer()
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