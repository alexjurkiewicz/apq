#!/usr/bin/env python

'''
Parse Postfix mailq and return a filtered list as JSON
'''

import sys, subprocess, re, time, datetime
try:
    import argparse
except ImportError:
    print >> sys.stderr, "Error: Can't import 'argparse'. Try installing python-argparse."
    sys.exit(1)

def parse_mq():
    '''
    Parse mailq output and return data as a dict.
    '''
    cmd = subprocess.Popen(['mailq'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = cmd.communicate()
    # 69 == postqueue: fatal: Queue report unavailable - mail system is down
    if cmd.returncode not in (0, 69):
        print >>sys.stderr, 'Error: mailq failed: "{}"'.format(stderr.strip())
    curmsg = None
    msgs = {}
    for line in stdout.strip().split('\n'):
        if not line or line.startswith('-Queue ID-') or line.startswith('--'):
            continue
        if line[0] in '0123456789ABCDEF':
            s = line.strip().split()
            curmsg = s[0]
            if curmsg[-1] == '*':
                status = 'active'
                curmsg = curmsg[:-1]
            else:
                status = 'deferred'
            msgs[curmsg] = {
                'size': s[1],
                'date': parse_mailq_date(' '.join(s[2:6])),
                'sender': s[-1],
                'reason': '',
                'status': status,
                }
        elif line.strip()[0] == '(':
            msgs[curmsg]['reason'] = line.strip()[1:-1].replace('\n', ' ')
        elif '@' in line: # pretty dumb check, I know
            msgs[curmsg]['recipient'] = line.strip()
        else:
            print >> sys.stderr, "Error: Unknown line in mailq output: %s" % line
            sys.exit(1)
    return msgs

def parse_ml():
    '''
    Read and parse messages from /var/log/mail.log
    '''
    lines = 0
    msgs = {}
    with open('/var/log/mail.log', 'rb') as f:
        for line in f.readlines():
            lines += 1
            if lines % 100000 == 0:
                # Technically off by one
                print >> sys.stderr, "Processed %s lines (%s messages)..." % (lines, len(msgs))
            try:
                l = line.strip().split()
                if l[4].startswith('postfix/smtpd') and l[6].startswith('client='):
                    curmsg = l[5].rstrip(':')
                    if curmsg not in msgs:
                        msgs[curmsg] = {
                            'source_ip': l[6].rsplit('[')[-1].rstrip(']'),
                            'date': parse_syslog_date(' '.join(l[0:3])),
                        }
                elif False and l[4].startswith('postfix/cleanup') and l[6].startswith('message-id='): # dont want msgid right now
                    curmsg = l[5].rstrip(':')
                    if curmsg in msgs:
                        msgid = l[6].split('=', 1)[1]
                        if msgid[0] == '<' and msgid[-1] == '>':
                            # Not all message-ids are wrapped in < brackets >
                            msgid = msgid[1:-1]
                        msgs[curmsg]['message-id'] = msgid
                elif l[4].startswith('postfix/qmgr') and l[6].startswith('from='):
                    curmsg = l[5].rstrip(':')
                    if curmsg in msgs:
                        msgs[curmsg]['sender'] = l[6].split('<', 1)[1].rsplit('>')[0]
                elif l[4].startswith('postfix/smtp[') and any([i.startswith('status=') for i in l]):
                    curmsg = l[5].rstrip(':')
                    if curmsg in msgs:
                        status_field = [i for i in l if i.startswith('status=')][0]
                        status = status_field.split('=')[1]
                        msgs[curmsg]['delivery-status'] = status
            except StandardError:
                print >> sys.stderr, "Warning: could not parse log line: %s" % repr(line)
    print >> sys.stderr, "Processed %s lines (%s messages)..." % (lines, len(msgs))
    return msgs

def parse_mailq_date(d):
    '''Parse a date in mailq's format (Fri Aug 30 16:47:05) and return a UNIX time'''
    # time.strptime defaults to a year of 1900. Try the current year but check this doesn't create a date in the future (eg if you run this on Jan 1 and there are things in the queue from Dec)
    t = time.strptime(d + ' ' + time.strftime('%Y'), '%a %b %d %H:%M:%S %Y')
    if t > time.localtime():
        t = time.strptime(d + ' ' + str(int(time.strftime('%Y')-1)), '%a %b %d %H:%M:%S %Y')
    return time.mktime(t)

def parse_syslog_date(d):
    '''Parse a date in syslog's format (Sep 5 10:30:36) and return a UNIX time'''
    t = time.strptime(d + ' ' + time.strftime('%Y'), '%b %d %H:%M:%S %Y')
    if t > time.localtime():
        t = time.strptime(d + ' ' + str(int(time.strftime('%Y')-1)), '%b %d %H:%M:%S %Y')
    return time.mktime(t)

def filter_on_msg_key(msgs, pattern, key):
    '''Filter msgs, returning only items where key 'key' matches regex 'pattern'.'''
    r = re.compile(pattern, re.IGNORECASE)
    msg_ids = [m for m in msgs if re.search(r, msgs[m][key])]
    msgs = dict((k, v) for k, v in msgs.iteritems() if k in msg_ids)
    return msgs

def filter_on_msg_age(msgs, condition, age):
    '''Filter msgs, returning only items where key 'date' meets 'condition' maxage/minage checking against 'age'.'''
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
    msg_ids = [msg for msg in msgs if f(msg)]
    msgs = dict((k, v) for k, v in msgs.iteritems() if k in msg_ids)
    return msgs

def format_msgs_for_output(msgs):
    '''Format msgs for output. Currently replaces time_struct dates with a string'''
    for msgid in msgs:
        msgs[msgid]['date'] = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(msgs[msgid]['date']))
    return msgs

def parse_args():
    '''
    Parse commandline arguments
    '''
    parser = argparse.ArgumentParser(description='Parse postfix mail queue.')
    parser.add_argument('-j', '--json', action='store_true', help="JSON output (default)")
    parser.add_argument('-y', '--yaml', action='store_true', help="YAML output")
    parser.add_argument('-c', '--count', action='store_true', help="Return only the count of matching items")
    parser.add_argument('--log', action='store_true', help="Experimental: Search /var/log/mail.log as well.")
    parser.add_argument('--reason', default=None, help="Select messages with a reason matching this regex")
    parser.add_argument('--recipient', default=None, help="Select messages with a recipient matching this regex")
    parser.add_argument('--sender', default=None, help="Select messages with a sender matching this regex")
    parser.add_argument('--maxage', default=None, help="Select messages younger than the given age. Format: age[{d,h,m,s}]. Defaults to seconds. eg: '3600', '1h'")
    parser.add_argument('--minage', default=None, help="Select messages older than the given age. Format: age[{d,h,m,s}]. Defaults to seconds. eg: '3600', '1h'")
    parser.add_argument('--exclude-active', action='store_true', help="Exclude items in the queue that are active")
    parser.add_argument('--only-active', action='store_true', help="Only include items in the queue that are active")

    args = parser.parse_args()

    if args.minage and args.minage[-1].isdigit():
        args.minage += 's'
    elif args.minage and args.minage[-1] not in 'smhd':
        print >> sys.stderr, "Error: --minage format is incorrect. Examples: 1800s, 30m"
        sys.exit(1)
    if args.maxage and args.maxage[-1].isdigit():
        args.maxage += 's'
    elif args.maxage and args.maxage[-1] not in 'smhd':
        print >> sys.stderr, "Error: --maxage format is incorrect. Examples: 1800s, 30m"
        sys.exit(1)
    if args.exclude_active and args.only_active:
        print >> sys.stderr, "Error: --exclude-active and --only-active are mutually exclusive"
        sys.exit(1)

    return args

def output_msgs(args, msgs):
    '''
    Take msgs and format it as requested.
    '''
    if args.count:
        print len(msgs)
    elif args.yaml:
        try:
            import yaml
        except ImportError:
            print >> sys.stderr, "Error: Can't import 'yaml'. Try installing python-yaml."
            sys.exit(1)
        print yaml.dump(msgs)
    else:
        import json
        print json.dumps(msgs, indent=4)


def main():
    '''
    Main function
    '''
    args = parse_args()

    # Do
    msgs = {}
    if args.log:
        msgs.update(parse_ml())
    msgs.update(parse_mq())
    if args.reason:
        msgs = filter_on_msg_key(msgs, args.reason, 'reason')
    if args.sender:
        msgs = filter_on_msg_key(msgs, args.sender, 'sender')
    if args.recipient:
        msgs = filter_on_msg_key(msgs, args.recipient, 'recipient')
    if args.minage:
        msgs = filter_on_msg_age(msgs, 'minage', args.minage)
    if args.maxage:
        msgs = filter_on_msg_age(msgs, 'maxage', args.maxage)
    if args.exclude_active or args.only_active:
        msg_ids = [m for m in msgs if 'status' in msgs[m] and msgs[m]['status'] != 'active']
        if args.exclude_active:
            msgs = dict((k, v) for k, v in msgs.iteritems() if k in msg_ids)
        else: # only_active
            msgs = dict((k, v) for k, v in msgs.iteritems() if k not in msg_ids)
    msgs = format_msgs_for_output(msgs)

    output_msgs(args, msgs)

if __name__ == '__main__':
    main()
