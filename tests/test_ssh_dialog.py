import curses
import curses.ascii
import keytab
from ped_test_util import read_str,validate_dialog,editor_test_suite,play_macro,screen_size,match_attr
from ssh_dialog import SSHFileDialog
from ssh_mod import ssh_put, ssh_del, ssh_stat
import dialog
import pytest
import os
import time

@pytest.fixture(scope="function")
def sftp_testdir(request,testdir):
    sftp_basepath = os.environ.get("SSH_DIALOG_BASEPATH",None)
    sftp_username = os.environ.get("SSH_DIALOG_USERNAME",None)
    sftp_password = os.environ.get("SSH_DIALOG_PASSWORD",None)
    assert sftp_basepath and sftp_username and sftp_password,"SSH_DIALOG environment not set"
    local_files = []
    remote_files = []
    local_file_names = []
    remote_file_names = []
    for i in range(0,5):
        args = { "local_%d"%(i):"\n".join(["local_%d test line %d"%(i,j) for j in range(0,200)])}
        local_files.append(testdir.makefile(".txt",**args))
        args = { "remote_%d"%(i):"\n".join(["local_%d test line %d"%(i,j) for j in range(0,200)])}
        remote_files.append(testdir.makefile(".txt",**args))
    for f in remote_files:
        ssh_put( str(f), sftp_basepath+str(f),lambda : { "ssh_username" : sftp_username, "ssh_password" : sftp_password}, False )
        remote_file_names.append(f.basename)
        f.remove()
    for f in local_files:
        local_file_names.append(f.basename)

    def cleanup_sftp_testdir():
        ssh_del( sftp_basepath+str(testdir.tmpdir.parts()[1]),True, lambda : { "ssh_username" : sftp_username, "ssh_password" : sftp_password })

    request.addfinalizer(cleanup_sftp_testdir)

    return {"ssh_username" : sftp_username,
            "ssh_password" : sftp_password,
            "ssh_basepath": sftp_basepath+str(testdir.tmpdir),
            "local_path": str(testdir.tmpdir),
            "local_files" : local_file_names,
            "remote_files" : remote_file_names,
            "testdir" : testdir }



def test_ssh_dialog(sftp_testdir,capsys):
    with capsys.disabled():
        def main(stdscr):
            screen_size( 30, 100 )

            d = SSHFileDialog(stdscr,   title = "SFTP File Manager",
                                        remote_path=sftp_testdir["ssh_basepath"],
                                        ssh_username=sftp_testdir["ssh_username"],
                                        ssh_password=sftp_testdir["ssh_password"],
                                        local_path=sftp_testdir["local_path"])
            d.main(False,True)
            validate_dialog(d)
            d.main(False,True,keytab.KEYTAB_TAB)
            d.main(False,True,keytab.KEYTAB_TAB)
            d.main(False,True,keytab.KEYTAB_TAB)
            assert(d.focus_list[d.current][1].name == "ssh_files")
            d.main(False,True,keytab.KEYTAB_DOWN)
            d.main(False,True,keytab.KEYTAB_DOWN)
            d.main(False,True,keytab.KEYTAB_DOWN)
            (ch,values) = d.main(False,True,keytab.KEYTAB_CR)
            selection,file_list = values["ssh_files"]
            assert(file_list[selection] == sftp_testdir["remote_files"][2] and values["ssh_file"] == sftp_testdir["remote_files"][2] and values["local_file"] == sftp_testdir["remote_files"][2])

            d.goto(d.get_button)
            (ch,values) = d.main(False,True,keytab.KEYTAB_SPACE)
            assert(os.path.exists(os.path.join(str(sftp_testdir["testdir"].tmpdir),sftp_testdir["remote_files"][2])))

            d.goto(d.file_list)
            assert(d.focus_list[d.current][1].name == "local_files")
            d.main(False,True,keytab.KEYTAB_DOWN)
            d.main(False,True,keytab.KEYTAB_DOWN)
            d.main(False,True,keytab.KEYTAB_DOWN)
            (ch,values) = d.main(False,True,keytab.KEYTAB_CR)
            selection,file_list = values["local_files"]
            assert(file_list[selection] == sftp_testdir["local_files"][2] and values["ssh_file"] == sftp_testdir["local_files"][2] and values["local_file"] == sftp_testdir["local_files"][2])

            d.goto(d.put_button)
            (ch,values) = d.main(False,True,keytab.KEYTAB_SPACE)
            assert(ssh_stat( values["ssh_dir"]+"/"+values["ssh_file"],lambda : { 'ssh_username':sftp_testdir['ssh_username'], 'ssh_password':sftp_testdir['ssh_password'] }) != (-1,-1))

            d.goto(d.open_button)
            (ch,values) = d.main(False,True,keytab.KEYTAB_SPACE)
            assert(ch == dialog.Component.CMP_KEY_OK)

            d.goto(d.cancel_button)
            (ch,values) = d.main(False,True,keytab.KEYTAB_SPACE)
            assert(ch == dialog.Component.CMP_KEY_CANCEL)

        curses.wrapper(main)
