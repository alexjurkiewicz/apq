#!/usr/bin/env python

import sys, subprocess, argparse, re, time, datetime

def parse_mq():
    try:
        mqstdout = subprocess.check_output('mailq')
    except subprocess.CalledProcessError:
        print "Could not run mailq!"
        sys.exit(1)
    curmsg = None
    msgs = {}
    for line in mqstdout.strip().split('\n'):
        if not line or line.startswith('-Queue ID-') or line.startswith('--'):
            continue
        if line[0] in '0123456789ABCDEF':
            s = line.strip().split()
            curmsg = s[0].rstrip('*')
            msgs[curmsg] = {
                'size': s[1],
                'date': parse_mailq_date(' '.join(s[2:6])),
                'sender': s[-1],
                'reason': '',
                }
        elif line.strip()[0] == '(':
            msgs[curmsg]['reason'] = line.strip()[1:-1].replace('\n', ' ')
        elif '@' in line: # pretty dumb check, I know
            msgs[curmsg]['recipient'] = line.strip()
        else:
            print "Unknown line: %s" % line
            sys.exit(1)
    return msgs

def parse_mailq_date(d):
    '''Parse a date in mailq's format and return a UNIX time'''
    # time.strptime defaults to a year of 1900. Try the current year but check this doesn't create a date in the future (eg if you run this on Jan 1 and there are things in the queue from Dec)
    t = time.strptime(d + ' ' + time.strftime('%Y'), '%a %b %d %H:%M:%S %Y')
    if t > time.localtime():
        t = time.strptime(d + ' ' + str(int(time.strftime('%Y')-1)), '%a %b %d %H:%M:%S %Y')
    return time.mktime(t)

def filter_msgs(msgs, reason=None, sender=None, recipient=None, minage=None, maxage=None):
    def filter_on_msg_key(msgs, pattern, key):
        '''Filter msgs, returning only items where key 'key' matches regex 'pattern' '''
        r = re.compile(pattern)
        msg_ids = filter(lambda m: re.search(r, msgs[m][key]), msgs)
        msgs = dict((k, v) for k,v in msgs.iteritems() if k in msg_ids)
        return msgs
    def filter_on_msg_age(msgs, condition, age):
        '''Filter msgs, returning only items where key 'date' meets the criteria 'age'.
        Internal format is {+-}age{dhms} (CLI assumes '-' by default)'''
        # Determine mode
        if age[-1] == 's':
            age_secs = int(age[:-1])
        elif age[-1] == 'm':
            age_secs = int(age[:-1]) * 60
        elif age[-1] == 'h':
            age_secs = int(age[:-1]) * 60 * 60
        elif age[-1] == 'd':
            age_secs = int(age[:-1]) * 60 * 60 * 24
        # Create lambda
        now = datetime.datetime.now()
        if condition == 'minage':
            f = lambda m: (now - datetime.datetime.fromtimestamp(msgs[m]['date'])).total_seconds() >= age_secs
        elif condition == 'maxage':
            f = lambda m: (now - datetime.datetime.fromtimestamp(msgs[m]['date'])).total_seconds() <= age_secs
        else:
            assert False
        # Filter
        msg_ids = filter(f, msgs)
        msgs = dict((k, v) for k,v in msgs.iteritems() if k in msg_ids)
        return msgs

    if reason:
        msgs = filter_on_msg_key(msgs, reason, 'reason')
    if sender:
        msgs = filter_on_msg_key(msgs, sender, 'sender')
    if recipient:
        msgs = filter_on_msg_key(msgs, recipient, 'recipient')
    if minage:
        msgs = filter_on_msg_age(msgs, 'minage', minage)
    if maxage:
        msgs = filter_on_msg_age(msgs, 'maxage', maxage)
    return msgs

def format_msgs_for_output(msgs):
    '''Format msgs for output. Currently replaces time_struct dates with a string'''
    for msgid in msgs:
        msgs[msgid]['date'] = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(msgs[msgid]['date']))
    return msgs

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Parse postfix mail queue.')
    parser.add_argument('-y', '--yaml', action='store_true', help="YAML output (default)")
    parser.add_argument('-j', '--json', action='store_true', help="JSON output")
    parser.add_argument('-c', '--count', action='store_true', help="Return only the count of matching items")
    parser.add_argument('--reason', default=None, help="Select messages with a reason matching this regex")
    parser.add_argument('--recipient', default=None, help="Select messages with a recipient matching this regex")
    parser.add_argument('--sender', default=None, help="Select messages with a sender matching this regex")
    parser.add_argument('--maxage', default=None, help="Select messages younger than the given age. Format: age[{d,h,m,s}]. Defaults to seconds. eg: '3600', '1h'")
    parser.add_argument('--minage', default=None, help="Select messages older than the given age. Format: age[{d,h,m,s}]. Defaults to seconds. eg: '3600', '1h'")

    args = parser.parse_args()

    # Validate
    if args.minage and args.minage[-1].isdigit():
        args.minage += 's'
    if args.minage and args.minage[-1] not in 'smhd':
        print "--minage format is incorrect. Examples: 1800s, 30m"
        sys.exit(1)
    if args.maxage and args.maxage[-1].isdigit():
        args.maxage += 's'
    if args.maxage and args.maxage[-1] not in 'smhd':
        print "--maxage format is incorrect. Examples: 1800s, 30m"
        sys.exit(1)

    # Do
    msgs = parse_mq()
    msgs = filter_msgs(msgs, reason=args.reason, recipient=args.recipient, sender=args.sender, minage=args.minage, maxage=args.maxage)
    msgs = format_msgs_for_output(msgs)

    if args.count:
        print len(msgs)
    elif args.json:
        import json
        print json.dumps(msgs)
    else:
        import yaml
        print yaml.dump(msgs)
