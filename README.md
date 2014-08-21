apq
===

Parse Postfix queue into JSON or YAML.

    usage: apq.py [-h] [-j] [-y] [-c] [--log] [--mailq-data MAILQ_DATA]
                  [--reason REASON] [--recipient RECIPIENT] [--sender SENDER]
                  [--parse-date] [--maxage MAXAGE] [--minage MINAGE]
                  [--exclude-active] [--only-active]
    
    Parse postfix mail queue.
    
    optional arguments:
      -h, --help            show this help message and exit
      -j, --json            JSON output (default)
      -y, --yaml            YAML output
      -c, --count           Return only the count of matching items
      --log                 Experimental: Search /var/log/mail.log as well.
      --mailq-data MAILQ_DATA
                            Use this file's contents instead of calling mailq
      --reason REASON, -m REASON
                            Select messages with a reason matching this regex
      --recipient RECIPIENT, -r RECIPIENT
                            Select messages with a recipient matching this regex
      --sender SENDER, -s SENDER
                            Select messages with a sender matching this regex
      --parse-date          Parse dates into a more machine-readable format (slow)
                            (implied by minage/maxage)
      --maxage MAXAGE, -n MAXAGE
                            Select messages younger than the given age. Format:
                            age[{d,h,m,s}]. Defaults to seconds. eg: 3600, 1h
      --minage MINAGE, -o MINAGE
                            Select messages older than the given age. Format:
                            age[{d,h,m,s}]. Defaults to seconds. eg: 3600, 1h
      --exclude-active, -x  Exclude items in the queue that are active
      --only-active         Only include items in the queue that are active

Todo
====

* Improve mail log parsing

Help
====

Email me (alex@jurkiewi.cz) or open a Github issue.
