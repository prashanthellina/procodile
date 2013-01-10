
# disable these imports if you do not
# need to produce debug images
if 1:
    import Image
    import ImageDraw

from itertools import chain

from procodile.procedural import BaseGenerator

COLORS = {
            'black': (0, 0, 0),
            'white': (255, 255, 255),
            'red': (255, 0, 0),
            'green': (0, 255, 0),
            'blue': (0, 0, 255),

            'light-blue': (0x00, 0x99, 0xff),
            'light-green': (0x33, 0x99, 0x00),
            'brown': (0x66, 0x33, 0x00),

            'yellow-lightest': (0xff, 0xff, 0x99),
            'yellow-lighter': (0xff, 0xcc, 0x00),
            'yellow-light': (0xff, 0x99, 0x00),
            'yellow': (0xff, 0x66, 0x00),

            'red-lightest': (0xcc, 0x66, 0x99),
            'red-lighter': (0xcc, 0x33, 0x00),
            'red-light': (0x99, 0x00, 0x00),
            'red': (0x66, 0x00, 0x00),

            'purple-lightest': (0x99, 0x99, 0xff),
            'purple-lighter': (0x66, 0x66, 0x99),
            'purple-light': (0x66, 0x33, 0x99),
            'purple': (0x66, 0x00, 0x99),
         }

class CellularAutomataCity(BaseGenerator):
    CONFIG = (
                'size', (1000, 20000), # in metres

                'cell_size', 100, # metres square

                # number of spawn points for city growth
                'num_villages', (1, 10),

                'num_forests', (1, 10),
                'forests_percentage', (.01, .1),

                'num_waters', (1, 10),
                'waters_percentage', (.01, .1),

                # level1, level2, level3, level4
                'level_percentages', [(.05, .2, .3, .45)],

                # Habitable zone percentages
                # residential, commercial, industrial
                'habitable_zone_percentages', [(1.0, .00, .00)],
                #'habitable_zone_percentages', [(.70, .30, .20)],

                # for level1, level2, level3, level4
                'layout_max_cells', [(25, 50, 100, 400)],

                # layout max elongation ratio (long side / short side)
                'layout_max_elongation_ratio', (2.0, 6.0),
             )

    SUB_GENERATORS = {
                     }

    def generate(self, config):

        grid = Grid(config, self.picker)
        grid.generate()
        groups = grid.group()

        grid.generate_image(open('/tmp/test.png', 'wb'))
        grid.generate_groups_image(groups, open('/tmp/test1.png', 'wb'))

class Budget: pass

def setattrs(**kwargs):

    def fn(obj):
        for k, v in kwargs.iteritems():
            if callable(v):
                v = v()
            setattr(obj, k, v)

    return fn

def value_distributor(distribution, picker):
    total = 0.0

    d = []
    for value, probability in distribution:
        total += probability
        d.append((value, total))

    def distributor():
        val = picker.random()

        for value, probability in d:
            if val <= probability:
                return value

    return distributor

