import curses
import curses.ascii
import keytab
from ped_test_util import read_str,validate_dialog,editor_test_suite,play_macro,screen_size,match_attr
from dialog import Frame,ListBox,Toggle,Button,StaticText,Prompt,Dialog,Component
from file_browse import FileBrowseComponent
from stream_select import StreamSelectComponent
import io

def test_dialog(testdir,capsys):
    with capsys.disabled():
        def main(stdscr):
            screen_size( 30, 100 )
            curses.resizeterm( 30, 100 )
            lines_to_test = [
                "import editor_manager",
                "import editor_common",
                "import sys",
                "",
                "# This is a comment",
                "def main( args ):",
                "    if args[0] == 'test':",
                "        print( 'This is a test' )",
                "    return args[1]",
                "",
                "if __name__ == '__main__':",
                "    main(sys.argv) # This line ends with a comment"
                ]
            args = { "python_test":"\n".join(lines_to_test)}
            testfile = testdir.makefile(".py", **args)

            d = Dialog(stdscr, "TestDialog", 30, 100, [
                    Frame("Test Dialog"),
                    ListBox("ListBox",1,50,2,7,20,"Select",5,[ "%d item in list"%f for f in range(1,10)]),
                    Toggle("Toggle",2,2,3,7,3,["%d option of 6"%f for f in range(1,7)]),
                    Button("Button",3,2,4,"OK",Component.CMP_KEY_OK),
                    StaticText("StaticText",2,5,"Text: ",20,"Just static text"),
                    Prompt("Prompt",6,2,6,"Prompt input: ",30),
                    FileBrowseComponent("FileBrowse",7,2,7,40,10,"Python Test",str(testfile)),
                    StreamSelectComponent("StreamSelect",8,2,17,40,10,"Stream Test",io.StringIO("\n".join(["%d stream line"%f for f in range(0,200)])))
                    ],0,0)

            (ch,values) = d.main(False,True)
            assert(values['ListBox'][0] == 5 and values['Toggle'][0] == 3 and values['Button']==False
                    and values['StaticText'] == 'Just static text' and values['Prompt'] == ''
                    and values['FileBrowse'] == 'import editor_manager' and values['StreamSelect'] == '0 stream line')
            validate_dialog(d)
            assert(d.focus_list[d.current][1].name == "ListBox")
            (ch,values) = d.main(False,True,keytab.KEYTAB_DOWN)
            assert(values['ListBox'][0] == 6)
            (ch,values) = d.main(False,True,keytab.KEYTAB_TAB)
            (ch,values) = d.main(False,True)
            validate_dialog(d)
            assert(d.focus_list[d.current][1].name == "Toggle")
            (ch,values) = d.main(False,True,keytab.KEYTAB_SPACE)
            assert(values['Toggle'][0] == 4)
            (ch,values) = d.main(False,True,keytab.KEYTAB_TAB)
            (ch,values) = d.main(False,True)
            validate_dialog(d)
            button = d.focus_list[d.current][1]
            (ch,values) = d.main(False,True,keytab.KEYTAB_TAB)
            (ch,values) = d.main(False,True)
            validate_dialog(d)
            assert(d.focus_list[d.current][1].name == "Prompt")
            for input_ch in list('I typed this'):
                (ch,values) = d.main(False,True,input_ch)
            assert(values['Prompt'] == 'I typed this')
            (ch,values) = d.main(False,True,keytab.KEYTAB_TAB)
            (ch,values) = d.main(False,True)
            validate_dialog(d)
            assert(d.focus_list[d.current][1].name == "FileBrowse")
            for r in range(0,7):
                (ch,values) = d.main(False,True,keytab.KEYTAB_DOWN)
            assert(values['FileBrowse'] == "        print( 'This is a test' )")
            (ch,values) = d.main(False,True,keytab.KEYTAB_TAB)
            (ch,values) = d.main(False,True)
            validate_dialog(d)
            assert(d.focus_list[d.current][1].name == "StreamSelect")
            for r in range(0,7):
                (ch,values) = d.main(False,True,keytab.KEYTAB_DOWN)
            assert(values['StreamSelect'] == "7 stream line")
            d.goto(button)
            (ch,values) = d.main(False,True)
            validate_dialog(d)
            assert(d.focus_list[d.current][1].name == "Button")
            (ch,values) = d.main(False,True,keytab.KEYTAB_SPACE)
            assert(ch == Component.CMP_KEY_OK)
            (ch,values) = d.main(False,True)
            validate_dialog(d)

        curses.wrapper(main)
