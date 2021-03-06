#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function
import os
import glob

# sudo pip install clang==3.8
import clang.cindex

# set path to libclang library
if not clang.cindex.Config.loaded:
    clang.cindex.Config.set_library_file('/opt/local/libexec/llvm-3.8/lib/libclang.dylib')

# create an index
index = clang.cindex.Index.create()

full_paths = glob.glob('../daedalus/src/*.cpp') + glob.glob('../daedalus/src/*.h')

#print(full_paths[2])
#tu = index.parse(full_paths[2])

def yield_children(node, pred):
    todo = [(None,node)]
    while todo:
        parent, node = todo.pop(0)
        if pred(node):
            yield parent, node
        todo.extend([(node,c) for c in node.get_children()])

# collect all the CreateMaze* methods in create.cpp
# there are 19 of these
def get_create_methods(tu):
    return [n for (p,n) in yield_children(
        tu.cursor,
        # predicate: kind is CXX_METHOD, name starts with "CreateMaze",
        # and node has a child with type COMPOUND_STMT
        lambda n: n.kind == clang.cindex.CursorKind.CXX_METHOD and
        n.spelling.startswith('CreateMaze') and
        any(c.kind == clang.cindex.CursorKind.COMPOUND_STMT for c in n.get_children()))]

print('Collecting CreateMaze* methods in create.cpp ...')
tu = index.parse('../daedalus/src/create.cpp')
create_methods = get_create_methods(tu)
print('Collecting CreateMaze* methods in labyrnth.cpp ...')
tu = index.parse('../daedalus/src/labyrnth.cpp')
create_methods.extend(get_create_methods(tu))

# collect all references to "ms" inside these methods
from collections import defaultdict
refs = defaultdict(set)
funcs = defaultdict(set)
for create_method in create_methods:
    # detect direct references to program state variables
    for parent, child in yield_children(
            create_method,
            lambda n: n.kind == clang.cindex.CursorKind.DECL_REF_EXPR and
            n.spelling in ['bm', 'ws', 'dr', 'ms']):
            #and any(c.kind == clang.cindex.CursorKind.MEMBER_REF_EXPR for c in n.get_children())):
        refs[create_method.spelling].add('{}.{}'.format(child.spelling, parent.spelling))
        #print create_method.spelling, child.spelling, parent.spelling, child.location
        #break
    # detect function calls
    for parent, child in yield_children(
            create_method,
            lambda n: n.kind == clang.cindex.CursorKind.CALL_EXPR):
        #print create_method.spelling, child.spelling, child.location
        funcs[create_method.spelling].add(child.spelling)
    #refs[method.spelling].append

# collect all relevent function names
#all_funcs = set.union(*funcs.values())

# now parse all the cpp files
for full_path in full_paths:
    print('Parsing', full_path, '...')
    tu = index.parse(full_path)
    # collect all function defs in the current TU
    for parent, child in yield_children(
            tu.cursor,
            lambda n: (n.kind == clang.cindex.CursorKind.CXX_METHOD or
                       n.kind == clang.cindex.CursorKind.FUNCTION_DECL) and
            #n.spelling in all_funcs and
            any(c.kind == clang.cindex.CursorKind.COMPOUND_STMT for c in n.get_children())):
        #print full_path, child.spelling, child.location
        # collect all references in the current function to program state variables
        for parent2, child2 in yield_children(
                child,
                lambda n: n.kind == clang.cindex.CursorKind.DECL_REF_EXPR and
                n.spelling in ['bm', 'ws', 'dr', 'ms']):
            refs[child.spelling].add('{}.{}'.format(child2.spelling, parent2.spelling))
        # collect all function calls from the current function
        for parent2, child2 in yield_children(
                child,
                lambda n: n.kind == clang.cindex.CursorKind.CALL_EXPR):
            #print create_method.spelling, child.spelling, child.location
            funcs[child.spelling].add(child2.spelling)

