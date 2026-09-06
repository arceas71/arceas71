import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FFMpegWriter

WORD = "LIFE"
FPS = 30
SECONDS = 10

FONT = {
    "L": ["1000","1000","1000","1000","1000","1000","1111"],
    "I": ["111","010","010","010","010","010","111"],
    "F": ["1111","1000","1000","1110","1000","1000","1000"],
    "E": ["1111","1000","1000","1110","1000","1000","1111"]
}

def make_grid():
    pieces = []
    for ch in WORD:
        pieces.append(np.array([[int(x) for x in row] for row in FONT[ch]], dtype=np.uint8))
        pieces.append(np.zeros((7, 2), dtype=np.uint8))
    pattern = np.kron(
        np.concatenate(pieces[:-1], axis=1),
        np.ones((2, 2), dtype=np.uint8)
    )
    grid = np.zeros((192, 108), dtype=np.uint8)
    y = (192 - pattern.shape[0]) // 2
    x = (108 - pattern.shape[1]) // 2
    grid[y:y+pattern.shape[0], x:x+pattern.shape[1]] = pattern
    return np.pad(grid, 1)

def step(grid):
    n = (
        grid[:-2, :-2] + grid[:-2, 1:-1] + grid[:-2, 2:] +
        grid[1:-1, :-2] + grid[1:-1, 2:] +
        grid[2:, :-2] + grid[2:, 1:-1] + grid[2:, 2:]
    )
    return (
        ((grid[1:-1, 1:-1] == 1) & ((n == 2) | (n == 3))) |
        ((grid[1:-1, 1:-1] == 0) & (n == 3))
    ).astype(np.uint8)

grid = make_grid()

fig = plt.figure(figsize=(9, 16), dpi=100, facecolor="#07111f")
ax = fig.add_axes([0, 0, 1, 1], facecolor="#07111f")
ax.set_xlim(0, 108)
ax.set_ylim(192, 0)
ax.axis("off")

image = ax.imshow(
    grid,
    cmap="magma",
    vmin=0,
    vmax=1,
    interpolation="nearest",
    aspect="equal"
)

writer = FFMpegWriter(
    fps=FPS,
    codec="libx264",
    bitrate=8000,
    extra_args=["-pix_fmt", "yuv420p", "-movflags", "+faststart"]
)

with writer.saving(fig, "LIFE_game_of_life.mp4", dpi=100):
    for frame in range(FPS * SECONDS):
        if frame >= 30 and frame % 2 == 0:
            grid = np.pad(step(grid), 1)
        image.set_data(grid)
        writer.grab_frame()

plt.close(fig)
