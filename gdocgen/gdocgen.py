import sys
import os
import fileinput
import re
import base64
import mimetypes
import argparse
from bs4 import BeautifulSoup
from email.message import EmailMessage
from email.utils import make_msgid
from premailer import transform
import smtplib
import datetime
import urllib
from urllib.parse import unquote


# Parse arguments
parser = argparse.ArgumentParser(description='Send GoogleDoc HTML as an email.')
parser.add_argument('--gdochtml', dest='gdochtml', action='store', required=True, default="", help='local path to the google doc html file')
parser.add_argument('--domain', dest='domain', action='store', required=True, default="", help='domain used in the embedded html')
parser.add_argument('--defaultlink', dest='defaultlink', action='store', required=True, default="", help='domain used in the embedded html')
parser.add_argument('--send', dest='send', action='store_true', help='send as an email')
parser.add_argument('--sendfrom', dest='sendfrom', action='store', required=False, default="", help='email from address')
parser.add_argument('--sendto', dest='sendto', action='store', required=False, default="", help='email to field (comma delimited)')
parser.add_argument('--sendsubject', dest='sendsubject', action='store', required=False, default="", help='email subject')
parser.add_argument('--draft', dest='draft', action='store_true', required=False, help='adding "draft" suffix with date to subject')
parser.add_argument('--smtphost', dest='smtphost', action='store', required=False, help='smtp host')
parser.add_argument('--smtpport', dest='smtpport', action='store', required=False, help='smtp port')
parser.add_argument('--smtpuser', dest='smtpuser', action='store', required=False, help='smtp user')
parser.add_argument('--smtppass', dest='smtppass', action='store', required=False, help='smtp pass')
args = parser.parse_args()

print(args)

# Get and validate the local html file
file = args.gdochtml
if not os.path.exists(file):
	print('Expected the file %s to exists' % file )
	sys.exit(1)
print('Using local file %s ' % file )

# Get and validate (TODO) the domain
domain = args.domain
print('Using domain %s ' % domain )

# Initialize the image link dictionary...
imgdct = {}

# Get and validate (TODO) the default image link
defaultlink = args.defaultlink
print('Using the default image link %s ' % defaultlink )

# Form a path to a local HTML file
tfile = os.path.join( os.path.dirname( file ), "transformed.html" )

# Email config...
sendIt = args.send
print('Sending: ', sendIt)

# Get email from...
mFrom = args.sendfrom  #George Williams <george.williams@gmail.com>
if sendIt and not mFrom:
	print('--sendfrom argument required when sending an email')
	sys.exit(1)

# Get email to...
mTo = args.sendto # [ 'George Williams <george.williams@gmail.com>' ] 
if sendIt and not mTo:
	print('--sendto argument required when sending an email')
	sys.exit(1)
mTo = mTo.split(",") # Needs to be a list

# Get email subject
mSubject = args.sendsubject
if sendIt and not mSubject:
	print('--sendsubject argument required when sending an email')
	sys.exit(1)

# Possibly add "draft" suffix with date
mDraft = args.draft
if sendIt and mDraft:
	mSubject = mSubject + " ( Draft Version at %s ) " % datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# Get SMTP info
if sendIt:
	if not args.smtphost or not args.smtpport or not args.smtpuser or not args.smtppass:
		print('SMTP information incomplete')
		sys.exit(1)
	smtpInfo = [ args.smtphost, int(args.smtpport), args.smtpuser, args.smtppass ]
	print('Using smtp info ', smtpInfo)
	
#
# The rest is the program...
#

# Read the html file...
fd = open(file,'r')
contents = fd.read()
fd.close()

# Parse with BS...
soup = BeautifulSoup(contents, 'html.parser')
html = soup.prettify() 

# Fixup googledoc hrefs...
ahrefs = soup.find_all('a',href=True)
for a in ahrefs:
	matches = re.match("https://www.google.com/url\?q=(.*)\&sa(.*)", a['href'])
	if matches:
		url = unquote(matches.groups()[0])
		print( "Warning: Changing URL to =", url)
		a['href']= url

# Fixup imgs ( make them links )...
imgs = soup.find_all('img')
for img in imgs:
	fn = os.path.join( os.path.dirname(file), img['src']) 
	if not os.path.isfile(fn):
		print('Warning: The path "',fn,'" does not exist')
		sys.exit(1)
	else:
		# Reparent to an href...
		par = img.parent
		img.extract()	

		link = defaultlink
		if img['title'] in imgdct.keys():
			link = imgdct[ img['title'] ]
		print("Warning: Using img alt link", img['title'], link)
		new_tag = soup.new_tag("a", href=link)
		par.insert(0, new_tag )
		new_tag.insert(0, img )

# If we are sending, then fix img's to refer to mime payload...
if sendIt:
	cid_dct = {}
	imgs = soup.find_all('img')
	for img in imgs:
		fn = os.path.join( os.path.dirname(file), img['src']) 
		if not os.path.isfile(fn):
			print(fn,' does not exist')
			sys.exit(1)
		else:
			# Replace img with CID...
			image_cid = make_msgid(domain=domain)
			cid_dct[image_cid] = fn
			img['src'] = "cid:" + image_cid[1:-1]


# Get the html...
html = soup.prettify()

# Transform CSS to inline style...
html_t = transform(html)

# Write intermediate output...
fd = open(tfile,'w')
fd.write(html_t)
fd.flush()
fd.close()
print('Warning: Wrote "', tfile, '"')

# If sending, then send it via smtp...
if sendIt:

	print("Warning: Sending...")

	# Craft an email message...
	msg = EmailMessage()
	msg['Subject'] = mSubject
	msg['From'] = mFrom
	msg['To'] = ", ".join(mTo)
	msg.add_alternative(html_t, subtype='html')

	# Add the image within the mime payload...
	for image_cid in cid_dct.keys():
		fn = cid_dct[image_cid]

		with open(fn, 'rb') as img:

			# know the Content-Type of the image
			maintype, subtype = mimetypes.guess_type(fn)[0].split('/')

			# attach it
			msg.get_payload()[0].add_related(img.read(), 
								 maintype=maintype, 
								 subtype=subtype, 
								 cid=image_cid)
		
	# Connect to SMTP server...
	try:  
	    server = smtplib.SMTP( smtpInfo[0], smtpInfo[1] )
	    server.ehlo()
	    server.starttls()
	    server.ehlo()
	except:  
	    print('Error: SMTP went wrong...')
	    print( sys.exc_info() )

	# Login...
	try:
	    server.login( smtpInfo[2], smtpInfo[3] )
	except:  
	    print('Error: Login went wrong...')
	    print( sys.exc_info() )

	# Send...
	try:
	    server.sendmail(msg['From'], mTo, msg.as_string())
	    server.close()
	except:  
	    print('Error: Send went wrong...')
	    print( sys.exc_info() )

	print("Email sent successfully! ")

print( "Done." )
