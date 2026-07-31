class GridSetup:

  def __init__(self):
    p1_coords = [(7, 0), (6, 2), (8, 2), (6, 4), (8, 4), (7, 6)]
    p2_coords = [(1, 0), (0, 2), (2, 2), (0, 4), (2, 4), (1, 6)]

    p1_pieces = [1, 3, 2, 5, 4, 6]
    p2_pieces = [-1, -2, -3, -4, -5, -6]

    self.p1_pieces_coords = {}
    self.p2_pieces_coords = {}
    for idx in range(len(p1_pieces)):
      self.p1_pieces_coords[p1_pieces[idx]] = p1_coords[idx]
      self.p2_pieces_coords[p2_pieces[idx]] = p2_coords[idx]

    self.grid = [[0 for _ in range(7)] for _ in range(9)]

    for pid, (r, c) in self.p1_pieces_coords.items():
      self.grid[r][c] = pid
    for pid, (r, c) in self.p2_pieces_coords.items():
      self.grid[r][c] = pid

  def activePairs(self, active_player):
    coords_dict = (
        self.p1_pieces_coords
        if active_player == "p1"
        else self.p2_pieces_coords
    )
    pids = list(coords_dict.keys())
    valid_pairs = []

    for i in range(len(pids)):
      for j in range(len(pids)):
        if i == j:
          continue
        pid1, pid2 = pids[i], pids[j]
        r1, c1 = coords_dict[pid1]
        r2, c2 = coords_dict[pid2]

        row_diff = abs(r1 - r2)
        col_diff = abs(c1 - c2)

        is_row = r1 == r2 and col_diff > 1
        is_col = c1 == c2 and row_diff > 1
        is_diag = row_diff == col_diff and row_diff > 1

        if not (is_row or is_col or is_diag):
          continue

        step_r = 0 if r1 == r2 else (1 if r2 > r1 else -1)
        step_c = 0 if c1 == c2 else (1 if c2 > c1 else -1)
        is_blocked = False
        curr_r, curr_c = r1 + step_r, c1 + step_c
        while (curr_r, curr_c) != (r2, c2):
          if self.grid[curr_r][curr_c] != 0:
            is_blocked = True
            break
          curr_r += step_r
          curr_c += step_c

        if is_blocked:
          continue

        p1_moves = self.get_valid_moves_for_piece(
            pid1, pid2, active_player
        )
        if not p1_moves:
          continue

        pair_has_valid_sequence = False
        orig_r1, orig_c1 = r1, c1
        for move1_r, move1_c in p1_moves:
          self.grid[orig_r1][orig_c1] = 0
          self.grid[move1_r][move1_c] = pid1
          coords_dict[pid1] = (move1_r, move1_c)

          p2_moves = self.get_valid_moves_for_piece(
              pid2, None, active_player
          )
          if p2_moves:
            pair_has_valid_sequence = True

          self.grid[move1_r][move1_c] = 0
          self.grid[orig_r1][orig_c1] = pid1
          coords_dict[pid1] = (orig_r1, orig_c1)

          if pair_has_valid_sequence:
            break

        if pair_has_valid_sequence:
          valid_pairs.append((pid1, pid2))

    return valid_pairs

  def is_in_neighborhood_of_own_pieces(
      self, r, c, skipping_pid, other_pid, active_player
  ):
    coords_dict = (
        self.p1_pieces_coords
        if active_player == "p1"
        else self.p2_pieces_coords
    )
    for pid, (pr, pc) in coords_dict.items():
      if pid == skipping_pid or (
          other_pid is not None and pid == other_pid
      ):
        continue
      if abs(r - pr) <= 1 and abs(c - pc) <= 1:
        return True
    return False

  def get_valid_moves_for_piece(self, pid, other_pid, active_player):
    coords_dict = (
        self.p1_pieces_coords
        if active_player == "p1"
        else self.p2_pieces_coords
    )
    r, c = coords_dict[pid]
    moves = []

    for dr in [-1, 0, 1]:
      for dc in [-1, 0, 1]:
        if dr == 0 and dc == 0:
          continue
        nr, nc = r + dr, c + dc
        if 0 <= nr < 9 and 0 <= nc < 7 and self.grid[nr][nc] == 0:
          if not self.is_in_neighborhood_of_own_pieces(
              nr, nc, pid, other_pid, active_player
          ):
            moves.append((nr, nc))
    return moves