class Grid:

    def __init__(self, config, picker):

        self.config = config
        self.picker = picker

        self.grid = []
        self.budget = self._compute_budget()

        self.rows = rows = self.budget.length
        self.cols = cols = self.budget.width

        for irow in xrange(rows):
            row = []

            for icol in xrange(cols):
                cell = Cell(self, irow, icol)
                row.append(cell)

            self.grid.append(row)

        self.unused_cells = self._get_all_cells()

    def get_neighbours(self, row, col):

        min_row = row - 1
        max_row = row + 1
        min_col = col - 1
        max_col = col + 1

        min_row = 0 if min_row < 0 else min_row
        max_row = self.rows - 1 if max_row >= self.rows else max_row

        min_col = 0 if min_col < 0 else min_col
        max_col = self.cols - 1 if max_col >= self.cols else max_col

        coords = [(r, c) for r in xrange(min_row, max_row + 1) \
                         for c in xrange(min_col, max_col + 1)]

        coords.remove((row, col))

        cells = [self.grid[r][c] for r, c in coords]
        return cells

    def _get_all_cells(self):
        rows = [row for row in self.grid]
        cells = list(chain(*rows))
        return dict([((c.row, c.col), c) for c in cells])

    def _compute_budget(self):
        budget = Budget()
        c = self.config

        length, width = c.size, c.size
        num_length = length / c.cell_size
        num_width = width / c.cell_size

        budget.total = num_length * num_width
        budget.length = num_length
        budget.width = num_width

        budget.forest = budget.total * c.forests_percentage
        budget.water = budget.total * c.waters_percentage

        budget.habitable = budget.total - budget.forest - budget.water

        level_cells = [0] * 4
        for index, percentage in enumerate(c.level_percentages):
            level_cells[index] = budget.habitable * percentage

        budget.level = level_cells

        return budget

    def _get_unused_cells(self, num=1,
                            set_cell_props = lambda x: None):
        cells = []

        for i in xrange(num):
            cell = self.picker.choice(self.unused_cells.keys())
            cell = self.unused_cells.pop(cell)
            cell.used = True
            set_cell_props(cell)
            cells.append(cell)

        return cells

    def generate(self):

        budget = self.budget
        c = self.config

        # generate forests
        f = setattrs(type=Cell.FOREST, habitable=False)
        forest_starts = self._get_unused_cells(c.num_forests, f)
        budget.forest -= c.num_forests
        self.grow(forest_starts, budget.forest, f)

        # generate water bodies
        f = setattrs(type=Cell.WATER, habitable=False)
        water_starts = self._get_unused_cells(c.num_waters, f)
        budget.water -= c.num_waters
        self.grow(water_starts, budget.water, f)

        # generate habitable regions
        distribution = zip(Cell.HABITABLE_TYPES, c.habitable_zone_percentages)
        habitation_type = value_distributor(distribution, self.picker)
        f = setattrs(type=habitation_type, habitable=True, level=1)
        level_starts = self._get_unused_cells(c.num_villages, f)
        budget.level[0] -= c.num_villages

        for i in xrange(len(budget.level)):
            f = setattrs(type=habitation_type, habitable=True, level=i+1)
            all, boundary = self.grow(level_starts, budget.level[i], f)
            level_starts = boundary

    def grow(self, start_cells, num,
                set_cell_props = lambda c: None):

        all_cells = []
        boundary_cells = start_cells[:]

        while num > 0 and self.unused_cells:

            if not boundary_cells:
                cell = self._get_unused_cells()[0]
                boundary_cells.append(cell)
                all_cells.append(cell)
                num -= 1
                cell.used = True
                set_cell_props(cell)

            cell_index = self._get_random_index(boundary_cells)
            cell = boundary_cells[cell_index]

            unused = self._get_unused_neighbours(cell)
            if not unused:
                boundary_cells.pop(cell_index)
                continue

            ncell = self._pop_random_item(unused)
            all_cells.append(ncell)
            ncell.used = True
            set_cell_props(ncell)

            if self._get_unused_neighbours(ncell):
                boundary_cells.append(ncell)

            num -= 1
            self.unused_cells.pop((ncell.row, ncell.col))

        return all_cells, boundary_cells

    def group(self):
        groups = []

        unused = self._get_all_cells()
        used = {}

        while unused:
            seed_coord = self.picker.choice(unused.keys())
            seed = unused.pop(seed_coord)
            used[seed_coord] = seed
            group = Group(seed, unused, used, self)

            while group.grow():
                pass

            groups.append(group)

        return groups

    def _get_unused_neighbours(self, cell):
        return [c for c in cell.get_neighbours() if not c.used]

    def _get_random_index(self, seq):
        return self.picker.randint(0, len(seq) - 1)

    def _pop_random_item(self, seq):
        index = self._get_random_index(seq)
        return seq.pop(index)

    def generate_image(self, stream):
        img = Image.new('RGB', (self.rows, self.cols))
        draw = ImageDraw.Draw(img)

        for irow, row in enumerate(self.grid):
            for icol, cell in enumerate(row):
                color = cell.get_color()
                draw.point((irow, icol), color)

        img.save(stream, 'PNG')

    def generate_groups_image(self, groups, stream):
        S = 8
        img = Image.new('RGB', (self.rows * S, self.cols * S))
        draw = ImageDraw.Draw(img)

        for g in groups:
            color = g.get_color()

            coords = [
                        (g.min_row * S, g.min_col * S),
                        (g.max_row * S, g.max_col * S),
                     ]

            draw.rectangle(coords, fill=color)

        img.save(stream, 'PNG')

class Cell:

    RESIDENTIAL = 0
    COMMERCIAL = 1
    INDUSTRIAL = 2

    HABITABLE_TYPES = [RESIDENTIAL, COMMERCIAL, INDUSTRIAL]

    FOREST = 0
    WATER = 1
    MOUNTAINS = 2

    UNHABITABLE_TYPES = [FOREST, WATER, MOUNTAINS]

    def __init__(self, grid=None, row=None, col=None):
        #: when a cell is used to represent habitable or unhabitable region
        #   it is said to be used up.
        self.used = False

        #: Whether this cell is a populable area
        self.habitable = False

        #: primitiveness level (1, 2, 3, 4) 1 is most primitive.
        self.level = None

        #: grid to which this cell belongs
        self.grid = grid

        #: residential/commercial/industrial or forest/water/mountain
        self.type = None

        #: row, column
        self.row = row
        self.col = col

    def get_neighbours(self):
        return self.grid.get_neighbours(self.row, self.col)

    def is_same_type(self, cell):
        if self.used != cell.used:
            return False

        if self.habitable != cell.habitable:
            return False

        if self.type != cell.type:
            return False

        if self.level != cell.level:
            return False

        return True

    def get_color(self):

        if not self.used:
            return COLORS['black']

        if not self.habitable:
            if self.type == Cell.FOREST:
                return COLORS['light-green']

            if self.type == Cell.WATER:
                return COLORS['light-blue']

            if self.type == Cell.MOUNTAINS:
                return COLORS['brown']

        else:

            if self.type == Cell.RESIDENTIAL:
                if self.level == 1:
                    return COLORS['red-lightest']
                if self.level == 2:
                    return COLORS['red-lighter']
                if self.level == 3:
                    return COLORS['red-light']
                if self.level == 4:
                    return COLORS['red']

            if self.type == Cell.COMMERCIAL:
                if self.level == 1:
                    return COLORS['yellow-lightest']
                if self.level == 2:
                    return COLORS['yellow-lighter']
                if self.level == 3:
                    return COLORS['yellow-light']
                if self.level == 4:
                    return COLORS['yellow']

            if self.type == Cell.INDUSTRIAL:
                if self.level == 1:
                    return COLORS['purple-lightest']
                if self.level == 2:
                    return COLORS['purple-lighter']
                if self.level == 3:
                    return COLORS['purple-light']
                if self.level == 4:
                    return COLORS['purple']

        return COLORS['white']

