ped
===

ped is an editor and accompanying tools written in python.


Background
==========

I wrote ped over the last 6-7 years basically for my own use. I wanted an editor that emulated Brief(TM) and that I could easily extend and that would run in terminals on linux or other places that curses was available. I had been using a Brief(TM) emulation macro in emacs, but that was very limited and emacs is complicated to extend because of all of the mass of features and variants that exist. At the time I was working in python almost exclusively, and I realized that a lot of sophisticated features would be made relatively easy because python packages existed for them, so I embarked on writing my own editor.

I guess this was an act of vanity, stupidity, or stubbornness, but it was fun and I got what I wanted in the end and have been using the editor and extending it since then. I don't expect that this will be anyone's favorite editor but mine, but there might be some snippets of code or modules that others find useful, so please use the code as you like.

If you find bugs let me know or send me a fix I may apply it or fix the bug or not. I don't warrant that this code is good for any particular purpose. I wouldn't use it in a product without considerable hardening, re-factoring, and testing. 

I'm not interested in code reviews or critiques, I know it's a hack and that many parts of it are sloppy ill-considered, inefficient, under-implemented, buggy or just dangerous, please take this as read. If you're new to programming, don't take this as an example of good coding style. If you're someone google-stalking me about a job, please understand that this is not representative of my professional work, it's something I do in moments of scarce free time and with the above caveats.


Installation
============

Check out the source code to a path.

Put the path on your operating system's execution path.

Requires python 2.4 or better.

Requires a terminal that works with the python curses module.

Requires the following python modules: pygments, pexpect, beautiful soup v4, paramiko

If you are going to use the xref extension: whoosh
If you are going to use the im extension: twisted

Notes
=====

A recent addition is the sftp browser bound to Shift-F10 which allows browsing an SFTP site, downloading or uploading files, or opening a file from the SFTP site. This is still a work in progress, some of the UI is a little quirky as yet.

Also there is a stand alone script called collect which uses the ssh module to scan a remote directory for a particular file pattern and copy all matching files to a local subdirectory structure. I used it to consolidate lots of different archived old machines and my collections of mp3 files into one folder recently. You may find other uses for it. It is sort of tangential to this editor ;-)

I plan to move additional features out of the core editor and into extensions so that it will be easy to pare the editor down as needed. Candidates are svn browsing, and news reading, but I could probably also move file find/browse as well.

I'll probaby work on writing some automated tests, since right now I just try a bunch of things that I do all the time to make sure they still work and that's it. So there are often regressions that I only fix when I finally run into them.

Documentation
=============

Have a look at the wiki page for usage and configuration documentation.
