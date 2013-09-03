apq
===

A better postqueue/mailq wrapper for human and computer consumption

    usage: apq.py [-h] [-j] [-y] [-c] [--reason REASON] [--recipient RECIPIENT]
                  [--sender SENDER] [--maxage MAXAGE] [--minage MINAGE]
    
    Parse postfix mail queue.
    
    optional arguments:
      -h, --help            show this help message and exit
      -j, --json            JSON output (default)
      -y, --yaml            YAML output
      -c, --count           Return only the count of matching items
      --reason REASON       Select messages with a reason matching this regex
      --recipient RECIPIENT
                            Select messages with a recipient matching this regex
      --sender SENDER       Select messages with a sender matching this regex
      --maxage MAXAGE       Select messages younger than the given age. Format:
                            age[{d,h,m,s}]. Defaults to seconds. eg: '3600', '1h'
      --minage MINAGE       Select messages older than the given age. Format:
                            age[{d,h,m,s}]. Defaults to seconds. eg: '3600', '1h'

Todo
====

* Optionally parse mail logs for past messages
* More useful date handling (filter based on older/newer than, relative dates)
