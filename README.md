ped
===

ped is an editor and accompanying tools written in python.


Background
==========

I wrote ped since 2009  basically for my own use. I wanted an editor that emulated Brief(TM) and that I could easily extend and that would run in terminals on linux or other places that curses was available. I had been using a Brief(TM) emulation macro in emacs, but that was very limited and emacs is complicated to extend because of all of the mass of features and variants that exist. When I started the project I was working in python almost exclusively, and I realized that a lot of sophisticated features would be made relatively easy because python packages existed for them, so I embarked on writing my own editor.

I guess this was an act of vanity, stupidity, or stubbornness, but it was fun and I got what I wanted in the end and have been using the editor and extending it since then. I don't expect that this will be anyone's favorite editor but mine, but there might be some snippets of code or modules that others find useful, so please use the code as you like.

If you find bugs let me know or send me a fix I may apply it or fix the bug or not. I don't warrant that this code is good for any particular purpose.


Installation
============

Install from pypy:

    python3 -m pip install ped-editor

OR

Check out the source code to a path OR download the release .zip file and unzip there.

Put the path on your operating system's execution path.

Requires python 3.8 or better.

Requires a terminal that works with the python curses module.

There is a requirements.txt file, you can do: pip install -r requirements.txt

Notes
=====

I've recently added a suite of pytest tests that cover about 78% of the code.

You can run them by doing the following in the source directory:

    export SSH_DIALOG_BASEPATH= { an ssh path of the form ssh://host/dir:port that points to a test sftp server where files can be get/put and directories created }

    export SSH_DIALOG_USERNAME= { ssh username to run the test as, needs permissions for the above }

    export SSH_DIALOG_PASSWORD= { ssh password for that user, you are responsible for the security of it }

    python -m pytest tests

OR with coverage:

    coverage run --source=. --omit=comment_extension.py,dummy_extension.py,lib/*,tests/* -m pytest tests


Documentation
=============

Have a look at the wiki page for usage and configuration documentation.
