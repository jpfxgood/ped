# Copyright 2009 James P Goodwin ped tiny python editor
""" clipboard module shared by editor and dialogs """

# types of clipboard contents, set of lines, span of characters, rectangular set of partial lines, or nothing
LINE_CLIP = 1
SPAN_CLIP = 2
RECT_CLIP = 3
NONE_CLIP = 0

# clipboard list adn type shared across editor instances
clip = []
clip_type = NONE_CLIP
