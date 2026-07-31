import random
from .grid_setup import GridSetup


class EntangledGameSimulation:

  def __init__(self, p1_type="random", p2_type="random", target_score=5):
    self.board = GridSetup()
    self.p1_type = p1_type
    self.p2_type = p2_type

    self.scores = {"p1": 0, "p2": 0}
    self.scored_interceptions = set()
    self.move_count = 0
    self.current_player = "p1"
    self.target_score = target_score

  def switch_player(self):
    self.current_player = "p2" if self.current_player == "p1" else "p1"

  def get_opponent(self):
    return "p2" if self.current_player == "p1" else "p1"

  def check_game_over(self, check_stuck=True):
    if (
        self.scores["p1"] >= self.target_score
        and self.scores["p2"] >= self.target_score
    ):
      return True, "draw", "draw_simultaneous_target"

    if self.scores["p1"] >= self.target_score:
      return True, "p1", "p1_win_score"
    if self.scores["p2"] >= self.target_score:
      return True, "p2", "p2_win_score"

    if check_stuck:
      current_active_moves = self.board.activePairs(self.current_player)
      if len(current_active_moves) == 0:
        winner = "p2" if self.current_player == "p1" else "p1"
        return True, winner, f"{winner}_win_opponent_stuck"

    return False, None, None

  def check_scoring_for_move(self):
    p1_blocking_pts = self.evaluate_blocking_points(
        pair_owner="p2", blocker_player="p1"
    )
    p2_blocking_pts = self.evaluate_blocking_points(
        pair_owner="p1", blocker_player="p2"
    )
    return p1_blocking_pts, p2_blocking_pts

  def evaluate_blocking_points(self, pair_owner, blocker_player):
    pair_coords = (
        self.board.p1_pieces_coords
        if pair_owner == "p1"
        else self.board.p2_pieces_coords
    )
    blocker_coords = (
        self.board.p1_pieces_coords
        if blocker_player == "p1"
        else self.board.p2_pieces_coords
    )

    pair_pids = list(pair_coords.keys())
    blocker_pids = list(blocker_coords.keys())

    new_points = 0

    for i in range(len(pair_pids)):
      for j in range(i + 1, len(pair_pids)):
        sp1, sp2 = pair_pids[i], pair_pids[j]

        r1, c1 = pair_coords[sp1]
        r2, c2 = pair_coords[sp2]

        row_diff = abs(r1 - r2)
        col_diff = abs(c1 - c2)

        is_row = r1 == r2 and col_diff >= 2
        is_col = c1 == c2 and row_diff >= 2
        is_diag = row_diff == col_diff and row_diff >= 2

        if not (is_row or is_col or is_diag):
          continue

        steps = max(row_diff, col_diff)
        step_r = (r2 - r1) // steps
        step_c = (c2 - c1) // steps

        for b_pid in blocker_pids:
          br, bc = blocker_coords[b_pid]

          in_row = is_row and br == r1 and min(c1, c2) < bc < max(c1, c2)
          in_col = is_col and bc == c1 and min(r1, r2) < br < max(r1, r2)
          in_diag = (
              is_diag
              and abs(r1 - br) == abs(c1 - bc)
              and abs(r2 - br) == abs(c2 - bc)
              and min(r1, r2) < br < max(r1, r2)
              and min(c1, c2) < bc < max(c1, c2)
          )

          if not (in_row or in_col or in_diag):
            continue

          is_blocked = False
          for step_idx in range(1, steps):
            curr_r = r1 + step_r * step_idx
            curr_c = c1 + step_c * step_idx
            if (curr_r, curr_c) != (br, bc) and self.board.grid[curr_r][
                curr_c
            ] != 0:
              is_blocked = True
              break

          if is_blocked:
            continue

          state_tuple = (
              min(sp1, sp2),
              max(sp1, sp2),
              b_pid,
              (r1, c1),
              (r2, c2),
              (br, bc),
          )

          if state_tuple not in self.scored_interceptions:
            self.scored_interceptions.add(state_tuple)
            new_points += 1

    return new_points

  def execute_turn(self, chosen_pair):
    pid1, pid2 = chosen_pair[0], chosen_pair[1]
    coords_dict = (
        self.board.p1_pieces_coords
        if self.current_player == "p1"
        else self.board.p2_pieces_coords
    )

    # --- STEP 1: PIECE 1 ACTION ---
    p1_moves = self.board.get_valid_moves_for_piece(
        pid1, pid2, self.current_player
    )
    orig_r1, orig_c1 = coords_dict[pid1]

    guaranteed_p1_moves = []
    for mr, mc in p1_moves:
      self.board.grid[orig_r1][orig_c1] = 0
      self.board.grid[mr][mc] = pid1
      coords_dict[pid1] = (mr, mc)

      p2_moves_after = self.board.get_valid_moves_for_piece(
          pid2, None, self.current_player
      )
      if p2_moves_after:
        guaranteed_p1_moves.append((mr, mc))

      self.board.grid[mr][mc] = 0
      self.board.grid[orig_r1][orig_c1] = pid1
      coords_dict[pid1] = (orig_r1, orig_c1)

    if not guaranteed_p1_moves:
      raise ValueError(
          f"execute_turn received pair {chosen_pair} with no legal sequence."
      )

    move1 = random.choice(guaranteed_p1_moves)

    self.board.grid[orig_r1][orig_c1] = 0
    self.board.grid[move1[0]][move1[1]] = pid1
    coords_dict[pid1] = move1

    # --- STEP 2: PIECE 2 ACTION ---
    p2_moves = self.board.get_valid_moves_for_piece(
        pid2, None, self.current_player
    )
    move2 = random.choice(p2_moves)

    orig_r2, orig_c2 = coords_dict[pid2]
    self.board.grid[orig_r2][orig_c2] = 0
    self.board.grid[move2[0]][move2[1]] = pid2
    coords_dict[pid2] = move2

    # --- SCORING EVALUATION AT TURN END ---
    p1_new_pts, p2_new_pts = self.check_scoring_for_move()
    self.scores["p1"] += p1_new_pts
    self.scores["p2"] += p2_new_pts

    self.move_count += 1
    self.switch_player()

    game_over, winner, reason = self.check_game_over(check_stuck=True)
    return game_over, winner, reason

  def run_simulation(self):
    while True:
      game_over, winner, reason = self.check_game_over(check_stuck=True)
      if game_over:
        return {
            "winner": winner,
            "reason": reason,
            "total_moves": self.move_count,
            "final_scores": self.scores.copy(),
        }

      valid_pairs = self.board.activePairs(self.current_player)
      current_type = (
          self.p1_type if self.current_player == "p1" else self.p2_type
      )

      if current_type == "random":
        chosen_pair = random.choice(valid_pairs)
      else:
        raise NotImplementedError(
            f"Player type '{current_type}' is not implemented in this build."
        )

      early_end, winner, reason = self.execute_turn(chosen_pair)

      if early_end:
        return {
            "winner": winner,
            "reason": reason,
            "total_moves": self.move_count,
            "final_scores": self.scores.copy(),
        }