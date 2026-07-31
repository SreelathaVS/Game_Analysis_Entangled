def direction_name(start_r, start_c, end_r, end_c):
  """Translates (start) -> (end) grid row/col shifts to cardinal/ordinal directions.

  Matrix orientation: Row index increases downwards, Column index increases
  rightwards.
  """
  dr = end_r - start_r
  dc = end_c - start_c

  row_dir = "" if dr == 0 else ("Down" if dr > 0 else "Up")
  col_dir = "" if dc == 0 else ("Right" if dc > 0 else "Left")

  if row_dir and col_dir:
    return f"{row_dir}-{col_dir}"
  elif row_dir:
    return row_dir
  elif col_dir:
    return col_dir
  return "Stayed"


def coord_str(r, c):
  """Formats grid coordinates (r, c) as [r, c]."""
  return f"[{r}, {c}]"