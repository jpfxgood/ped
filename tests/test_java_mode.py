from ped_core import editor_manager
from ped_core import editor_common
import curses
import curses.ascii
from ped_core import keytab
from ped_test_util import read_str,validate_screen,editor_test_suite,play_macro,screen_size,match_attr,wait_for_screen

def test_java_mode(testdir,capsys):
    with capsys.disabled():
        def main(stdscr):
            lines_to_test = [
                '// This is a simple Java program.',
                '//   FileName : "HelloWorld.java"',
                'class HelloWorld',
                '{',
                '    // Your program begins with a call to main()',
                '    // Prints "Hello, World" to the terminal window',
                '    public static void main(String args[])',
                '    {',
                '        System.out.println("Hello, World");',
                '    }',
                '}'
                ]
            args = { "java_test":"\n".join(lines_to_test)}
            testfile = testdir.makefile(".java", **args)

            green = curses.color_pair(1)
            red = curses.color_pair(2)
            cyan = curses.color_pair(3)
            white = curses.color_pair(4)

            ed = editor_common.Editor(stdscr,None,str(testfile))
            ed.setWin(stdscr.subwin(ed.max_y,ed.max_x,0,0))
            validate_screen(ed)
            assert(ed.mode and ed.mode.name() == "java_mode")
            match_list = [(0,0,32,red),(2,0,5,cyan),(4,4,44,red),(8,27,14,green)]
            for line,pos,width,attr in match_list:
                assert(match_attr(ed.scr,line+1,pos,1,width,attr))
            ed.goto(7,5)
            ed.endln()
            ed.main(False,10)
            assert(ed.getLine() == 8 and ed.getPos() == 4)
            ed.insert('if (20 > 18) {')
            ed.main(False,10)
            ed.insert('System.out.println("20 greater than 18");')
            ed.main(False,10)
            ed.insert('}')
            ed.main(False,10)
            wait_for_screen(ed)
            assert(match_attr(ed.scr,9,4,1,2,cyan))
            assert(match_attr(ed.scr,10,27,1,20,green))
            assert(ed.getLine() == 11 and ed.getPos() == 4)

        curses.wrapper(main)