INTERESTING_SETTINGS = {'ms.fSection', 'ms.fTeleportEntrance', 'ms.fPoleNoDeadEnd',
                        'ms.fSolveEveryPixel', 'ms.fSolveDotExit', 'ms.fRandomPath',
                        'ms.fCountShortest', 'ms.nTweakPassage', 'ms.cMaze',
                        'ms.nWeaveOff', 'ms.nWeaveOn', 'ms.nWeaveRail', 'ms.nEntrancePos',
                        'ms.nLabyrinth', 'ms.lcs', 'ms.nClassical', 'ms.fClassicalCirc',
                        'ms.szCustom', 'ms.fCustomAuto', 'ms.nCustomFold', 'ms.nCustomAsym',
                        'ms.nCustomPartX', 'ms.nCustomPartY', 'ms.lcc', 'ms.zCustomMiddle',
                        'ms.fRiver', 'ms.fRiverEdge', 'ms.fRiverFlow', 'ms.omega',
                        'ms.omega2', 'ms.omegas', 'ms.omegaf', 'ms.nOmegaDraw',
                        'ms.szPlanair', 'ms.fTreeWall', 'ms.fTreeRandom', 'ms.nTreeRiver',
                        'ms.nForsInit', 'ms.nForsAdd', 'ms.cSpiral', 'ms.cSpiralWall',
                        'ms.cRandomAdd', 'ms.xFractal', 'ms.yFractal', 'ms.zFractal',
                        'ms.fFractalI', 'ms.fCrackOff', 'ms.nCrackLength', 'ms.nCrackPass',
                        'ms.nCrackSector', 'ms.nSparse', 'ms.fKruskalPic', 'ms.fWeaveCorner',
                        'ms.fTiltDiamond', 'ms.nTiltSize', 'ms.nRndBias', 'ms.nRndRun'}

GLOBAL_SETTINGS = {
    'ms.cRandomAdd': ('int', '0'),
    'ms.cSpiral': ('int', '15'),
    'ms.cSpiralWall': ('int', '15'),
    'ms.fKruskalPic': ('bool', 'False'),
    'ms.fRiver': ('bool', 'True'),
    'ms.fRiverEdge': ('bool', 'True'),
    'ms.fRiverFlow': ('bool', 'True'),
    'ms.fSection': ('bool', 'False'),
    'ms.fTiltDiamond': ('bool', 'False'),
    'ms.fTreeRandom': ('bool', 'True'),
    'ms.fTreeWall': ('bool', 'False'),
    'ms.nEntrancePos': ('int', 'ENTRANCE_RANDOM'),
    'ms.nForsAdd': ('int', '-100'),
    'ms.nForsInit': ('int', '1'),
    'ms.nRndBias': ('int', '0'),
    'ms.nRndRun': ('int', '0'),
    'ms.nTiltSize': ('int', '4'),
    'ms.nTreeRiver': ('int', '10'),
    'ms.zFractal': ('int', '3'),
}

# now, for each CreateMaze* function
total_closure = set()
for create_method in create_methods:
    method_name = create_method.spelling
    # find the transitive closure over all the functions it calls
    closure = set(refs[method_name])
    done = set()
    todo = list(funcs[method_name])
    while todo:
        func = todo.pop()
        if func in done:
            continue
        done.add(func)
        closure |= refs[func]
        todo.extend(list(funcs[func]))
    #refs[method_name] & BLAH
    #print(method_name, closure)
    closure = closure & INTERESTING_SETTINGS
    total_closure |= closure
    if closure:
        print()
        print('// declaration')
        print(method_name)
        for ref in sorted(closure):
            print('{} {},'.format(GLOBAL_SETTINGS[ref][0], ref.split('.')[-1]))
        print()
        print('// setting')
        print(method_name)
        for ref in sorted(closure):
            print('{} = {};'.format(ref, ref.split('.')[-1]))
        print()
        print('// python')
        print(method_name)
        for ref in sorted(closure):
            print('{}={},'.format(ref.split('.')[-1], GLOBAL_SETTINGS[ref][1]))
        print()
        for ref in sorted(closure):
            print('{},'.format(ref.split('.')[-1]))
        print()
        for ref in sorted(closure):
            print(':param {} {}: defaults to {}'.format(GLOBAL_SETTINGS[ref][0],
                                                        ref.split('.')[-1],
                                                        GLOBAL_SETTINGS[ref][1]))

# detect class member function definitions (not bare functions):
# node.kind == clang.cindex.CursorKind.CXX_METHOD
# all of these have kind.is_declaration() == True

# detect bare function definitions (not class member functions):
# node.kind == clang.cindex.CursorKind.FUNCTION_DECL

# detect function calls (including to class member functions):
# node.kind == clang.cindex.CursorKind.CALL_EXPR

# detect references like "ms.fRiver"
# node.kind == CursorKind.DECL_REF_EXPR and node.spelling == 'ms'
# children: child.kind == CursorKind.MEMBER_REF_EXPR



# print all nodes in create.cpp line 53:
# flag fClean = ms.fRiver && ms.fRiverEdge && ms.fRiverFlow;

# clang.cindex.CursorKind.VARIABLE_REF never shows up

# clang.cindex.CursorKind.CXX_METHOD
# ('found call expr:', 'PerfectGenerate', <SourceLocation file '../daedalus/src/create.cpp', line 48, column 12>)
