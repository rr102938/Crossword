import sys
from crossword import *

class CrosswordCreator():

    def __init__(self, crossword):
        self.crossword = crossword
        self.domains = {
            var: self.crossword.words.copy()
            for var in self.crossword.variables
        }

    def letter_grid(self, assignment):
        letters = [[None for _ in range(self.crossword.width)] for _ in range(self.crossword.height)]
        for variable, word in assignment.items():
            direction = variable.direction
            for k in range(len(word)):
                i = variable.i + (k if direction == Variable.DOWN else 0)
                j = variable.j + (k if direction == Variable.ACROSS else 0)
                letters[i][j] = word[k]
        return letters

    def print(self, assignment):
        letters = self.letter_grid(assignment)
        # Using self.crossword.height and self.crossword.width
        for i in range(self.crossword.height):
            for j in range(self.crossword.width):
                if self.crossword.structure[i][j]:
                    print(letters[i][j] or " ", end="")
                else:
                    print("█", end="")
            print()

    def save(self, assignment, filename):
        from PIL import Image, ImageDraw, ImageFont
        cell_size = 100
        cell_border = 2
        interior_size = cell_size - 2 * cell_border
        letters = self.letter_grid(assignment)
        img = Image.new("RGBA", (self.crossword.width * cell_size, self.crossword.height * cell_size), "black")
        font = ImageFont.truetype("assets/fonts/OpenSans-Regular.ttf", 80)
        draw = ImageDraw.Draw(img)
        for i in range(self.crossword.height):
            for j in range(self.crossword.width):
                rect = [(j * cell_size + cell_border, i * cell_size + cell_border),
                        ((j + 1) * cell_size - cell_border, (i + 1) * cell_size - cell_border)]
                if self.crossword.structure[i][j]:
                    draw.rectangle(rect, fill="white")
                    if letters[i][j]:
                        draw.text((rect[0][0] + 10, rect[0][1] - 10), letters[i][j], fill="black", font=font)
        img.save(filename)

    def solve(self):
        self.enforce_node_consistency()
        self.ac3()
        return self.backtrack(dict())

    def enforce_node_consistency(self):
        for var in self.crossword.variables:
            for word in self.domains[var].copy():
                if len(word) != var.length:
                    self.domains[var].remove(word)

    def revise(self, x, y):
        revised = False
        overlap = self.crossword.overlaps[x, y]
        if overlap:
            i, j = overlap
            for word_x in self.domains[x].copy():
                if not any(word_x[i] == word_y[j] for word_y in self.domains[y]):
                    self.domains[x].remove(word_x)
                    revised = True
        return revised

    def ac3(self, arcs=None):
        queue = list(arcs) if arcs else [(x, y) for x in self.crossword.variables for y in self.crossword.neighbors(x)]
        while queue:
            (x, y) = queue.pop(0)
            if self.revise(x, y):
                if not self.domains[x]: return False
                for z in self.crossword.neighbors(x) - {y}:
                    queue.append((z, x))
        return True

    def assignment_complete(self, assignment):
        return len(assignment) == len(self.crossword.variables)

    def consistent(self, assignment):
        words = list(assignment.values())
        if len(words) != len(set(words)): return False
        for var, word in assignment.items():
            if len(word) != var.length: return False
            for neighbor in self.crossword.neighbors(var):
                if neighbor in assignment:
                    i, j = self.crossword.overlaps[var, neighbor]
                    if assignment[var][i] != assignment[neighbor][j]: return False
        return True

    def order_domain_values(self, var, assignment):
        def count_conflicts(word):
            count = 0
            for neighbor in self.crossword.neighbors(var):
                if neighbor not in assignment:
                    i, j = self.crossword.overlaps[var, neighbor]
                    for neighbor_word in self.domains[neighbor]:
                        if word[i] != neighbor_word[j]: count += 1
            return count
        return sorted(list(self.domains[var]), key=count_conflicts)

    def select_unassigned_variable(self, assignment):
        unassigned = [v for v in self.crossword.variables if v not in assignment]
        return min(unassigned, key=lambda v: (len(self.domains[v]), -len(self.crossword.neighbors(v))))

    def backtrack(self, assignment):
        if self.assignment_complete(assignment): return assignment
        var = self.select_unassigned_variable(assignment)
        for value in self.order_domain_values(var, assignment):
            if self.consistent({**assignment, var: value}):
                assignment[var] = value
                result = self.backtrack(assignment)
                if result: return result
                assignment.pop(var)
        return None

def main():
    if len(sys.argv) not in [3, 4]:
        sys.exit("Usage: python generate.py structure words [output]")
    crossword = Crossword(sys.argv[1], sys.argv[2])
    creator = CrosswordCreator(crossword)
    assignment = creator.solve()
    if assignment is None:
        print("No solution.")
    else:
        creator.print(assignment)
        if len(sys.argv) == 4:
            creator.save(assignment, sys.argv[3])

if __name__ == "__main__":
    main()
