#! /usr/bin/python

#  A sudoku solver
#  Larion Garaczi 2014
#
# TODO
#
# urgent: performance leak -> when backtracking every new Sudoku instance
# initializes regions which takes a lot of time (refactor self.table
# to be a dict? This would also help with memoization!)
#
# - raise exception on inputs that are too long
#
# - implement __getitem__() on Sudoku?
# - generate sudokus
# - generate extremely hard sudokus (measure the time it takes for this
# program to solve it or the amount of backtracking needed)
# - add --verbose switch to Sudoku
#
# - decent output :) (gui?)
# - memoize everything (refractor to be able to memoize functions that
# have mutable parameters)
#
# TESTS TODO
#
# - test for readfile
# - add specific tests for all solve functions
#

import itertools
import copy
import sys

from decorators import *

class SudokuError(Exception):
    pass

class SudokuInputError(SudokuError):
    pass

def p(string):
    print "DEBUG: {!s}".format(string)

def d():
    import pdb; pdb.set_trace()

class SudokuCollection(object):
    """ Class that can store a collection of sudoku puzzles."""
    def __init__(self, sudokufile):
        self.sudokus=[]
        for line in sudokufile:
            # description of a single sudoku puzzle
            description = line.strip() 
            if len(description) == 81:
                self.sudokus.append(Sudoku(instr=description))

    def solve_all(self, outfile=None, verbose=True):
        """ solves all sudokus in the collection, and (optionally) writes out 
        the solutions to the file specified """
        v = verbose
        total = len(self) #total number of sudokus in the collection
        if v: print "Solving {!s} sudokus.".format(total)
        for i, sudoku in enumerate(self):
            if v: print sudoku
            sudoku.solve()
            if v: print sudoku
            if v: print "{!s} out of {!s} sudokus solved.".format(i+1, total)
        if outfile:
            if v: print "Writing output to file."
            for sudoku in self:
                for row in sudoku.table:
                    for cell in row:
                        outfile.write(str(cell[0]))
                outfile.write("\n")
            if v: print "Done."
        return "Success"

    def __getitem__(self, no):
        return self.sudokus[no]
    
    def __len__(self):
        return len(self.sudokus)

