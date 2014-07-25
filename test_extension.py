# Copyright 2014 James P Goodwin ped tiny python editor
""" extension to test the extension_manager  """
from editor_common import Editor
from message_dialog import message


def ped_ext_info():
    """ return registration information for extension_manager """
    return ( "CMD_HELP", None, None, None, "test_extension" )


def ped_ext_invoke( cmd_id, target, ch ):
    """ do our thing with the target object """
    message( target.scr, "Help Extension", "On our way to help!" )
    return True
