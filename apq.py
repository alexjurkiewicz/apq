#!/usr/bin/env python

import sys, subprocess, argparse, re

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
                'date': ' '.join(s[2:6]),
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

def filter_msgs(msgs, reason=None, sender=None, recipient=None, size=None):
    def filter_on_msg_key(msgs, pattern, key):
        r = re.compile(pattern)
        msg_ids = filter(lambda m: re.search(r, msgs[m][key]), msgs)
        msgs = dict((k, v) for k,v in msgs.iteritems() if k in msg_ids)
        return msgs
    if reason:
        msgs = filter_on_msg_key(msgs, reason, 'reason')
    if sender:
        msgs = filter_on_msg_key(msgs, sender, 'sender')
    if recipient:
        msgs = filter_on_msg_key(msgs, recipient, 'recipient')
    return msgs


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Parse postfix mail queue data')
    parser.add_argument('-j', '--json', action='store_true', help="JSON output")
    parser.add_argument('-y', '--yaml', action='store_true', help="YAML output (default)")
    parser.add_argument('-c', '--count', action='store_true', help="Return only the count of matching items")
    parser.add_argument('--reason', default=None, help="Return only messages with a reason matching this regex pattern")
    parser.add_argument('--recipient', default=None, help="Return only messages with a recipient matching this regex pattern")
    parser.add_argument('--sender', default=None, help="Return only messages with a sender matching this regex pattern")
    args = parser.parse_args()

    msgs = parse_mq()
    msgs = filter_msgs(msgs, reason=args.reason, recipient=args.recipient, sender=args.sender)

    if args.count:
        print len(msgs)
    elif args.json:
        import json
        print json.dumps(msgs)
    else:
        import yaml
        print yaml.dump(msgs)
