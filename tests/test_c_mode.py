import editor_manager
import editor_common
import curses
import curses.ascii
import keytab
from ped_test_util import read_str,validate_screen,editor_test_suite,play_macro,screen_size,match_attr

def test_c_mode(testdir,capsys):
    with capsys.disabled():
        def main(stdscr):
            lines_to_test = [
                '#include <stdio.h>',
                'int main() {',
                '  // printf() displays the string inside quotation',
                '  printf("Hello, World!");',
                '  return 0;',
                '}'
                ]
            args = { "c_test":"\n".join(lines_to_test)}
            testfile = testdir.makefile(".c", **args)

            green = curses.color_pair(1)
            red = curses.color_pair(2)
            cyan = curses.color_pair(3)
            white = curses.color_pair(4)

            ed = editor_common.Editor(stdscr,None,str(testfile))
            ed.setWin(stdscr.subwin(ed.max_y,ed.max_x,0,0))
            ed.main(False)
            ed.main(False)
            validate_screen(ed)
            assert(ed.mode and ed.mode.name() == "C")
            match_list = [(0,0,18,red),(2,2,48,red),(3,2,6,white),(3,9,15,green),(4,9,1,green),(1,0,3,cyan),(4,2,6,cyan)]
            for line,pos,width,attr in match_list:
                assert(match_attr(ed.scr,line+1,pos,1,width,attr))
            ed.goto(1,0)
            ed.endln()
            ed.main(False,10)
            assert(ed.getLine() == 2 and ed.getPos() == 2)
            ed.insert('if (foo == 12) {')
            ed.main(False)
            ed.main(False)
            assert(match_attr(ed.scr,3,2,1,2,cyan))
            assert(match_attr(ed.scr,3,6,1,3,white))
            assert(match_attr(ed.scr,3,13,1,2,green))
            ed.main(False,10)
            assert(ed.getLine() == 3 and ed.getPos() == 4)
            ed.insert('printf("foo %d",foo)')
            ed.main(False,10)
            assert(ed.getLine() == 4 and ed.getPos() == 4)
            ed.insert('}')
            ed.main(False,10)
            assert(ed.getLine() == 5 and ed.getPos() == 2)
            ed.main(False)
            ed.main(False)

            lines_to_test = [
                "// Your First C++ Program",
                "",
                "#include <iostream>",
                "",
                "int main() {",
                '  std::cout << "Hello World!";',
                "  return 0;",
                "}"
                ]
            args = { "cpp_test":"\n".join(lines_to_test)}
            testfile = testdir.makefile(".cpp", **args)

            ed = editor_common.Editor(stdscr,None,str(testfile))
            ed.setWin(stdscr.subwin(ed.max_y,ed.max_x,0,0))
            ed.main(False)
            ed.main(False)
            validate_screen(ed)
            assert(ed.mode and ed.mode.name() == "C++")
            match_list = [(0,0,25,red),(2,0,19,red),(5,2,12,white),(5,15,14,green),(6,9,1,green),(4,0,3,cyan),(6,2,6,cyan)]
            for line,pos,width,attr in match_list:
                assert(match_attr(ed.scr,line+1,pos,1,width,attr))


        curses.wrapper(main)
