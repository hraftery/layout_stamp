#!/usr/bin/env python3

# Icon from flaticon.com: <a href="https://www.flaticon.com/free-icons/clone-stamp" title="clone stamp icons">Clone stamp icons created by Freepik - Flaticon</a>

from kipy import KiCad
from kipy.geometry import Vector2
from kipy.board import BoardLayer, BoardLayerClass
from kipy.board_types import BoardText, FootprintInstance, Field

import sys
import os
import tempfile
import pickle
import shutil
#import kipy.proto.common.types.base_types_pb2
#import json

def copy_selected_footprint_properties():
    selection = board.get_selection()
    if len(selection) != 1:
        print("Select a single footprint first.")
        sys.exit()

    # TODO: Very hard to serialise a dict of KiCad properties.
    #       Instead, serialise the whole selection and extract properties later.
    #return board.get_selection_as_string()
    return selection[0]._proto.SerializeToString()

    s = selection[0]
    props = {}
    props['position'] = s.position._proto.SerializeToString()
    props['orientation'] = s.orientation._proto.SerializeToString()
    # We're assuming we only want to copy the footprint instance properties, so ignore
    # free text objects, which are a property of the footprint in the library.
    props['fields'] = [f._proto.SerializeToString() for f in s.texts_and_fields if isinstance(f, Field)]

    return props

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

def paste_footprint_properties(props):
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
                f_dst.text.layer = f_src.text.layer
                f_dst.text.position = f_src.text.position + offset
                break
    board.push_commit(commit, 'stamp layout') # NOTE: I don't know where the name appears

    board.update_items(s)


if __name__=='__main__':
    kicad = KiCad()
    board = kicad.get_board()

    # tmp_dir = tempfile.mkdtemp()
    # with tempfile.TemporaryDirectory(dir='copy-layout') as tmp_dir:
    #     tmp_path = os.path.join(tmp_dir, 'clipboard')
        #tmp_path = tmp_dir + 'clipboard'
    #shutil.copy(tmp_dir.name, 'bar.txt')

    tmp_dir = kicad.get_plugin_settings_path('copy-layout')
    os.makedirs(tmp_dir, exist_ok=True)
    tmp_path = os.path.join(tmp_dir, 'clipboard')
    #tmp_path.mkdir(parents=True, exist_ok=True)


    if len(sys.argv) >= 2 and sys.argv[1] == 'copy':
        with open(tmp_path, 'wb') as f:
            props = copy_selected_footprint_properties()
#            pickle.dump(props, f)
#            json.dump(props, f)
            f.write(props)
    elif len(sys.argv) >= 2 and sys.argv[1] == 'paste':
        with open(tmp_path, 'rb') as f:
#            props = pickle.load(f)
#            props = json.load(f)
            props = get_properties_from_serialised_footprint(f.read())
            paste_footprint_properties(props)
    else:
        print("Must pass 'copy' or 'paste' as argument.")
