#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from .._maze import Maze

def test_maze():
    '''
    Simple test of Maze functionality.
    '''
    maze = Maze(63, 63)
    assert maze.width == 63
    assert maze.height == 63
    assert maze.CreateMazePerfect()
    assert maze.Resize(31, 61)
    assert maze.width == 31
    assert maze.height == 61
    assert maze.CreateMazePerfect()
    #maze.SaveBitmap("test.bmp")
    #maze.SaveText("test.txt")