class Sudoku(object):
    """ Class that represents Sudoku puzzles. The only public method is sudoku.solve(). 
    This combines simple elimination techniques (see Sudoku.solve1, Sudoku.solve2 andSudoku.solve3)
    with backtracking (which is only used when simple methods fail)."""

    def __init__(self, infile=None, instr=None, inlist=None, indict=None): 
        """ Read in puzzle from a file, a string or a list parameter.
        You should define only one kind of input, otherwise the result
        is undetermined

        >>> mysudoku = Sudoku(infile=myfile) # read data in from myfile
        >>> mysudoku = Sudoku(instr=("30000060000005018000060170000007")
        ("0506050030070401020000006802000098010000002000004")) # read string
        >>> mysudoku = Sudoku(inlist = mylist) # read list
        """ 

        try:
            if infile:
                self.read_file(infile)
            elif instr:
                self.read_str(instr)
            elif inlist:
                self.read_list(inlist)
            elif indict:
                self.read_dict(indict)
            else:
                raise SudokuError(("The Sudoku class constructor needs a parameter ")
                        ("to retrieve the puzzle"))
        except ValueError:
            raise SudokuInputError
        self.set_regions()
        self.initialize_peers()

    # high-level solving functions

    def solve(self):
        """ The main function of this class. Tries to solve the
        puzzle. It returns False if the puzzle is inconsistent
        and True otherwise.""" 
        # iterate solve1(), solve2() and solve3() until stuck.
        solvers = [self.solve1, self.solve2, self.solve3]
        if self.repeat_until_stuck(solvers): 
            return True
        else:
            # if the solvers don't solve the puzzle
            if self.is_consistent(): # and seems consistent
                return self.bt() # do some backtracking
            else:
                return False

    def bt(self):
        """ backtracking function if other techniques
        fail """
        table_copy = copy.deepcopy(self.table)
        mincell = min([ (len(cell), cell) 
            for cell in self.table.itervalues() if len(cell)>1], key=lambda x: x[0])[1]
        mincell_copy = mincell[:]
        del mincell[:]
        for cand in mincell_copy:
            mincell.append(cand)
            child = Sudoku(indict=table_copy)
            if child.solve():
                self.table = child.table
                return True
            del mincell[:]
        else:
            return False

    def solve1(self): #TODO: don't revisit cells
        """ For all regions check if there is only one cell left in
        it. If so, fill in the last cell accordingly. Do this until
        stuck. """
        for col in xrange(9):
            for row in xrange(9):
                cell = self.table[(col,row)] 
                if len(cell)==1:
                    value = cell[0]
                    # loop through all the cells where the same 
                    # value would result in a collision and try
                    # to delete value from the list of possible
                    # candidates:
                    for cell2 in self.peers(col,row):
                            try:
                                cell2.remove(value)
                            except ValueError:
                                pass

    def solve2(self):
        """For all regions and numbers not yet filled in, check if
        there is only one possible cell to insert the number into.
        If so, insert it. This only makes sense in conjunction with
        solve 1"""
        for region in self.regions:
            for no in xrange(1,10):
                possible = self.subregion(no, region)
                if len(possible) == 1: #found a cell where there is only one number possible
                    cell = possible[0]
                    if cell: #we don't want to "repair" inconsistent puzzles #TODO is this enough?
                        del cell[:]
                        cell.append(no)

    def solve3(self): #this makes solve1() redundant
        """ For all regions and numbers check the subregion (subr_1) where this
        candidate number is possible. If this subregion is also a subregion of
        another region (subr_2), then we can delete all the number candidate
        occurences from subr_2 - subr_1. To understand this on a concrete 
        example read this:

        https://www.sudokuoftheday.com/techniques/candidate-lines/ 
        """
        numbers = range(1,10)
        for region in self.regions:
        #loop through the subregions defined by the candidate numbers:
            for n in numbers:
                subregion = self.subregion_coords(n, region)
                for region2 in self.regions:
                    if not subregion <= region2: 
                        return
                    target = region2 - subregion
                    for coord in target:
                        try:
                            self.table[coord].remove(n)
                        except ValueError: pass

    #middle level helper methods

    def initialize_peers(self):
        """ Initialize a list of peers for each cell in self.peers, so that we
        don't have to generate this list every time. """
        self.peersdict={}
        for col in xrange(9):
            for row in xrange(9):
                self.peersdict[(col,row)] = [self.table[(col_peer, row_peer)]
                for region in self.regions 
                if (col,row) in region
                for (col_peer, row_peer) in region
                if (col_peer, row_peer) != (col, row)]

    def peers(self, coll, row):
        return self.peersdict[(coll, row)]

    def set_regions(self): 
        """ Initializes regions. """
        prod = itertools.product
        projections = [range(3), range(3, 6), range(6,9)]
        subsquares = [frozenset((row, col) for row, col in prod(x,y))
            for x, y in prod(projections, projections)]
        rows  = [frozenset((x,y) for y in range(9)) for x in range(9)]
        cols  = [frozenset((x,y) for x in range(9)) for y in range(9)]
        self.regions = subsquares + rows + cols
    
    def is_cell_in_region(self, cell, region): #TODO delete this
        """ checks whether a cell instance is in a region """
        return any(cell is cell2 for cell2 in region)

    def subregion(self, no, region): #TODO can't this be a genexpr?
        """ returns those cells of region, where no is a candidate """
        return [self.table[coord] for coord in region if no in self.table[coord]]

    def subregion_coords(self, no, region): #TODO document, can't we inline this? Also make test for this!
        """ returns those cells of region, where no is a candidate """
        return set(coord for coord in region if no in self.table[coord])

    def repeat_until_stuck(self, function): 
        """ Iterates a solving function until it gets stuck (i. e. self.table
        doesn't get changed anymore) or the puzzle is solved. If called with a
        list of function it iterates through all of them until stuck. """
        if not isinstance(function, list):
            tasks = [function]
        else:
            tasks = function
        table=[]
        while table != self.table:
            table = copy.deepcopy(self.table)
            for func in tasks:
                func()
                if self.is_solved():
                    return True
        return False

    def is_solved(self):
        """ return True if the puzzle is solved,
        False otherwise """
        return all(len(cand_lst)==1 for cand_lst in self.table.itervalues())
                                    
    def is_consistent(self):
        """ Detects collisions. Technically this function just returns False
        if there is a cell in self.table which is empty (no 
        candidates left) """
        return all(cand_lst for cand_lst in self.table.itervalues())

    # low-level internal processing methods

    def char_to_cand_list(self, char):
        """ convert a character to a list of candidates according
        to the following pattern:
        0 -> [1, 2, 3, 4, 5, 6, 7, 8, 9]
        1 -> [1], 2 -> [2], ...
        """
        every = range(1, 9+1)
        if char == "0": return every
        else: return [int(char)]
    
    def read_dict(self, indict):
        """ reads a dictionary and copies it to self.table """
        self.table = copy.deepcopy(indict) #TODO do we need deepcopy?
        self.check_table() # TODO move this to __init__

    def read_file(self, infile): 
        """ reads in input file to self.table"""
        puzzle_str = map(self.char_to_cand_list, infile.read(81))
        self.read_str(puzzle_str)

    def read_list(self, inlist): 
        """ reads in input list to self.table """
        self.table = dict()
        listcopy = copy.deepcopy(inlist)
        for i1, col in enumerate(listcopy):
            for i2, cell in enumerate(col):
                self.table[(i1,i2)]=cell
        self.check_table()

    def read_str(self, instr):
        """ reads in a string representation of a sudoku puzzle to self.table """
        if len(instr) < 81:
            raise SudokuInputError("Invalid input. Grid geometry corrupt. ")
        self.table = dict()
        for row in xrange(9):
            for col in xrange(9):
                self.table[(row,col)]=self.char_to_cand_list(instr[row*9+col])
        self.check_table()

    def check_table(self):
        """ Check self.table for possible corruptions. This is just a
        low-level internal check to filter out corrupt input. It doesn't
        detect inconsistencies (i. e. collisions within regions). """
        numbers = range(1, 10)
        # there should be 9 columns:
        if len(set([a for (a,b) in self.table.keys()])) != 9: 
            raise SudokuInputError("Invalid input. Grid geometry corrupt. ")
        #and 9 cells in every columns:
        #TODO de-obfuscate this?
        for col in xrange(9):
            rows = set(row for (x,row) in self.table.keys() if x == col)
            if not len(rows) == 9:
                raise SudokuInputError("Invalid input. Grid geometry corrupt.")
        #if not all(len(set([y for (x,y) in self.table.keys() if x == col])) == 9 for col in xrange(9)):
        #    raise SudokuInputError("Invalid input. Grid geometry corrupt.")

        #and no numbers besides 1,2,...,9:
        candidates = set(no for col in xrange(9) for row in xrange(9) for no in self.table[col,row])
        if not candidates.issubset(numbers):
            p(candidates)
            raise SudokuInputError("Invalid input. Grid geometry corrupt.") #TODO more informative message here

    def __str__(self):
        """ Pretty printer. This loses information, so that it can be easily 
        readable by humans: it only prints out unambiguous cells. """
        out = ""
        for col in range(9):
            for row in range(9):
                cell = self.table[(col,row)]
                if len(cell)==1:
                    out=out+str(cell[0]).center(3)
                else:
                    out=out+"_".center(3)
            out = out+"\n"
        return out
        
    def __repr__(self): #TODO atm we can't read this in!
        """ The output of this function is the format that the class
        can read in as well (serialization) - a list of possibilities
        for all cells of the 9*9 grid. This doesn't lose any 
        information. """
        return repr(self.table)

if __name__ == "__main__":
    with open(sys.argv[1]) as infile:
        sudoku = Sudoku(infile)
    print sudoku
    if sudoku.solve():
        print sudoku
    else:
        print "This puzzle is invalid."
