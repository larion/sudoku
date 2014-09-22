#! /usr/bin/python

from sudoku import Sudoku, SudokuCollection, SudokuError, SudokuInputError
import time

def test_sudoku_class(): #rebuild this function
    """ performs tests on the Sudoku class """
    
    # set up test puzzles:
    validpuzzle = (
    "005079003"
    "200000000"
    "348000000"
    "050680000"
    "070204080"
    "000013020"
    "000000471"
    "000000006"
    "800790300")

    puzzles_corrupt=[]
    puzzles_corrupt.append(
    "005079003" #one less line
    "200000000"
    "348000000" 
    "050680000"
    "070204080"
    "000000471"
    "000000006"
    "800790300")
    puzzles_corrupt.append(
    "00507900" #one line shorter
    "200000000"
    "348000000" 
    "050680000"
    "070204080"
    "000013020"
    "000000471"
    "000000006"
    "800790300")
    puzzles_corrupt.append(
    "00507900" #shorter lines
    "20000000"
    "34800000"
    "05068000"
    "07020400"
    "00001300"
    "00000041"
    "00000006"
    "80079030")
    puzzles_corrupt.append(
    "005079003"
    "200000000"
    "348000000"
    "050680000"
    "070204080"
    "00001A020" #notice the A
    "000000471"
    "000000006"
    "800790300")

    puzzles_inconsistent=[]
    puzzles_inconsistent.append(
    "905079003" #first row inconsistent
    "200000000"
    "348000000"
    "050680000"
    "070204080"
    "000013020"
    "000000471"
    "000000006"
    "800790300")
    puzzles_inconsistent.append(
    "105079003" #first col inconsistent
    "200000000"
    "348000000"
    "050680000"
    "070204080"
    "000013020"
    "000000471"
    "100000006"
    "800790300")
    puzzles_inconsistent.append(
    "005079003" #first box inconsistent
    "280000000"
    "348000000"
    "050680000"
    "070204080"
    "000013020"
    "000000471"
    "000000006"
    "800790300")
    puzzles_inconsistent.append(
    "005079003" #middle box inconsistent
    "200000000"
    "348000000"
    "050680000"
    "070264080"
    "000013020"
    "000000471"
    "000000006"
    "800790300")
    puzzles_inconsistent.append(
    "005079003" #last row inconsistent
    "200000000"
    "348000000"
    "050680000"
    "070204080"
    "000013020"
    "000000471"
    "000000006"
    "800790308")
    puzzles_inconsistent.append(
    "005079003" #last col inconsistent
    "200000000"
    "348000000"
    "050680000"
    "070204080"
    "000013026"
    "000000471"
    "000000006"
    "800790300")

    srtestpuzzle = ( #puzzle for the subregion test
    "665679663"
    "266666666"
    "348666666"
    "656686666"
    "676264686"
    "666613626"
    "666666471"
    "666666666"
    "866796366")

    for puzzle in puzzles_corrupt: #corrupt puzzles test
        try:
            Sudoku(instr=puzzle)
        except SudokuInputError: pass
        else: raise Exception("Bad input accepted")

    for incons in puzzles_inconsistent: #inconsistent puzzles test
        sudoku = Sudoku(instr=incons)
        sudoku.solve()
        assert not sudoku.is_consistent()

    sudoku = Sudoku(instr=validpuzzle) # OK, let's see a valid puzzle
    print sudoku
    sudoku.solve()
    print sudoku
    assert sudoku.is_consistent()
    print "human readable: \n{!s}".format(sudoku)
    print "repr: \n {!r}".format(sudoku)
    print "sudoku.regions: \n{}".format(sudoku.regions)

    sudoku = Sudoku(instr=validpuzzle) # is_no_in_region tests

    sudoku = Sudoku(instr=srtestpuzzle) # subregion tests
    assert sorted(sudoku.subregion(4, [(6,x) for x in range(9)])) == sorted([sudoku.table[(6,6)]])
    assert sorted(sudoku.subregion(7, [(6,x) for x in range(9)])) == sorted([sudoku.table[(6,7)]])
    assert sorted(sudoku.subregion(1, [(6,x) for x in range(9)])) == sorted([sudoku.table[(6,8)]])
    assert sorted(sudoku.subregion(2, [(6,x) for x in range(9)])) == []
    assert sorted(sudoku.subregion(3, [(6,x) for x in range(9)])) == []
    assert sorted(sudoku.subregion(5, [(6,x) for x in range(9)])) == []
    assert sorted(sudoku.subregion(8, [(6,x) for x in range(9)])) == []
    assert sorted(sudoku.subregion(9, [(6,x) for x in range(9)])) == []
    assert sudoku.subregion(1, [(x,y) for x in range(9) for y in range(9)]) == [sudoku.table[(5,4)], sudoku.table[(6,8)]]
    assert sudoku.subregion(2, [(x,y) for x in range(9) for y in range(9)]) == [sudoku.table[(1,0)], sudoku.table[(4,3)], sudoku.table[(5,7)]]

    print "OK. Let's see how fast we can solve some puzzle collections."
    benchmarklist = [ ("50 puzzles from Project Euler", "puzzles/euler_puzzles_50.txt", "puzzles/euler_solutions_50.txt"),
            ("95 hard puzzles", "puzzles/hard_puzzles_95.txt", "puzzles/hard_solutions_95.txt") ]
    for collection_name, path_puzzle, path_solution in benchmarklist:
        print collection_name
        with open(path_puzzle) as puzzles, open("puzzles/euler_solutions_50.txt","w") as solutions:
            before = time.clock()
            collection = SudokuCollection(puzzles)
            collection.solve_all(solutions, verbose=True)
            puzzleno = len(collection.sudokus) #number of sudokus, TODO: implement API
            after = time.clock()
            elapsed = after-before
            average = elapsed/50.0
            print "Solving {!s} puzzles took {!s} secs, avg: {!s} sec".format(puzzleno, elapsed, average) #TODO check results
    print "Tests succesful!"
    return True

if __name__=="__main__":
    test_sudoku_class()
