Hello! This is my chat application that was created to be compliant with RFC 1459 of the
Internet Chat Relay Protocol. It is still missing some intended features, and there are few bugs
to be sorted out, but the basic functionality is there. 

Getting Started
Download and unzip the directory.

Prerequisites
This application was created for compatibility with Python 3.x.

Installing
The Chatserver.py can be run from the command line with 'python Chatserver.py' or
in your IDE.
Then run main.py.

USAGE: python main.py [-h hostname] [-u username] [-p port] [-c conf_file]
[-t test_file] [-l log]

-h --hostname 
-u --username 
-p --port
-c --conf_file (TBD)
-t --test_file 
-l --log

hostname: 'localhost'/127.0.0.1
port: 50000

Ex: python main.py
      python main.py -h 127.0.0.1 -u geegee -p 50000  

Running the tests

A test client along with test files containing commands that are fed to the server, can be found
in the 'files' folder.
The test client works by running as follows:

type 'python TestClient.py' at the command line, and it will execute
the test file that is specified in the code.

