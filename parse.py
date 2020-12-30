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
from dataclasses import dataclass

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


@dataclass
class Value:
    type: str


@dataclass
class Library(Node):
    name: str
    elements: [Node]


@dataclass
class Group(Node):
    name: str
    parameters: [Node]
    attributes: [Node]


@dataclass
class SimpleAttribute(Node):
    name: str
    value: Value


@dataclass
class ComplexAttribute(Node):
    name: str
    values: [Value]


class LibertyNodeVisitor(PTNodeVisitor):
    def __init__(self, *args, **kwargs):
        super(LibertyNodeVisitor, self).__init__(*args, **kwargs)

    def visit_library(self, node, children):
        # print(f"\n\nlibrary: {children}")
        libraryname = children[0]
        elements = children[1:]
        return Library(libraryname, elements)

    def visit_libraryname(self, node, children):
        return str(children[0])

    def visit_simple_attribute(self, node, children):
        return SimpleAttribute(children[0], children[1])

    def visit_complex_attribute(self, node, children):
        values = []
        if len(children) > 1:
            values = children[1]
        return ComplexAttribute(children[0], values)

    def visit_group(self, node, children):
        if len(children) < 3:
            return Group(children[0], [], children[1])
        else:
            return Group(children[0], children[1],  children[2])

    def visit_valueset(self, node, children):
        return children

    def visit_valuetypelist(self, node, children):
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
        with concurrent.futures.ThreadPoolExecutor() as executor:
            results = executor.map(parse_file, tests)
            print(results)
        return results
    else:
        result = parse_file('tests/sky130_fd_sc_hvl__ff_085C_5v50_lv1v95.lib')
        print(result)


if __name__ == '__main__':
    main(debug=False, all=False)
