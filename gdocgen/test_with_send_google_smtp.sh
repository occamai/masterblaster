#!/bin/bash

# Note, you should have a file called "LOCALDATA" where you have defined the shell variables below
source ./LOCALDATA
echo "$EMAILFROM"
echo "$EMAILTO"
echo "$SMTPUSER"
echo "$SMTPPASS"

python gdocgen.py --gdochtml "Newsletter/Newsletter.html" --domain "google.com" --defaultlink "http://www.google.com/"  --send  --sendfrom "$EMAILFROM" --sendto "$EMAILTO" --sendsubject "It's A Newsletter" --draft --smtphost "smtp.gmail.com" --smtpport "587" --smtpuser "$SMTPUSER" --smtppass "$SMTPPASS"

