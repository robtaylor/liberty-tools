#!/usr/bin/env python3
# -*- coding: utf-8 -*-
###############################################################################
# Name: parser.py
# Purpose: Liberty parser definition using PEG
# Author: Rob Taylor <rob@shape.build>
# Copyright: (c) 2020 Shape.Build Ltd
# License: MIT License
###############################################################################


from arpeggio import PTNodeVisitor, visit_parse_tree
from arpeggio.peg import ParserPEG


class LibertyNodeVisitor(PTNodeVisitor):
    def __init__(self, *args, **kwargs):
        super(LibertyNodeVisitor, self).__init__(*args, **kwargs)

    def visit_library(self, node, children):
        #print(f"\n\nlibrary: {children}")
        libraryname = children[0]
        elements = children[1:]
        return {"library": {"name": libraryname,
                            "elements": elements}}

    def visit_libraryname(self, node, children):
        return str(children[0])

    def visit_cell(self, node, children):
        return {"cell": {"name": children[0],
                         "elements": children[1]}}

    def visit_bus(self, node, children):
        return {"bus", children}

    def visit_simple_attribute(self, node, children):
        return {children[0]: children[1]}

    def visit_complex_attribute(self, node, children):
        #print(f"\n\ncomplex attribute:  {children}")
        values = []
        if len(children) > 1:
            values = children[1]
        return {children[0]: values}

    def visit_group(self, node, children):
        if len(children) < 3:
            return {"group": {"type": children[0],
                              "elements": children[1]}}
        else:
            return {"group": {"type": children[0],
                              "name": children[1],
                              "elements": children[2]}}

    def visit_valueset(self, node, children):
        # print(f"\n\nvalueset:  {children}")
        return children

    def visit_valuetypelist(self, node, children):
        #print(f"\n\nvaluetypelist: {children}")
        return children


def main(debug=False):
    peg_grammar = open('liberty.peg').read()
    parser = ParserPEG(peg_grammar, 'liberty', 'comment')
    test = open('tests/sky130_fd_sc_hvl__ff_085C_5v50_lv1v95.lib').read()
    tree = parser.parse(test)
    print(tree.tree_str())

    result = visit_parse_tree(tree, LibertyNodeVisitor(debug=debug))
    #print(result)


if __name__ == '__main__':
    main(debug=False)
