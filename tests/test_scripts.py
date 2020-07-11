import pexpect
import os
import sys
from ped_core import keytab


pyfind_output = "/home/james/ped-git/scripts/ped: from ped_core import editor_common\r\n"

def test_scripts ( request ):
    """ test suite to make sure that the scripts in the scripts folder actually work """
    # note that hex_output is special it needs to be output from the actual pexpect.read() of a spawned process
    # the lines end in /r/n because it is a terminal remember this when hex_dump.txt needs to be udpated
    python_path = os.path.dirname(os.path.dirname(request.fspath))
    exec_path = os.path.join(python_path,"scripts")
    os.environ["PYTHONPATH"] = python_path

    hex_output = open(os.path.join(os.path.dirname(request.fspath),"hex_dump.txt"),"r",encoding="utf-8",newline='').read()
    child = pexpect.spawnu(os.path.join(exec_path,'hex')+' '+os.path.join(exec_path,'hex'),env=os.environ)
    cmd_output = child.read()
    assert(cmd_output == hex_output)
    assert(child.isalive() == False)

    child = pexpect.spawnu(os.path.join(exec_path,'pyfind')+' -p "import\s*editor" '+os.path.join(exec_path,'ped'),env=os.environ)
    cmd_output = child.read()
    assert(cmd_output == pyfind_output)
    assert(child.isalive() == False)

    child = pexpect.spawnu(os.path.join(exec_path,'ped'),env=os.environ)
    assert(child.isalive() == True)
    test_file = "test_scripts_test.txt"
    macro = [keytab.KEYTAB_TAB]+list(test_file)+[keytab.KEYTAB_TAB,keytab.KEYTAB_CR]+list("This is test text")+[keytab.KEYTAB_ALTX]
    for key in macro:
        child.send(key)
    child.read()
    assert(child.isalive() == False)
    assert(os.path.exists(test_file))
    assert(open(test_file,"r").read() == "This is test text\n")
    os.remove(test_file)

    child = pexpect.spawnu(os.path.join(exec_path,'pless')+' '+os.path.join(exec_path,'pless'),env=os.environ)
    assert(child.isalive() == True)
    child.send(keytab.KEYTAB_ESC)
    child.read()
    assert(child.isalive() == False)
