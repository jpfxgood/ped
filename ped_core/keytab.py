# Copyright 2009-2012 James P Goodwin ped tiny python editor
""" module that contains the symbolic names of the keys """
import curses

KEYTAB_NOKEY=chr(0)
KEYTAB_ALTA=chr(27)+'a'
KEYTAB_ALTB=chr(27)+'b'
KEYTAB_ALTC=chr(27)+'c'
KEYTAB_ALTD=chr(27)+'d'
KEYTAB_ALTE=chr(27)+'e'
KEYTAB_ALTF=chr(27)+'f'
KEYTAB_ALTG=chr(27)+'g'
KEYTAB_ALTH=chr(27)+'h'
KEYTAB_ALTI=chr(27)+'i'
KEYTAB_ALTJ=chr(27)+'j'
KEYTAB_ALTK=chr(27)+'k'
KEYTAB_ALTL=chr(27)+'l'
KEYTAB_ALTM=chr(27)+'m'
KEYTAB_ALTN=chr(27)+'n'
KEYTAB_ALTo=chr(27)+'o'
KEYTAB_ALTO=chr(27)+'O'
KEYTAB_ALTP=chr(27)+'p'
KEYTAB_ALTQ=chr(27)+'q'
KEYTAB_ALTR=chr(27)+'r'
KEYTAB_ALTS=chr(27)+'s'
KEYTAB_ALTT=chr(27)+'t'
KEYTAB_ALTU=chr(27)+'u'
KEYTAB_ALTV=chr(27)+'v'
KEYTAB_ALTW=chr(27)+'w'
KEYTAB_ALTX=chr(27)+'x'
KEYTAB_ALTY=chr(27)+'y'
KEYTAB_ALTZ=chr(27)+'z'
KEYTAB_BACKSPACE="backspace"
KEYTAB_BACKSPACE=chr(8)
KEYTAB_BACKTAB=chr(27)+'[Z'
KEYTAB_BTAB="btab"
KEYTAB_CR=chr(10)
KEYTAB_CTRLA=chr(1)
KEYTAB_CTRLB=chr(2)
KEYTAB_CTRLC=chr(3)
KEYTAB_CTRLD=chr(4)
KEYTAB_CTRLE=chr(5)
KEYTAB_CTRLF=chr(6)
KEYTAB_CTRLG=chr(7)
KEYTAB_CTRLH=chr(8)
KEYTAB_CTRLI=chr(9)
KEYTAB_CTRLJ=chr(10)
KEYTAB_CTRLK=chr(11)
KEYTAB_CTRLL=chr(12)
KEYTAB_CTRLM=chr(13)
KEYTAB_CTRLN=chr(14)
KEYTAB_CTRLO=chr(15)
KEYTAB_CTRLP=chr(16)
KEYTAB_CTRLQ=chr(17)
KEYTAB_CTRLR=chr(18)
KEYTAB_CTRLS=chr(19)
KEYTAB_CTRLT=chr(20)
KEYTAB_CTRLU=chr(21)
KEYTAB_CTRLV=chr(22)
KEYTAB_CTRLW=chr(23)
KEYTAB_CTRLX=chr(24)
KEYTAB_CTRLY=chr(25)
KEYTAB_CTRLZ=chr(26)
KEYTAB_CTRLLEFT='ctrl-left'
KEYTAB_CTRLRIGHT='ctrl-right'
KEYTAB_CTRLHOME='ctrl-home'
KEYTAB_CTRLEND='ctrl-end'
KEYTAB_DELC="delc"
KEYTAB_DLGCANCEL="cancel"
KEYTAB_DLGNOP=KEYTAB_NOKEY
KEYTAB_DLGOK="ok"
KEYTAB_DOWN="down"
KEYTAB_END="end"
KEYTAB_ESC=chr(27)
KEYTAB_F00="fk00"
KEYTAB_F01="fk01"
KEYTAB_F02="fk02"
KEYTAB_F03="fk03"
KEYTAB_F04="fk04"
KEYTAB_F05="fk05"
KEYTAB_F06="fk06"
KEYTAB_F07="fk07"
KEYTAB_F08="fk08"
KEYTAB_F09="fk09"
KEYTAB_F10="fk10"
KEYTAB_F11="fk11"
KEYTAB_F12="fk12"
KEYTAB_F13="fk13"
KEYTAB_F14="fk14"
KEYTAB_F15="fk15"
KEYTAB_F16="fk16"
KEYTAB_F17="fk17"
KEYTAB_F18="fk18"
KEYTAB_F19="fk19"
KEYTAB_F20="fk20"
KEYTAB_F21="fk21"
KEYTAB_F22="fk22"
KEYTAB_F23="fk23"
KEYTAB_F24="fk24"
KEYTAB_F25="fk25"
KEYTAB_F26="fk26"
KEYTAB_F27="fk27"
KEYTAB_F28="fk28"
KEYTAB_F29="fk29"
KEYTAB_F30="fk30"
KEYTAB_F31="fk31"
KEYTAB_F32="fk32"
KEYTAB_F33="fk33"
KEYTAB_F34="fk34"
KEYTAB_F35="fk35"
KEYTAB_F36="fk36"
KEYTAB_F37="fk37"
KEYTAB_F38="fk38"
KEYTAB_F39="fk39"
KEYTAB_F40="fk40"
KEYTAB_F41="fk41"
KEYTAB_F42="fk42"
KEYTAB_F43="fk43"
KEYTAB_F44="fk44"
KEYTAB_F45="fk45"
KEYTAB_F46="fk46"
KEYTAB_F47="fk47"
KEYTAB_F48="fk48"
KEYTAB_F49="fk49"
KEYTAB_F50="fk50"
KEYTAB_F51="fk51"
KEYTAB_F52="fk52"
KEYTAB_F53="fk53"
KEYTAB_F54="fk54"
KEYTAB_F55="fk55"
KEYTAB_F56="fk56"
KEYTAB_F57="fk57"
KEYTAB_F58="fk58"
KEYTAB_F59="fk59"
KEYTAB_F60="fk60"
KEYTAB_F61="fk61"
KEYTAB_F62="fk62"
KEYTAB_F63="fk63"
KEYTAB_HOME="home"
KEYTAB_INSERT="insert"
KEYTAB_KEYPADPLUS=chr(27)+'Ok'
KEYTAB_KEYTPADMINUS=chr(27)+'Om'
KEYTAB_LEFT="left"
KEYTAB_PAGEDOWN="pagedown"
KEYTAB_PAGEUP="pageup"
KEYTAB_REFRESH="refresh"
KEYTAB_RESIZE="resize"
KEYTAB_RIGHT="right"
KEYTAB_SPACE=' '
KEYTAB_TAB=chr(9)
KEYTAB_UP="up"
KEYTAB_MOUSE="mouse"


