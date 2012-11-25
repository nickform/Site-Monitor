#!/usr/bin/env python

# sample usage: checksites.py eriwen.com nixtutor.com yoursite.org

import os, sys, logging, time, urllib2, re, csv
from optparse import OptionParser, OptionValueError
from smtplib import SMTP
from getpass import getuser
from socket import gethostname


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

fieldnames = [ 'time',
        'internet was reachable',
        'status',
        'response time',
        'elapsed time since measurement started',
        'uptime since measurement started',
        'availability since measurement started',
        'time since last state change']

def get_statuses(statuses, url):
    # time
    statuses.append(time.time())
    # internet was reachable
    statuses.append(is_internet_reachable())

    startTime = time.time()
    siteStatus = get_site_status(url)
    elapsedTime = time.time() - startTime

    # status
    statuses.append(siteStatus)
    # response time
    statuses.append(elapsedTime if siteStatus == "up" else -1)

def calculate_statistics(statuses, previous_statuses):
    if previous_statuses == None:
        # 'elapsed time since measurement started',
        statuses.append(0.0)
        # 'uptime since measurement started',
        statuses.append(0.0)
        # 'availability since measurement started',
        statuses.append(0.0)
        # 'time since last state change']
        statuses.append(0.0)
    else:
        time_interval = statuses[0] - float(previous_statuses[0])
        state_transition_in_interval = statuses[2] != previous_statuses[2]
        uptime_in_interval = time_interval if ((not state_transition_in_interval) and statuses[2] == 'up') else 0.0
        # 'elapsed time since measurement started',
        statuses.append(float(previous_statuses[4]) + time_interval)
        # 'uptime since measurement started',
        statuses.append(float(previous_statuses[5]) + uptime_in_interval)
        # 'availability since measurement started',
        statuses.append(statuses[5] / statuses[4])
        # 'time since last state change'
        statuses.append(0.0 if state_transition_in_interval else float(previous_statuses[7]) + time_interval)

def main(url=None, filename=None):

    if url == None:
        # Get argument flags and command options
        (options,args) = get_command_line_options()
    
        # Print out usage if no arguments are present
        if len(args) != 2:
            print 'Usage:'
            print "\tPlease specify a single url followed by the name of the file to log status to."
            return
        
        url = args[0]
        filename = args[1]

    url = normalize_url(url)
    filename = add_extension(filename)

    logging.basicConfig(level=logging.WARNING, filename='checksites.log',
        format='%(asctime)s %(levelname)s: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S')

    # Get statuses
    statuses = []
    get_statuses(statuses, url)

    # Get any existing rows from the file if it exists...
    rows = []
    if os.path.isfile(filename):
        with open(filename, 'rb') as csvfile:
            # Read out the existing rows using a DictReader
            dr = csv.reader(csvfile)
            rows = list(dr)

    # If there are any existing rows, choose the last one as the previous_statues...
    numrows = len(rows)
    previous_statuses = None
    if numrows > 1:
        previous_statuses = rows[len(rows) - 1]
    # Otherwise initialise the rows list...
    else:
        rows.append(fieldnames)

    # Calculate the statistics for the new row...
    calculate_statistics(statuses, previous_statuses)

    # Append the new row...
    rows.append(statuses)

    # Write all rows to the file 
    with open(filename, 'wb') as csvfile:
        dw = csv.writer(csvfile)
        for row in rows:
          dw.writerow(row)


if __name__ == '__main__':
    # First arg is script name, skip it
    main()

