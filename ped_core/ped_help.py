# Copyright 2009 James P Goodwin ped tiny python editor
""" module to hold the help text for the ped editor """
help_string = """
--------------------------------------------------------------------------------------------------
Help for ped James' simple python editor

keystroke               action
---------------------   --------------------------------------------------------------------------
alt-m or ctrl-k:        begin marking a span of characters
alt-c or ctrl-r:        begin marking a rectangle of characters
alt-l or ctrl-l:        begin marking lines
keypad minus or ctrl-x: cut marked characters
keypad plus or ctrl-c:  copy marked characters (also copies entire dialog prompt field)
insert or ctrl-v:       paste marked characters (also works in dialog prompt fields)
alt-g or ctrl-g:        goto a line by number
alt-w or ctrl-s:        save current file
alt-o or ctrl-w:        save current file to a different file
ctrl-f:                 show full name of current buffer or
                         in a streaming shell buffer toggle follow
alt-f:                  find files or search within files
alt-b:                  buffer list, switch buffers directly
all-d:                  kill the current buffer
alt-u:                  undo
alt-k:                  kill current window
alt-z:                  zoom current window
alt-x:                  exit and save all
esc:                    exit without saving
alt-p:                  previous buffer
alt-n:                  next buffer
alt-e:                  edit a new file
alt-h:                  split the current window horizontally
alt-v:                  split the current window vertically
tab:                    indent from the current position to the next tab stop
                        if lines are selected then indent the set of lines
shift-tab:              unindent from the current posiion or the nearest blank space to the left
                        if lines are selected then unindent the set of lines
up arrow, down arrow,
left arrow, right arrow,
page up, page down:     move cursor in file
up arrow:               in prompt fields in dialogs goes back through previous entries with wrap around
down arrow:             in prompt fields clears the input
ctrl-right arrow:       move to the end of the next (or current) word
ctrl-left arrow:        move to the start of the previous (or current) word
home:                   once beginning of line, twice top of window, three times top of file
end:                    once end of line, twice end of window, three times end of file
F10:                    run shell command capture output in a buffer
Shift F10:              open files from sftp
F2:                     refresh the screen
F5:                     search forward
Shift F5:               search backward
F6:                     search and replace
F3:                     search again
F4:                     next window
F7:                     transfer clipboard to x clipboard (if xclip is installed)
F8:                     transfer clipboard from x clipboard (if xclip is installed)
F9:                     toggle recording of keyboard macro
alt-a,F11:                    play back keyboard macro
alt-i,F1:               this help page is inserted in a buffer

Usage: {cmd |} ped [options] {files to edit}

A tiny text editor in python by James P Goodwin.

Options:
  -h, --help            show this help message and exit
  -f, --file_find       start in file find mode, optional args file find
                        pattern and text find pattern and recurse yes/no
  -s, --svn_browse      start in SVN browse mode, optional args path, file,
                        revision
  -c, --contrast        start display in higher contrast
  -r, --readonly        open file in read only mode
  -n, --newsbrowse      launch in news browse mode
  -b BACKUPROOT, --backuproot=BACKUPROOT
                        directory root for backup dir, if exists will be used,
                        otherwise homedir will be used
  -u USERNAME, --username=USERNAME
                        svn username
  -p PASSWORD, --password=PASSWORD
                        svn password
  -d, --dumpkeymap      dump the default keymap to ~/.pedkeymap and default
                        kedefs to ~/.pedkeydef and exit

--------------------------------------------------------------------------------------------------
Copyright 2020 James P Goodwin
--------------------------------------------------------------------------------------------------
"""


def get_help():
    """ wrapper so we can make the help generation a little more dynamic """
    return help_string
