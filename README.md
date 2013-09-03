apq
===

A better postqueue/mailq wrapper for human and computer consumption

    usage: apq.py [-h] [-j] [-y] [-c] [--reason REASON] [--recipient RECIPIENT]
                  [--sender SENDER]
    
    Parse postfix mail queue data
    
    optional arguments:
      -h, --help            show this help message and exit
      -j, --json            JSON output
      -y, --yaml            YAML output (default)
      -c, --count           Return only the count of matching items
      --reason REASON       Return only messages with a reason matching this regex
                            pattern
      --recipient RECIPIENT
                            Return only messages with a recipient matching this
                            regex pattern
      --sender SENDER       Return only messages with a sender matching this regex
                            pattern


Todo
====

* Optionally parse mail logs for past messages
* More useful date handling (filter based on older/newer than, relative dates)