name_to_key = {
"KEYTAB_ALTA" : KEYTAB_ALTA,
"KEYTAB_ALTB" : KEYTAB_ALTB,
"KEYTAB_ALTC" : KEYTAB_ALTC,
"KEYTAB_ALTD" : KEYTAB_ALTD,
"KEYTAB_ALTE" : KEYTAB_ALTE,
"KEYTAB_ALTF" : KEYTAB_ALTF,
"KEYTAB_ALTG" : KEYTAB_ALTG,
"KEYTAB_ALTH" : KEYTAB_ALTH,
"KEYTAB_ALTI" : KEYTAB_ALTI,
"KEYTAB_ALTJ" : KEYTAB_ALTJ,
"KEYTAB_ALTK" : KEYTAB_ALTK,
"KEYTAB_ALTL" : KEYTAB_ALTL,
"KEYTAB_ALTM" : KEYTAB_ALTM,
"KEYTAB_ALTN" : KEYTAB_ALTN,
"KEYTAB_ALTo" : KEYTAB_ALTo,
"KEYTAB_ALTO" : KEYTAB_ALTO,
"KEYTAB_ALTP" : KEYTAB_ALTP,
"KEYTAB_ALTQ" : KEYTAB_ALTQ,
"KEYTAB_ALTR" : KEYTAB_ALTR,
"KEYTAB_ALTS" : KEYTAB_ALTS,
"KEYTAB_ALTT" : KEYTAB_ALTT,
"KEYTAB_ALTU" : KEYTAB_ALTU,
"KEYTAB_ALTV" : KEYTAB_ALTV,
"KEYTAB_ALTW" : KEYTAB_ALTW,
"KEYTAB_ALTX" : KEYTAB_ALTX,
"KEYTAB_ALTY" : KEYTAB_ALTY,
"KEYTAB_ALTZ" : KEYTAB_ALTZ,
"KEYTAB_BACKSPACE" : KEYTAB_BACKSPACE,
"KEYTAB_BACKSPACE" : KEYTAB_BACKSPACE,
"KEYTAB_BACKTAB" : KEYTAB_BACKTAB,
"KEYTAB_BTAB" : KEYTAB_BTAB,
"KEYTAB_CR" : KEYTAB_CR,
"KEYTAB_CTRLA" : KEYTAB_CTRLA,
"KEYTAB_CTRLB" : KEYTAB_CTRLB,
"KEYTAB_CTRLC" : KEYTAB_CTRLC,
"KEYTAB_CTRLD" : KEYTAB_CTRLD,
"KEYTAB_CTRLE" : KEYTAB_CTRLE,
"KEYTAB_CTRLF" : KEYTAB_CTRLF,
"KEYTAB_CTRLG" : KEYTAB_CTRLG,
"KEYTAB_CTRLH" : KEYTAB_CTRLH,
"KEYTAB_CTRLI" : KEYTAB_CTRLI,
"KEYTAB_CTRLJ" : KEYTAB_CTRLJ,
"KEYTAB_CTRLK" : KEYTAB_CTRLK,
"KEYTAB_CTRLL" : KEYTAB_CTRLL,
"KEYTAB_CTRLM" : KEYTAB_CTRLM,
"KEYTAB_CTRLN" : KEYTAB_CTRLN,
"KEYTAB_CTRLO" : KEYTAB_CTRLO,
"KEYTAB_CTRLP" : KEYTAB_CTRLP,
"KEYTAB_CTRLQ" : KEYTAB_CTRLQ,
"KEYTAB_CTRLR" : KEYTAB_CTRLR,
"KEYTAB_CTRLS" : KEYTAB_CTRLS,
"KEYTAB_CTRLT" : KEYTAB_CTRLT,
"KEYTAB_CTRLU" : KEYTAB_CTRLU,
"KEYTAB_CTRLV" : KEYTAB_CTRLV,
"KEYTAB_CTRLW" : KEYTAB_CTRLW,
"KEYTAB_CTRLX" : KEYTAB_CTRLX,
"KEYTAB_CTRLY" : KEYTAB_CTRLY,
"KEYTAB_CTRLZ" : KEYTAB_CTRLZ,
"KEYTAB_CTRLLEFT" : KEYTAB_CTRLLEFT,
"KEYTAB_CTRLRIGHT" : KEYTAB_CTRLRIGHT,
"KEYTAB_CTRLHOME" : KEYTAB_CTRLHOME,
"KEYTAB_CTRLEND" : KEYTAB_CTRLEND,
"KEYTAB_DELC" : KEYTAB_DELC,
"KEYTAB_DLGCANCEL" : KEYTAB_DLGCANCEL,
"KEYTAB_DLGNOP" : KEYTAB_DLGNOP,
"KEYTAB_DLGOK" : KEYTAB_DLGOK,
"KEYTAB_DOWN" : KEYTAB_DOWN,
"KEYTAB_END" : KEYTAB_END,
"KEYTAB_ESC" : KEYTAB_ESC,
"KEYTAB_F00" : KEYTAB_F00,
"KEYTAB_F01" : KEYTAB_F01,
"KEYTAB_F02" : KEYTAB_F02,
"KEYTAB_F03" : KEYTAB_F03,
"KEYTAB_F04" : KEYTAB_F04,
"KEYTAB_F05" : KEYTAB_F05,
"KEYTAB_F06" : KEYTAB_F06,
"KEYTAB_F07" : KEYTAB_F07,
"KEYTAB_F08" : KEYTAB_F08,
"KEYTAB_F09" : KEYTAB_F09,
"KEYTAB_F10" : KEYTAB_F10,
"KEYTAB_F11" : KEYTAB_F11,
"KEYTAB_F12" : KEYTAB_F12,
"KEYTAB_F13" : KEYTAB_F13,
"KEYTAB_F14" : KEYTAB_F14,
"KEYTAB_F15" : KEYTAB_F15,
"KEYTAB_F16" : KEYTAB_F16,
"KEYTAB_F17" : KEYTAB_F17,
"KEYTAB_F18" : KEYTAB_F18,
"KEYTAB_F19" : KEYTAB_F19,
"KEYTAB_F20" : KEYTAB_F20,
"KEYTAB_F21" : KEYTAB_F21,
"KEYTAB_F22" : KEYTAB_F22,
"KEYTAB_F23" : KEYTAB_F23,
"KEYTAB_F24" : KEYTAB_F24,
"KEYTAB_F25" : KEYTAB_F25,
"KEYTAB_F26" : KEYTAB_F26,
"KEYTAB_F27" : KEYTAB_F27,
"KEYTAB_F28" : KEYTAB_F28,
"KEYTAB_F29" : KEYTAB_F29,
"KEYTAB_F30" : KEYTAB_F30,
"KEYTAB_F31" : KEYTAB_F31,
"KEYTAB_F32" : KEYTAB_F32,
"KEYTAB_F33" : KEYTAB_F33,
"KEYTAB_F34" : KEYTAB_F34,
"KEYTAB_F35" : KEYTAB_F35,
"KEYTAB_F36" : KEYTAB_F36,
"KEYTAB_F37" : KEYTAB_F37,
"KEYTAB_F38" : KEYTAB_F38,
"KEYTAB_F39" : KEYTAB_F39,
"KEYTAB_F40" : KEYTAB_F40,
"KEYTAB_F41" : KEYTAB_F41,
"KEYTAB_F42" : KEYTAB_F42,
"KEYTAB_F43" : KEYTAB_F43,
"KEYTAB_F44" : KEYTAB_F44,
"KEYTAB_F45" : KEYTAB_F45,
"KEYTAB_F46" : KEYTAB_F46,
"KEYTAB_F47" : KEYTAB_F47,
"KEYTAB_F48" : KEYTAB_F48,
"KEYTAB_F49" : KEYTAB_F49,
"KEYTAB_F50" : KEYTAB_F50,
"KEYTAB_F51" : KEYTAB_F51,
"KEYTAB_F52" : KEYTAB_F52,
"KEYTAB_F53" : KEYTAB_F53,
"KEYTAB_F54" : KEYTAB_F54,
"KEYTAB_F55" : KEYTAB_F55,
"KEYTAB_F56" : KEYTAB_F56,
"KEYTAB_F57" : KEYTAB_F57,
"KEYTAB_F58" : KEYTAB_F58,
"KEYTAB_F59" : KEYTAB_F59,
"KEYTAB_F60" : KEYTAB_F60,
"KEYTAB_F61" : KEYTAB_F61,
"KEYTAB_F62" : KEYTAB_F62,
"KEYTAB_F63" : KEYTAB_F63,
"KEYTAB_HOME" : KEYTAB_HOME,
"KEYTAB_INSERT" : KEYTAB_INSERT,
"KEYTAB_KEYPADPLUS" : KEYTAB_KEYPADPLUS,
"KEYTAB_KEYTPADMINUS" : KEYTAB_KEYTPADMINUS,
"KEYTAB_LEFT" : KEYTAB_LEFT,
"KEYTAB_NOKEY" : KEYTAB_NOKEY,
"KEYTAB_PAGEDOWN" : KEYTAB_PAGEDOWN,
"KEYTAB_PAGEUP" : KEYTAB_PAGEUP,
"KEYTAB_REFRESH" : KEYTAB_REFRESH,
"KEYTAB_RESIZE" : KEYTAB_RESIZE,
"KEYTAB_RIGHT" : KEYTAB_RIGHT,
"KEYTAB_SPACE" : KEYTAB_SPACE,
"KEYTAB_TAB" : KEYTAB_TAB,
"KEYTAB_UP" : KEYTAB_UP,
"KEYTAB_MOUSE" : KEYTAB_MOUSE,
}

