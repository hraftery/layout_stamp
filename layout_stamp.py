#!/usr/bin/env python3

# Icon from flaticon.com: <a href="https://www.flaticon.com/free-icons/clone-stamp" title="clone stamp icons">Clone stamp icons created by Freepik - Flaticon</a>

from kipy import KiCad
from kipy.geometry import Vector2
from kipy.board import BoardLayer, BoardLayerClass
from kipy.board_types import BoardText, FootprintInstance, Field

import sys
import os

def serialise_selected_footprint(board):
    selection = board.get_selection()
    if len(selection) != 1:
        print("Select a single footprint first.")
        sys.exit()

    # Turns out to be very hard to serialise a dict of KiCad properties.
    # Serialise the whole footprint instead, using the same protobufs format
    # used to get it through the API.
    return selection[0]._proto.SerializeToString()

def get_properties_from_serialised_footprint(ser):
    fpi = FootprintInstance()
    fpi._proto.ParseFromString(ser)
    
    props = {}
    props['position'] = fpi.position
    props['orientation'] = fpi.orientation
    # We're assuming we only want to copy the footprint instance properties, so ignore
    # free text objects, which are a property of the footprint in the library.
    props['fields'] = [f for f in fpi.texts_and_fields if isinstance(f, Field)]

    return props

def paste_footprint_properties(board, props):
    selection = board.get_selection()
    if len(selection) != 1:
        print("Select a single footprint first.")
        sys.exit()

    s = selection[0]

    offset = s.position - props['position']
    
    commit = board.begin_commit() # do all changes in one undo history step
    s.orientation = props['orientation']
    for f_src in props['fields']:
        for f_dst in [f for f in s.texts_and_fields if isinstance(f, Field)]:
            if f_src.name == f_dst.name: 
                f_dst.visible = f_src.visible
                f_dst.layer = f_src.layer
                f_dst.text.attributes = f_src.text.attributes # argh, where's knockout?
                f_dst.text.proto.knockout = f_src.text.proto.knockout # oh, dear, finally found it.
                f_dst.text.layer = f_src.text.layer
                f_dst.text.position = f_src.text.position + offset
                break
    board.push_commit(commit, 'stamp layout') # NOTE: I don't know where the name appears

    board.update_items(s)


def main(argv):
    kicad = KiCad()
    board = kicad.get_board()

    # Hot damn it's hard to persist something temporarily!
    # None of the tempfile stuff is predictable from invocation to invocation,
    # so ended up creating a file in the settings path instead.

    # KiCad currently requires an identifer that is NOT valid. Apparent bug here:
    # https://gitlab.com/kicad/code/kicad/-/blob/master/common/api/api_handler_common.cpp#L311
    # That means something that *doesn't* match /[\w\d]{2,}\.[\w\d]+\\.[\w\d]+/
    # https://gitlab.com/kicad/code/kicad/-/blob/master/common/api/api_plugin.cpp#L203
    # That is, something *without* 2 or more tokens, dot, 1 or more tokens, dot, 1 or more tokens,
    # where a "token" is an alphanumeric character or an underscore.
    tmp_dir = kicad.get_plugin_settings_path('ee,empirical,kipy,layout_stamp')
    os.makedirs(tmp_dir, exist_ok=True)
    tmp_path = os.path.join(tmp_dir, 'clipboard')

    if len(argv) >= 2 and argv[1] == 'copy':
        with open(tmp_path, 'wb') as f:
            selection = serialise_selected_footprint(board)
            f.write(selection)
    elif len(argv) >= 2 and argv[1] == 'paste':
        with open(tmp_path, 'rb') as f:
            props = get_properties_from_serialised_footprint(f.read())
            paste_footprint_properties(board, props)
    else:
        print("Must pass 'copy' or 'paste' as argument.")


if __name__=='__main__':
    main(sys.argv)
