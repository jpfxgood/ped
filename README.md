ped
===

ped is an editor and accompanying tools written in python.


Background
==========

I wrote ped over the last 6-7 years basically for my own use. I wanted an editor that emulated Brief(TM) and that I could easily extend and that would run in terminals on linux or other places that curses was available. I had been using a Brief(TM) emulation macro in emacs, but that was very limited and emacs is complicated to extend because of all of the mass of features and variants that exist. At the time I was working in python almost exclusively, and I realized that a lot of sophisticated features would be made relatively easy because python packages existed for them, so I embarked on writing my own editor.

I guess this was an act of vanity, stupidity, or stubborness, but it was fun and I got what I wanted in the end and have been using the editor and extending it since then. I don't expect that this will be anyone's favorite editor but mine, but there might be some snippets of code or modules that others find useful, so please use the code as you like.

Installation
============

Check out the source code to a path.

Put the path on your operating system's execution path.

Requires python 2.4 or better.

Requires a terminal that works with the python curses module.

Requires the following python modules: pygments, pexpect, beautiful soup v4

If you are going to use the xref extension: whoosh
If you are going to use the im extension: twisted

Notes
=====

At the moment I'm working on optimizing the display rendering to not display more than it needs to, this reduces screen flash and on big displays improves editing performance. This is still a work in progress so there are some display artifacts that I'm still fixing.

I plan to move additional features out of the core editor and into extensions so that it will be easy to pare the editor down as needed. Candidates are svn browsing, and news reading, but I could probably also move file find/browse as well.

I'll probaby work on writing some automated tests, since right now I just try a bunch of things that I do all the time to make sure they still work and that's it. So there are often regressions that I only fix when I finally run into them.

Documentation
=============

Have a look at the wiki page for usage and configuration documentation.

