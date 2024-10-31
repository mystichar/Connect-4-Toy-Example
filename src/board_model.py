from pydantic import BaseModel, conint, field_validator
from typing import Dict, Tuple, Optional

# Define a constrained integer type alias
CellValue = Optional[conint(strict=True, ge=-1, le=1)]

class Connect4Board(BaseModel):
    board: Dict[Tuple[int, int], CellValue]

    @field_validator('board')
    def validate_board_values(cls, board):
        for key, value in board.items():
            if value not in {0, -1, 1, None}:
                raise ValueError(f"Each cell must have a value of 0, -1, 1, or None. Invalid value at {key}: {value}")
        return board