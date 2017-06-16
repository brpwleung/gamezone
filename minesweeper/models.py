import math
import random

from django.core import validators
from django.db import models
from django.utils import timezone

class Game(models.Model):
    game_date = models.DateTimeField()
    num_rows = models.PositiveIntegerField()
    num_cols = models.PositiveIntegerField()
    mines = models.TextField(
        validators=[
            validators.validate_comma_separated_integer_list
            ]
        )

    def __str__(self):
        return str(self.game_date.timestamp())

class PlayerAction(models.Model):
    game = models.ForeignKey(Game, on_delete=models.CASCADE)
    command = models.CharField(max_length=200)
    tile = models.PositiveIntegerField()
    result = models.TextField(
        validators=[
            validators.validate_comma_separated_integer_list
            ]
        )

class GameMaster:
    game = None

    def _debug(self):
        print("***** Game Board *****")
        print("")
        for m in range(self._num_rows):
            s = ''
            for n in range(self._num_cols):
                x = self.mn_to_i(m, n)
                if x in self._mines:
                    s += 'x'
                else:
                    s += str(self.count[x]) 
            print(s)
        print("")

    def _flood_fill(self, i):
        def _ff_internal(i, visited, kept):
            if ((i is not None)
                    and (i not in visited)
                    and (i not in self._flagged)
                    and (i not in self._revealled)):
                visited += [i]
                (m, n) = self.i_to_mn(i)
                if (self._is_valid_tile(m, n)):
                    kept += [i]
                    if self.count[i] == 0:
                        _ff_internal(self.mn_to_i(m - 1, n), visited, kept)
                        _ff_internal(self.mn_to_i(m, n - 1), visited, kept)
                        _ff_internal(self.mn_to_i(m, n + 1), visited, kept)
                        _ff_internal(self.mn_to_i(m + 1, n), visited, kept)

        v = []
        k = []
        _ff_internal(i, v, k)
        return k

    def _is_valid_tile(self, m, n):
        m_is_valid = m >= 0 and m < self._num_rows
        n_is_valid = n >= 0 and n < self._num_cols
        return m_is_valid and n_is_valid

    def _game_not_done(f):
        def wrapper(self, *arg):
            if self._game_status == 0:
                a = f(self, *arg)
                return a
        return wrapper

    def _tile_not_flagged(f):
        def wrapper(self, tile, *arg):
            if tile not in self._flagged:
                a = f(self, tile, *arg)
                return a
        return wrapper

    def _tile_not_revealled(f):
        def wrapper(self, tile, *arg):
            if tile not in self._revealled:
                a = f(self, tile, *arg)
                return a
        return wrapper

    def num_tiles(self):
        """Return the number of gameboard tiles."""
        return self._num_rows * self._num_cols

    def i_to_mn(self, i):
        """Convert from tile index to tile coordinates.

        Argument:
        i -- the tile index

        Returns: A 2-tuple of the tile coordinates
        """
        if i >= 0 and i < self.num_tiles():
            return (i // self._num_cols, i % self._num_cols)
        else:
            return None

    def mn_to_i(self, m, n):
        """Convert from tile coordinates to tile index.

        Argument:
        m -- the tile's row position
        n -- the tile's column position

        Returns: The tile index
        """
        if self._is_valid_tile(m, n):
            return m*self._num_cols + n
        else:
            return None

    def dump(self):
        """Fetch a manifest of the present game state.

        Returns: A dictionary containing
            num_rows -- number of gameboard rows
            num_cols -- number of gameboard columns
            game_status -- game is ongoing (0), lost (<0), or won (>0)
            flagged -- the indices of flagged tiles
            revealled -- the indices of revealled tiles
            count -- corresponding mine counts for the revealled tiles
        """
        return {
            'num_rows': self._num_rows,
            'num_cols': self._num_cols,
            'game_status': self._game_status,
            'flagged': list(self._flagged),
            'revealled': list(self._revealled),
            'count': [self.count[i] for i in self._revealled],
            'mines': list(self._mines)
        }

    def reset(self, num_rows, num_cols, pct_mines):
        """Generate a new round of minesweeper gameplay.

        Arguments:
        num_rows -- number of gameboard rows
        num_cols -- number of gameboard columns
        pct_mines -- percentage (in [0, 1]) of mined tiles 
        """

        self._num_rows = num_rows
        self._num_cols = num_cols

        num_mines = math.floor(self.num_tiles() * pct_mines)
        self._mines = set(random.sample(range(self.num_tiles()), num_mines))

        self.count = [0] * self.num_tiles()
        for i in self._mines:
            (m, n) = self.i_to_mn(i)
            neighbourhood = [
                (-1, -1), (0, -1), (1, -1),
                (-1, 0), (0, 0), (1, 0),
                (-1, 1), (0, 1), (1, 1),
                ]
            for (x, y) in neighbourhood:
                j = self.mn_to_i(m + x, n + y)
                if j is not None:
                    self.count[j] += 1
        for i in self._mines:
            self.count[i] = -1

        self._flagged = set()
        self._revealled = set()

        self._active = set(range(self.num_tiles())) - self._mines
        self._game_status = 0

        GameMaster.game = Game(
            game_date=timezone.now(),
            num_rows=self._num_rows,
            num_cols=self._num_cols,
            mines=self._mines
            )
        GameMaster.game.save()

    @_game_not_done
    @_tile_not_flagged
    @_tile_not_revealled
    def reveal(self, tile):
        """Reveal a tile.

        Argument:
        tile -- index of the tile to be revealled

        Returns: A dictionary containing
            game_status
            revealled -- the tiles revealled by this game action
            count
        only if the game state has changed. Otherwise, a blank
        dictionary is returned.
        """

        results = {}
        if tile in self._mines:
            revealled = list(self._mines)
            self._game_status = -1
        else:
            if self.count[tile] > 0:
                revealled = [tile]
            else:
                revealled = self._flood_fill(tile)
            self._active -= set(revealled)
            if len(self._active) == 0:
                self._game_status = 1
        count = [self.count[i] for i in revealled]
        self._revealled |= set(revealled)
        results['revealled'] = revealled
        results['count'] = count
        results['game_status'] = self._game_status
        GameMaster.game.playeraction_set.create(
            command='reveal',
            tile=tile,
            result=results['revealled']
            )
        return results

    def _flag_tile(self, tile):
        self._flagged.add(tile)
        return [tile]

    def _unflag_tile(self, tile):
        self._flagged.discard(tile)
        return [tile]

    @_game_not_done
    @_tile_not_revealled
    def toggle_flag(self, tile):
        """Flag a tile to prevent further game action on the tile
        until it is unflagged. If the tile is already flagged, this
        method will unflag it instead.

        Argument: 
        tile -- index of the tile to be flagged

        Returns: A dictionary containing
            game_status
        and either one of the following list of tile indices:
            flagged -- the tile that was successfully flagged
            unflagged -- the tile that was successfully unflagged
        only if the game state has changed. Otherwise, a blank
        dictionary is returned.
        """

        results = {
            'game_status': self._game_status,
        }
        if tile not in self._flagged:
            results['flagged'] = self._flag_tile(tile)
            GameMaster.game.playeraction_set.create(
                command='flag',
                tile=tile,
                result=results['flagged']
                )
        else:
            results['unflagged'] = self._unflag_tile(tile)
            GameMaster.game.playeraction_set.create(
                command='unflag',
                tile=tile,
                result=results['unflagged']
                )
        return results

    def undo(self):
        results = {}
        pa = GameMaster.game.playeraction_set.order_by('-id').first()
        if pa is not None:
            if pa.command == 'flag':
                results['unflagged'] = self._unflag_tile(pa.tile)
            elif pa.command == 'unflag':
                results['flagged'] = self._flag_tile(pa.tile)
            elif pa.command == 'reveal':
                covered = [int(x) for x in pa.result[1:-1].split(',')]
                self._revealled -= set(covered)
                self._active |= set(covered)
                self._active -= self._mines
                results['covered'] = covered
            pa.delete()
        return results

def reset_game(difficulty='normal'):
    if difficulty == 'easy':
        gm.reset(8, 8, 0.16)
    elif difficulty == 'hard':
        gm.reset(13, 13, 0.40)
    else:
        gm.reset(10, 10, 0.25)
    gm._debug()
    game_data = gm.dump()

gm = GameMaster()
