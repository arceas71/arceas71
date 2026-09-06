import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FFMpegWriter

FPS = 30
SECONDS = 18
WIDTH = 108
HEIGHT = 192

def initial_grid():
    y, x = np.mgrid[-1.8:1.8:HEIGHT*1j, -1.0:1.0:WIDTH*1j]
    r = np.sqrt(x*x + y*y)
    a = np.arctan2(y, x)
    pattern = (
        (np.sin(11*r - 5*a + 1.5*np.sin(3*a)) > 0.55) &
        (np.cos(7*a + 4*r) > 0.15) &
        (r < 1.55)
    )
    return pattern.astype(np.uint8)

def step(g):
    n = (
        g[:-2, :-2] + g[:-2, 1:-1] + g[:-2, 2:] +
        g[1:-1, :-2] + g[1:-1, 2:] +
        g[2:, :-2] + g[2:, 1:-1] + g[2:, 2:]
    )
    return (
        ((g[1:-1, 1:-1] == 1) & ((n == 2) | (n == 3))) |
        ((g[1:-1, 1:-1] == 0) & (n == 3))
    ).astype(np.uint8)

grid = np.pad(initial_grid(), 1)

fig = plt.figure(figsize=(9, 16), dpi=100, facecolor="#05030d")
ax = fig.add_axes([0, 0, 1, 1], facecolor="#05030d")
ax.set_xlim(0, WIDTH)
ax.set_ylim(HEIGHT, 0)
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
    bitrate=10000,
    extra_args=["-pix_fmt", "yuv420p", "-movflags", "+faststart"]
)

with writer.saving(fig, "game_of_life.mp4", dpi=100):
    for frame in range(FPS * SECONDS):
        if frame >= FPS:
            grid = np.pad(step(grid), 1)
        image.set_data(grid)
        writer.grab_frame()

plt.close(fig)