class Group:

    LEFT = 0
    RIGHT = 1
    UP = 2
    DOWN = 3

    DIRECTIONS = (LEFT, RIGHT, UP, DOWN)

    def __init__(self, seed_cell, unused_cells, used_cells, grid):
        self.habitable = seed_cell.habitable
        self.type = seed_cell.type
        self.level = seed_cell.type

        self.rows = property(self._get_rows)
        self.cols = property(self._get_cols)

        self.row = property(self._get_row)
        self.col = property(self._get_col)

        self.min_row = self.max_row = seed_cell.row
        self.min_col = self.max_col = seed_cell.col

        self.cells = [seed_cell]
        self.unused = unused_cells
        self.used = used_cells

        self._config = grid.config
        self._picker = grid.picker
        self._grid = grid
        self._directions = list(self.DIRECTIONS)

    def get_color(self):
        if self.cells:
            return self.cells[0].get_color()

        else:
            return COLORS['white']

    def _get_row(self):
        return self.min_row

    def _get_col(self):
        return self.min_col

    def _get_rows(self):
        return self.max_row - self.min_row + 1

    def _get_cols(self):
        return self.max_col - self.min_col + 1

    def grow(self):
        self._picker.shuffle(self._directions)

        grown = False

        for direction in self._directions:
            grown = self.grow_in_direction(direction)
            if grown:
                break

        return grown

    def grow_in_direction(self, direction):
        grid = self._grid
        c = self._config

        min_row, max_row = 0, 0
        min_col, max_col = 0, 0

        rows = self._get_rows()
        cols = self._get_cols()
        row = self._get_row()
        col = self._get_col()

        if direction == self.LEFT:
            min_row, max_row = row, row + rows - 1
            min_col = max_col = col - 1

        elif direction == self.RIGHT:
            min_row, max_row = row, row + rows - 1
            min_col = max_col = col + cols

        elif direction == self.UP:
            min_row = max_row = row - 1
            min_col, max_col = col, col + cols - 1

        elif direction == self.DOWN:
            min_row = max_row = row - 1
            min_col, max_col = col, col + cols - 1

        # check if growth is going beyond grid boundaries
        if min_col < 0 or min_row < 0:
            return False

        if max_col >= grid.cols or max_row >= grid.rows:
            return False

        # compute new location and dimensions of group
        n_min_col = min_col if min_col < self.min_col else self.min_col
        n_max_col = max_col if max_col > self.max_col else self.max_col
        n_min_row = min_row if min_row < self.min_row else self.min_row
        n_max_row = max_row if max_row > self.max_row else self.max_row

        # does new growth lead make group exceed area limitation?
        if self.habitable:
            new_area = (n_max_col - n_min_col + 1) * (n_max_row - n_min_row + 1)
            max_area = c.layout_max_cells[self.level]
            if new_area > max_area:
                return False

        # does group elongation ratio exceed max?
        sides = [(n_max_col - n_min_col + 1), (n_max_row - n_min_row + 1)]
        ratio = float(max(sides)) / float(min(sides))
        if ratio > c.layout_max_elongation_ratio:
            return False

        # generate growth cell coordinates
        cell_coords = [(r, c) for r in xrange(min_row, max_row + 1) \
                              for c in xrange(min_col, max_col + 1)]
        cell_coords = list(chain(cell_coords))

        # ensure all growth cells are unused and are of same type
        # a group cell type
        for c in cell_coords:
            if c in self.used:
                return False

            cell = self.unused[c]
            if not cell.is_same_type(self.cells[0]):
                return False

        # grow
        for c in cell_coords:
            cell = self.unused.pop(c)
            self.used[c] = cell
            self.cells.append(cell)

        # adjust group location and size properties to reflect inclusion
        # of growth area.
        self.min_col = n_min_col
        self.max_col = n_max_col
        self.min_row = n_min_row
        self.max_row = n_max_row

        return True
