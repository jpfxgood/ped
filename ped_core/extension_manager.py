# Copyright 2014 James P Goodwin ped tiny python editor
""" extension manager to load extensions and bind them to commands """
import sys
import os
from ped_core import cmd_names
from ped_core import keymap
from ped_core import keytab

extensions = {}

# extension modules are python modules with the following two entry points
# ped_ext_info which takes no arguments and returns a tuple ( cmd_name, keymap_name {"EDITOR","DIALOG","MANAGER"}, keytab_key_name, keytab_key_name_ret, ext_name )
# cmd_name can be the same as an existing name which will be an override or it can be a new name
# keymap_name and keytab_key_name should be None if it is an override, if not it needs to be specified
# ped_ext_invoke which takes arguments ( Dialog or EditorManager or Editor, key ordinal we entered on )
# returns True to continue cmd processing or False to exit cmd processing allows for augmenting commands
# with a prior action

def register_extensions():
    """ search the directory ~/.pedextension for python modules that implement ped_ext_info, ped_ext_invoke methods """

    ped_extension_path = "~/.pedextension"
    if "PED_EXTENSION_PATH" in os.environ:
        ped_extension_path = os.environ["PED_EXTENSION_PATH"]

    ext_dir = os.path.expanduser( ped_extension_path )

    if os.path.exists(ext_dir) and os.path.isdir(ext_dir):
        pwd = os.getcwd()
        os.chdir(ext_dir)
        sys_path = list(sys.path)
        sys.path.append(ext_dir)
        for f in os.listdir(ext_dir):
            if f.endswith(".py"):
                ext_mod = __import__(f[:-3])
                if hasattr(ext_mod,"ped_ext_info") and hasattr(ext_mod,"ped_ext_invoke"):
                    cm_name, km_name, km_key, km_ret_key, ex_name  = ext_mod.ped_ext_info()
                    if cm_name in cmd_names.name_to_cmd:
                            extensions[cm_name] = ext_mod
                    else:
                        new_cmd = max(cmd_names.name_to_cmd.values())+1
                        cmd_names.cmd_to_name[new_cmd] = cm_name
                        cmd_names.name_to_cmd[cm_name] = new_cmd
                        if km_name == "EDITOR":
                            keymap.keymap_editor[keytab.name_to_key[km_key]] = ( new_cmd, keytab.name_to_key[km_ret_key] )
                        elif km_name == "MANAGER":
                            keymap.keymap_manager[keytab.name_to_key[km_key]] = ( new_cmd, keytab.name_to_key[km_ret_key] )
                        elif km_name == "DIALOG":
                            keymap.keymap_dialog[keytab.name_to_key[km_key]] = ( new_cmd, keytab.name_to_key[km_ret_key] )
                        extensions[cm_name] = ext_mod
        os.chdir(pwd)
        sys.path = sys_path

def is_extension( cmd_id ):
    """ test to see if there is an extension for a command id """
    return (cmd_names.cmd_to_name[cmd_id] in extensions)

def invoke_extension( cmd_id, target, ch ):
    """ invoke the extension returns true if processing should continue for augmenting or false if processing should exit for overrides """
    # target could be Editor, EditorManager, or Dialog object, plugin needs to know
    return extensions[cmd_names.cmd_to_name[cmd_id]].ped_ext_invoke( cmd_id, target, ch )
