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

Make sure that ~/.local/bin is on your PATH

OR

Check out the source code to a path OR download the release .zip file and unzip there.

Put the path on your operating system's execution path and the modules on your PYTHONPATH.

Requires python 3.6.9 or better.

Requires a terminal that works with the python curses module.

There is a requirements.txt file, you can do: pip install -r requirements.txt

Notes
=====

Documentation
=============

Have a look at the wiki page for usage and configuration documentation.

Contributing
============

If you're interested in contributing these are the instructions. Please understand that while you retain the copyright for any of your work, once it is contributed it is licensed under the same MIT license as the rest of the project.

To get set up you should do the following:

  *   Create your own fork of the repository on github <https://guides.github.com/activities/forking/>
  *   Clone this repo to your local machine ( see same directions )
  *   Make changes and test them, the regression tests run with the runtests script need to pass
  *   Sometimes you may need to add new tests if your functionality isn't covered in the existing tests
  *   Please update this README or send us a request to udpate the wiki with documentation
  *   Create and send a pull request upstream and we'll review the change and decide if it should go in, we may have changes or additions before we accept it. Not every change will be accepted, but you are free to use your change from your own fork.

Some of the finer details of the dev environment:

  *   You need Python 3.6.9 ( or better I've tested up to 3.8)  available on your machine
  *   I'd recommend creating a local python environment using venv something like:
    *    python3 -m pip install venv
    *    in your checkout directory: python3 -m venv .
       *    when you start working in the directory: source bin/activate
          *    first time do: python3 -m pip install -r requirements.txt
          *    and: python3 -m pip install -r dev\_requirements.txt
    *    ./runtests will run the tests you can select individual tests using -k see the pytest documentation for other useful options
  *   make sure that when you're running your changes that PYTHONPATH is set to your checkout directory
  *   there are some environment variables required by the tests:
    *    SSH\_DIALOG\_USERNAME = username for a test ssh/sftp server
    *    SSH\_DIALOG\_PASSWORD = password for a test ssh/sftp server
    *    SSH\_DIALOG\_BASEPATH = target folder expressed as ssh://host:port/directory/subdirectory, you should be comfortable with anything below this path being deleted

If you happen to use Microsoft Visual Studio Code here is a template for launching and debugging both tests and the code, put this in launch.json for your working folder:

    {
        // Use IntelliSense to learn about possible attributes.
        // Hover to view descriptions of existing attributes.
        // For more information, visit: https://go.microsoft.com/fwlink/?linkid=830387
        "version": "0.2.0",
        "configurations": [
            {
                "name": "Python: Current File",
                "type": "python",
                "request": "launch",
                "program": "/home/yourhome/ped-git/scripts/ped",
                "args": ["ped_core/editor_common.py"],
                "env": { "PYTHONPATH":"." },
                "console": "externalTerminal"
            },
            {
                "name": "Python: Pytest",
                "type": "python",
                "request": "launch",
                "module": "pytest",
                "args": [ "tests", "-k", "test_Editor_wrapped" ],
                "env" : { "PYTHONPATH":".", "SSH_DIALOG_BASEPATH":"ssh://your-ssh-server:22/home/yourhome/ssh_tmp", "SSH_DIALOG_USERNAME":"your_user_name",
    "SSH_DIALOG_PASSWORD":"*******" },
                "console": "externalTerminal"
            }
        ]
    }


