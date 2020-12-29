#!/usr/bin/env python3
# -*- coding: utf-8 -*-
###############################################################################
# Name: parser.py
# Purpose: Liberty parser definition using PEG
# Author: Rob Taylor <rob@shape.build>
# Copyright: (c) 2020 Shape.Build Ltd
# License: MIT License
###############################################################################


import concurrent.futures

from enum import Enum
from glob import glob

from arpeggio import PTNodeVisitor, visit_parse_tree
from arpeggio.peg import ParserPEG


class Node:
    pass


class Type(Enum):
    EXPR = "Expression"
    VIDENT = "VIdent"
    VIDENT_WITH_BUS = "VIdent_with_bus"
    STRING = "String"
    NUMBER = "Number"
    BOOL = "Bool"


class Value:
    type: str


class Library(Node):
    name: str
    elements: [Node]


class Cell(Node):
    name: str
    values: [Node]


class Group(Node):
    name: str
    parameters: [Node]
    attributes: [Node]


class Define(Node):
    attribute_name: str
    group_name: str
    attribute_type: str


class SimpleAttribute(Node):
    name: str
    value: Value


class LibertyNodeVisitor(PTNodeVisitor):
    def __init__(self, *args, **kwargs):
        super(LibertyNodeVisitor, self).__init__(*args, **kwargs)

    def visit_library(self, node, children):
        # print(f"\n\nlibrary: {children}")
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
        # print(f"\n\ncomplex attribute:  {children}")
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
        # print(f"\n\nvaluetypelist: {children}")
        return children


def main(debug=False, all=False):
    peg_grammar = open('liberty.peg').read()
    parser = ParserPEG(peg_grammar, 'liberty', 'comment')

    def parse_file(file):
        print(f"Parsing '{file}'")
        test = open(file).read()
        tree = parser.parse(test)
        # print(tree.tree_str())
        return visit_parse_tree(tree, LibertyNodeVisitor(debug=debug))

    if all:
        tests = glob('tests/*.lib')
        print(tests)
        with concurrent.futures.ThreadPoolExecutor() as executor:
            results = executor.map(parse_file,tests)
        return results
    else:
        return parse_file('tests/sky130_fd_sc_hvl__ff_085C_5v50_lv1v95.lib')


if __name__ == '__main__':
    main(debug=False, all=True)
