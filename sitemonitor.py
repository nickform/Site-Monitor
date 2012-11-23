#!/usr/bin/env python

# sample usage: checksites.py eriwen.com nixtutor.com yoursite.org

import os, sys, logging, time, urllib2, re, csv, datetime
from optparse import OptionParser, OptionValueError
from smtplib import SMTP
from getpass import getuser
from socket import gethostname
from collections import OrderedDict


def generate_email_alerter(to_addrs, from_addr=None, use_gmail=False,
        username=None, password=None, hostname=None, port=25):

    if not from_addr:
        from_addr = getuser() + "@" + gethostname()

    if use_gmail:
        if username and password:
            server = SMTP('smtp.gmail.com', 587)
            server.starttls()
        else:
            raise OptionValueError('You must provide a username and password to use GMail')
    else:
        if hostname:
            server = SMTP(hostname, port)
        else:
            server = SMTP()            
        import pdb; pdb.set_trace()
        server.connect()
    
    if username and password:
        server.login(username, password)

        
    def email_alerter(message, subject='You have an alert'):
        server.sendmail(from_addr, to_addrs, 'To: %s\r\nFrom: %s\r\nSubject: %s\r\n\r\n%s' % (", ".join(to_addrs), from_addr, subject, message))

    return email_alerter, server.quit

def get_site_status(url):
    try:
        urlfile = urllib2.urlopen(url);
        status_code = urlfile.code
        if status_code in (200,302):
            return 'up'
    except:
        pass
    return 'down'

def get_headers(url):
    '''Gets all headers from URL request and returns'''
    try:
        return urllib2.urlopen(url).info().headers
    except:
        return 'Headers unavailable'

def check_site_status(url):
    startTime = time.time()
    status = get_site_status(url)
    endTime = time.time()
    elapsedTime = endTime - startTime

    if status != "up": elapsedTime = -1

    return status, elapsedTime

def is_internet_reachable():
    '''Checks Google then Yahoo just in case one is down'''
    statusGoogle, urlfileGoogle = get_site_status('http://www.google.com')
    statusYahoo, urlfileYahoo = get_site_status('http://www.yahoo.com')
    if statusGoogle == 'down' and statusYahoo == 'down':
        return False
    return True

def normalize_url(url):
    '''If a url doesn't have a http/https prefix, add http://'''
    if not re.match('^http[s]?://', url):
        url = 'http://' + url
    return url

def get_urls_from_file(filename):
    try:
        f = open(filename, 'r')
        filecontents = f.readlines()
        results = []
        for line in filecontents:
            foo = line.strip('\n')
            results.append(foo)
        return results
    except:
        logging.error('Unable to read %s' % filename)
        return []

def add_extension(filename):
    if not re.match('^.*\.csv$', filename):
        filename = filename + '.csv'
    return filename

def get_command_line_options():
    '''Sets up optparse and command line options'''
    usage = "Usage: %prog [options] url"
    parser = OptionParser(usage=usage)

    return parser.parse_args()

fns = ['datetime',
              'internet was reachable',
              'status',
              'response time',
              'elapsed time since measurement started',
              'uptime since measurement started',
              'availability since measurement started',
              'time since last state change']

def get_statuses(statuses, url):
    statuses['datetime'] = datetime.datetime.now().isoformat()
    statuses['internet was reachable'] = is_internet_reachable()
    startTime = time.time()
    site_status = get_site_status(url)
    statuses['site status'] = site_status
    statuses['response time'] = time.time() - startTime if site_status == "up" else -1

def calculate_statistics(statuses, previous_statuses):
    if previous_statuses == None:
        statuses['elapsed time since measurement started'] = -1
        statuses['uptime since measurement started'] = -1
        statuses['availability since measurement started'] = -1
        statuses['time since last state change'] = -1
    else:
        statuses['elapsed time since measurement started']
        statuses['uptime since measurement started']
        statuses['availability since measurement started']
        statuses['time since last state change']
        

def main():

    # Get argument flags and command options
    (options,args) = get_command_line_options()
    
    # Print out usage if no arguments are present
    if len(args) != 2:
        print 'Usage:'
        print "\tPlease specify a single url followed by the name of the file to log status to."
        return

    url = normalize_url(args[0])
    statsfile = add_extension(args[1])

    logging.basicConfig(level=logging.WARNING, filename='checksites.log',
        format='%(asctime)s %(levelname)s: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S')

    # Get statuses
    statuses = OrderedDict()
    get_statuses(statuses, url)
    for k, v in statuses.iteritems():
        print '{0}: {1}'.format(k, v)

    # open the file
    existing_rows = None
    if os.path.isfile(statsfile):
        with open(statsfile, 'rb') as csvfile:
            # Read out the existing rows using a DictReader
            dr = csv.DictReader(csvfile)
            existing_rows = list(dr)

    # If there is a previous row, calculate the new row...
    if existing_rows != None:
        numrows = len(existing_rows)
        print 'numrows = {0}'.format(numrows)
        if numrows > 0:
            print existing_rows[0]
    # Otherwise create the file...
    else:
        with open(statsfile, 'wb') as csvfile:
            dw = csv.DictWriter(csvfile, delimiter=',', filenames=fns)
            dw.writerow(fns)
            dw.writerow(statuses)

    # Write all rows to the file 


if __name__ == '__main__':
    # First arg is script name, skip it
    main()

