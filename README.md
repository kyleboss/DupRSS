# _DupRSS_

_Description: DupRSS is a tool that mirrors RSS feeds from an external source to an AWS account. DupRSS was initially created to provide Chinese citizens the ability to view blocked RSS content._

## Project Setup

1. _Set up an Amazon Web Services (AWS) account & make a bucket for DupRSS._
2. _Make a MySQL Database using the SQL code provided in sql.sql_
3. _Create a directory for videos to be stored and make sure it has appropriate write and read permissions._
4. _Create a text file for logging errors and make sure it has appropriate write permissions._
5. _Supply the globVars.py file with the appropriate information. Make sure the FULL location is given for videosDir & errorLoc._
6. _Make Cron Jobs to update the feeds. Examples are provided in CronExample._
7. _Make sure the following python libraries are installed: urllib, sys, os, HTMLParser, re, subprocess, MySQLdb, ntpath, glob, boto, urllib2, time, StringIO, parser, bs4, hashlib, urlparse, etree, cgi, cgitb, copy, json_

That's it! Once these steps are fulfilled, the rest is easy. It's worth mentioning that the majority of DupRSS is a command line Python script (copyFeed.py). However, there is also a graphic-interface as well for it included in the DupRSS.cgi file

## Troubleshooting & Useful Tools

_Update all of the feeds (e.g. transfer new content from external feed to S3 for each feed)._
> - python copyFeed.py updateAll 

_Move all videos in the local video directory to S3._
> - python copyFeed.py updateVids

_Add feed to database or update a single feed._
> - python copyFeed.py stdRequest http://URL_HERE.com
