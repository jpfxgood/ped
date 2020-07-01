import editor_manager
import editor_common
import curses
import curses.ascii
import keytab
from ped_test_util import read_str,validate_screen,editor_test_suite,play_macro,screen_size,match_attr,wait_for_screen

def test_python_mode(testdir,capsys):
    with capsys.disabled():
        def main(stdscr):
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

            green = curses.color_pair(1)
            red = curses.color_pair(2)
            cyan = curses.color_pair(3)
            white = curses.color_pair(4)

            ed = editor_common.Editor(stdscr,None,str(testfile))
            ed.setWin(stdscr.subwin(ed.max_y,ed.max_x,0,0))
            validate_screen(ed)
            assert(ed.mode and ed.mode.name() == "python_mode")
            match_list = [(0,0,6,cyan),(4,0,19,red),(6,18,5,green),(11,19,31,red)]
            for line,pos,width,attr in match_list:
                assert(match_attr(ed.scr,line+1,pos,1,width,attr))
            ed.goto(6,0)
            ed.endln()
            ed.main(False,10)
            assert(ed.getLine() == 7 and ed.getPos() == 8)
            ed.insert('foo = "A double quoted string"')
            wait_for_screen(ed)
            assert(match_attr(ed.scr,8,8,1,3,white))
            assert(match_attr(ed.scr,8,14,1,24,green))


        curses.wrapper(main)
