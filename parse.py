#!/usr/bin/env python3
# -*- coding: utf-8 -*-
###############################################################################
# Name: parser.py
# Purpose: Liberty parser definition using PEG
# Author: Rob Taylor <rob@shape.build>
# Copyright: (c) 2020 Shape.Build Ltd
# License: MIT License
###############################################################################


from arpeggio import PTNodeVisitor
from arpeggio.peg import ParserPEG


class LibertyNodeVisitor(PTNodeVisitor):
    pass


def main(debug=False):
    peg_grammar = open('liberty.peg').read()
    parser = ParserPEG(peg_grammar, 'liberty', 'comment')
    test = open('tests/sky130_fd_sc_hvl__ff_085C_5v50_lv1v95.lib').read()
    tree = parser.parse(test)
    print(tree.tree_str())


if __name__ == '__main__':
    main(debug=True)