key_to_name = {}
for name,key in list(name_to_key.items()):
    key_to_name[key] = name

keydef = [
((0,),KEYTAB_NOKEY),
((27,-1,),KEYTAB_ESC),
((27,ord('a'),-1),KEYTAB_ALTA),
((27,ord('b'),-1),KEYTAB_ALTB),
((27,ord('c'),-1),KEYTAB_ALTC),
((27,ord('d'),-1),KEYTAB_ALTD),
((27,ord('e'),-1),KEYTAB_ALTE),
((27,ord('f'),-1),KEYTAB_ALTF),
((27,ord('g'),-1),KEYTAB_ALTG),
((27,ord('h'),-1),KEYTAB_ALTH),
((27,ord('i'),-1),KEYTAB_ALTI),
((27,ord('j'),-1),KEYTAB_ALTJ),
((27,ord('k'),-1),KEYTAB_ALTK),
((27,ord('l'),-1),KEYTAB_ALTL),
((27,ord('m'),-1),KEYTAB_ALTM),
((27,ord('n'),-1),KEYTAB_ALTN),
((27,ord('o'),-1),KEYTAB_ALTo),
((27,ord('p'),-1),KEYTAB_ALTP),
((27,ord('q'),-1),KEYTAB_ALTQ),
((27,ord('r'),-1),KEYTAB_ALTR),
((27,ord('s'),-1),KEYTAB_ALTS),
((27,ord('t'),-1),KEYTAB_ALTT),
((27,ord('u'),-1),KEYTAB_ALTU),
((27,ord('v'),-1),KEYTAB_ALTV),
((27,ord('w'),-1),KEYTAB_ALTW),
((27,ord('x'),-1),KEYTAB_ALTX),
((27,ord('y'),-1),KEYTAB_ALTY),
((27,ord('z'),-1),KEYTAB_ALTZ),
((27,ord('A'),-1),KEYTAB_ALTA),
((27,ord('B'),-1),KEYTAB_ALTB),
((27,ord('C'),-1),KEYTAB_ALTC),
((27,ord('D'),-1),KEYTAB_ALTD),
((27,ord('E'),-1),KEYTAB_ALTE),
((27,ord('F'),-1),KEYTAB_ALTF),
((27,ord('G'),-1),KEYTAB_ALTG),
((27,ord('H'),-1),KEYTAB_ALTH),
((27,ord('I'),-1),KEYTAB_ALTI),
((27,ord('J'),-1),KEYTAB_ALTJ),
((27,ord('K'),-1),KEYTAB_ALTK),
((27,ord('L'),-1),KEYTAB_ALTL),
((27,ord('M'),-1),KEYTAB_ALTM),
((27,ord('N'),-1),KEYTAB_ALTN),
((27,ord('O'),-1),KEYTAB_ALTO),
((27,ord('P'),-1),KEYTAB_ALTP),
((27,ord('Q'),-1),KEYTAB_ALTQ),
((27,ord('R'),-1),KEYTAB_ALTR),
((27,ord('S'),-1),KEYTAB_ALTS),
((27,ord('T'),-1),KEYTAB_ALTT),
((27,ord('U'),-1),KEYTAB_ALTU),
((27,ord('V'),-1),KEYTAB_ALTV),
((27,ord('W'),-1),KEYTAB_ALTW),
((27,ord('X'),-1),KEYTAB_ALTX),
((27,ord('Y'),-1),KEYTAB_ALTY),
((27,ord('Z'),-1),KEYTAB_ALTZ),
((curses.KEY_BACKSPACE,-1),KEYTAB_BACKSPACE),
((8,-1),KEYTAB_BACKSPACE),
((127,-1),KEYTAB_BACKSPACE),
((27,ord('['),ord('Z'),-1),KEYTAB_BACKTAB),
((curses.KEY_BTAB,-1),KEYTAB_BTAB),
((10,-1),KEYTAB_CR),
((1,-1),KEYTAB_CTRLA),
((2,-1),KEYTAB_CTRLB),
((3,-1),KEYTAB_CTRLC),
((4,-1),KEYTAB_CTRLD),
((5,-1),KEYTAB_CTRLE),
((6,-1),KEYTAB_CTRLF),
((7,-1),KEYTAB_CTRLG),
((8,-1),KEYTAB_CTRLH),
((9,-1),KEYTAB_CTRLI),
((10,-1),KEYTAB_CTRLJ),
((11,-1),KEYTAB_CTRLK),
((12,-1),KEYTAB_CTRLL),
((13,-1),KEYTAB_CTRLM),
((14,-1),KEYTAB_CTRLN),
((15,-1),KEYTAB_CTRLO),
((16,-1),KEYTAB_CTRLP),
((17,-1),KEYTAB_CTRLQ),
((18,-1),KEYTAB_CTRLR),
((19,-1),KEYTAB_CTRLS),
((20,-1),KEYTAB_CTRLT),
((21,-1),KEYTAB_CTRLU),
((22,-1),KEYTAB_CTRLV),
((23,-1),KEYTAB_CTRLW),
((24,-1),KEYTAB_CTRLX),
((25,-1),KEYTAB_CTRLY),
((26,-1),KEYTAB_CTRLZ),
((545,-1),KEYTAB_CTRLLEFT),
((560,-1),KEYTAB_CTRLRIGHT),
((530,-1),KEYTAB_CTRLHOME),
((525,-1),KEYTAB_CTRLEND),
((curses.KEY_DC,-1),KEYTAB_DELC),
((curses.KEY_DOWN,-1),KEYTAB_DOWN),
((curses.KEY_END,-1),KEYTAB_END),
((curses.KEY_F0,-1),KEYTAB_F00),
((curses.KEY_F1,-1),KEYTAB_F01),
((curses.KEY_F2,-1),KEYTAB_F02),
((curses.KEY_F3,-1),KEYTAB_F03),
((curses.KEY_F4,-1),KEYTAB_F04),
((curses.KEY_F5,-1),KEYTAB_F05),
((curses.KEY_F6,-1),KEYTAB_F06),
((curses.KEY_F7,-1),KEYTAB_F07),
((curses.KEY_F8,-1),KEYTAB_F08),
((curses.KEY_F9,-1),KEYTAB_F09),
((curses.KEY_F10,-1),KEYTAB_F10),
((curses.KEY_F11,-1),KEYTAB_F11),
((curses.KEY_F12,-1),KEYTAB_F12),
((curses.KEY_F13,-1),KEYTAB_F13),
((curses.KEY_F14,-1),KEYTAB_F14),
((curses.KEY_F15,-1),KEYTAB_F15),
((curses.KEY_F16,-1),KEYTAB_F16),
((curses.KEY_F17,-1),KEYTAB_F17),
((curses.KEY_F18,-1),KEYTAB_F18),
((curses.KEY_F19,-1),KEYTAB_F19),
((curses.KEY_F20,-1),KEYTAB_F20),
((curses.KEY_F21,-1),KEYTAB_F21),
((curses.KEY_F22,-1),KEYTAB_F22),
((curses.KEY_F23,-1),KEYTAB_F23),
((curses.KEY_F24,-1),KEYTAB_F24),
((curses.KEY_F25,-1),KEYTAB_F25),
((curses.KEY_F26,-1),KEYTAB_F26),
((curses.KEY_F27,-1),KEYTAB_F27),
((curses.KEY_F28,-1),KEYTAB_F28),
((curses.KEY_F29,-1),KEYTAB_F29),
((curses.KEY_F30,-1),KEYTAB_F30),
((curses.KEY_F31,-1),KEYTAB_F31),
((curses.KEY_F32,-1),KEYTAB_F32),
((curses.KEY_F33,-1),KEYTAB_F33),
((curses.KEY_F34,-1),KEYTAB_F34),
((curses.KEY_F35,-1),KEYTAB_F35),
((curses.KEY_F36,-1),KEYTAB_F36),
((curses.KEY_F37,-1),KEYTAB_F37),
((curses.KEY_F38,-1),KEYTAB_F38),
((curses.KEY_F39,-1),KEYTAB_F39),
((curses.KEY_F40,-1),KEYTAB_F40),
((curses.KEY_F41,-1),KEYTAB_F41),
((curses.KEY_F42,-1),KEYTAB_F42),
((curses.KEY_F43,-1),KEYTAB_F43),
((curses.KEY_F44,-1),KEYTAB_F44),
((curses.KEY_F45,-1),KEYTAB_F45),
((curses.KEY_F46,-1),KEYTAB_F46),
((curses.KEY_F47,-1),KEYTAB_F47),
((curses.KEY_F48,-1),KEYTAB_F48),
((curses.KEY_F49,-1),KEYTAB_F49),
((curses.KEY_F50,-1),KEYTAB_F50),
((curses.KEY_F51,-1),KEYTAB_F51),
((curses.KEY_F52,-1),KEYTAB_F52),
((curses.KEY_F53,-1),KEYTAB_F53),
((curses.KEY_F54,-1),KEYTAB_F54),
((curses.KEY_F55,-1),KEYTAB_F55),
((curses.KEY_F56,-1),KEYTAB_F56),
((curses.KEY_F57,-1),KEYTAB_F57),
((curses.KEY_F58,-1),KEYTAB_F58),
((curses.KEY_F59,-1),KEYTAB_F59),
((curses.KEY_F60,-1),KEYTAB_F60),
((curses.KEY_F61,-1),KEYTAB_F61),
((curses.KEY_F62,-1),KEYTAB_F62),
((curses.KEY_F63,-1),KEYTAB_F63),
((curses.KEY_HOME,-1),KEYTAB_HOME),
((curses.KEY_IC,-1),KEYTAB_INSERT),
((27,ord('O'),ord('k'),-1),KEYTAB_KEYPADPLUS),
((27,ord('O'),ord('m'),-1),KEYTAB_KEYTPADMINUS),
((curses.KEY_LEFT,-1),KEYTAB_LEFT),
((curses.KEY_NPAGE,-1),KEYTAB_PAGEDOWN),
((curses.KEY_PPAGE,-1),KEYTAB_PAGEUP),
((curses.KEY_RESIZE,-1),KEYTAB_RESIZE),
((curses.KEY_RIGHT,-1),KEYTAB_RIGHT),
((ord(' '),-1),KEYTAB_SPACE),
((9,-1),KEYTAB_TAB),
((curses.KEY_UP,-1),KEYTAB_UP),
((curses.KEY_MOUSE,-1),KEYTAB_MOUSE),
]
