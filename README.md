# MasterBlaster - A Collection Of Useful Programmatic Marketing Tools

Includes:
* (gdocgen) A way to generate HTML-based email newsletter from a Google Doc


## gdocgen

A way to generate HTML-based email newsletter from a Google Doc.

### Prerequisites

* Python 3 Installation ( I used the Anaconda 3.7 Package for Mac )
* Packages ( I installed via "conda" )
  * BeautifulSoup
  * premailer
  * smtplist

### Example

* Go into the "gdocgen" folder
* run the "test.sh" script
* it will create a stand-alone html file that you can use in an email campaign ( ie, via MailChimp ) based on the "NewsLetter" example in the folder

### Use Your Google Doc

* Craft a google doc in your google account
* Download as HTML to your local machine
* Use this path for the --gdochtml argument for gdocgen.py ( see test.sh )
* This will create a standalone html file that you can use in an emal campaign ( ie, via MailChip )

### Sending Via SMTP

See the "test_send_with_google_smtp.sh" to have gdocgen.py also send via google smtp relay.
