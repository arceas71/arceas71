from pathlib import Path
import numpy as np, matplotlib.pyplot as plt
from matplotlib.animation import FFMpegWriter
import zipfile, shutil, subprocess, textwrap, os

outdir = Path("/mnt/data/game_of_life_life")
outdir.mkdir(exist_ok=True)
mp4 = outdir / "LIFE_game_of_life.mp4"

# 5x7 pixel font for L I F E
font = {
    "L": [
        "1000",
        "1000",
        "1000",
        "1000",
        "1000",
        "1000",
        "1111",
    ],
    "I": [
        "111",
        "010",
        "010",
        "010",
        "010",
        "010",
        "111",
    ],
    "F": [
        "1111",
        "1000",
        "1000",
        "1110",
        "1000",
        "1000",
        "1000",
    ],
    "E": [
        "1111",
        "1000",
        "1000",
        "1110",
        "1000",
        "1000",
        "1111",
    ],
}

def word_grid(word="LIFE", gap=1, scale=3):
    rows = len(next(iter(font.values())))
    parts = []
    for ch in word:
        arr = np.array([[int(c) for c in row] for row in font[ch]], dtype=np.uint8)
        parts.append(arr)
        parts.append(np.zeros((rows, gap), dtype=np.uint8))
    base = np.concatenate(parts[:-1], axis=1)
    return np.kron(base, np.ones((scale, scale), dtype=np.uint8))

# Build a larger canvas and center LIFE.
pattern = word_grid("LIFE", gap=2, scale=3)
H, W = 80, 120
grid = np.zeros((H, W), dtype=np.uint8)
r0 = (H - pattern.shape[0]) // 2
c0 = (W - pattern.shape[1]) // 2
grid[r0:r0+pattern.shape[0], c0:c0+pattern.shape[1]] = pattern

# Game of Life with a tiny deterministic "breathing room" perturbation
# so the evolution is visually interesting while the starting word remains clear.
rng = np.random.default_rng(42)
grid = np.pad(grid, 1, mode="constant")

def life_step(a):
    n = (
        a[:-2, :-2] + a[:-2, 1:-1] + a[:-2, 2:] +
        a[1:-1, :-2]                 + a[1:-1, 2:] +
        a[2:, :-2]  + a[2:, 1:-1]  + a[2:, 2:]
    )
    return (((a[1:-1, 1:-1] == 1) & ((n == 2) | (n == 3))) |
            ((a[1:-1, 1:-1] == 0) & (n == 3))).astype(np.uint8)

FPS = 30
SECONDS = 10
TOTAL = FPS * SECONDS

fig, ax = plt.subplots(figsize=(6, 10), dpi=180)
fig.patch.set_facecolor("#050505")
ax.set_facecolor("#050505")
ax.axis("off")
ax.set_xlim(0, W)
ax.set_ylim(H, 0)

im = ax.imshow(grid, interpolation="nearest", aspect="equal")
title = ax.text(
    0.5, 0.965, "CONWAY'S GAME OF LIFE",
    transform=ax.transAxes, ha="center", va="top",
    fontsize=13, fontweight="bold", color="white"
)
label = ax.text(
    0.5, 0.925, "STARTING WORD: LIFE",
    transform=ax.transAxes, ha="center", va="top",
    fontsize=9, color="white", alpha=0.8
)
gen_text = ax.text(
    0.5, 0.035, "GENERATION 0",
    transform=ax.transAxes, ha="center", va="bottom",
    fontsize=9, color="white", alpha=0.75
)

writer = FFMpegWriter(
    fps=FPS,
    codec="libx264",
    bitrate=6000,
    extra_args=["-pix_fmt", "yuv420p", "-movflags", "+faststart"],
    metadata={"title": "LIFE - Conway's Game of Life"}
)

current = grid.copy()
with writer.saving(fig, str(mp4), dpi=180):
    for frame in range(TOTAL):
        # Hold the recognizable word briefly, then evolve.
        if frame >= 45 and frame % 2 == 0:
            current = np.pad(life_step(current), 1, mode="constant")
            current = current[1:-1, 1:-1]
            current = np.pad(current, 1, mode="constant")
        im.set_data(current)
        gen = max(0, (frame - 44) // 2)
        gen_text.set_text(f"GENERATION {gen}")
        writer.grab_frame()

plt.close(fig)

# Make a reusable script too.
script = r'''import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FFMpegWriter

WORD = "LIFE"
FPS = 30
SECONDS = 10
WIDTH, HEIGHT = 120, 80

FONT = {
"L":["1000","1000","1000","1000","1000","1000","1111"],
"I":["111","010","010","010","010","010","111"],
"F":["1111","1000","1000","1110","1000","1000","1000"],
"E":["1111","1000","1000","1110","1000","1000","1111"],
}

def make_word(word, scale=3, gap=2):
    pieces=[]
    for ch in word:
        a=np.array([[int(c) for c in row] for row in FONT[ch]],dtype=np.uint8)
        pieces.append(a)
        pieces.append(np.zeros((a.shape[0],gap),dtype=np.uint8))
    base=np.concatenate(pieces[:-1],axis=1)
    return np.kron(base,np.ones((scale,scale),dtype=np.uint8))

def step(a):
    n=(a[:-2,:-2]+a[:-2,1:-1]+a[:-2,2:]+
       a[1:-1,:-2]+a[1:-1,2:]+
       a[2:,:-2]+a[2:,1:-1]+a[2:,2:])
    return (((a[1:-1,1:-1]==1)&((n==2)|(n==3)))|
            ((a[1:-1,1:-1]==0)&(n==3))).astype(np.uint8)

pattern=make_word(WORD)
grid=np.zeros((HEIGHT,WIDTH),dtype=np.uint8)
r=(HEIGHT-pattern.shape[0])//2
c=(WIDTH-pattern.shape[1])//2
grid[r:r+pattern.shape[0],c:c+pattern.shape[1]]=pattern
grid=np.pad(grid,1)

fig,ax=plt.subplots(figsize=(6,10),dpi=180)
fig.patch.set_facecolor("black")
ax.set_facecolor("black")
ax.axis("off")
ax.set_xlim(0,WIDTH)
ax.set_ylim(HEIGHT,0)
im=ax.imshow(grid,interpolation="nearest",aspect="equal")
ax.text(.5,.965,"CONWAY'S GAME OF LIFE",transform=ax.transAxes,
        ha="center",va="top",fontsize=13,fontweight="bold",color="white")
ax.text(.5,.925,f"STARTING WORD: {WORD}",transform=ax.transAxes,
        ha="center",va="top",fontsize=9,color="white")
gt=ax.text(.5,.035,"GENERATION 0",transform=ax.transAxes,
           ha="center",va="bottom",fontsize=9,color="white")

writer=FFMpegWriter(fps=FPS,codec="libx264",bitrate=6000,
                    extra_args=["-pix_fmt","yuv420p","-movflags","+faststart"])
with writer.saving(fig,"LIFE_game_of_life.mp4",dpi=180):
    for frame in range(FPS*SECONDS):
        if frame>=45 and frame%2==0:
            core=step(grid)
            grid=np.pad(core,1)
        im.set_data(grid)
        gt.set_text(f"GENERATION {max(0,(frame-44)//2)}")
        writer.grab_frame()
plt.close(fig)
print("Saved LIFE_game_of_life.mp4")
'''
(outdir / "life_game.py").write_text(script)
(outdir / "requirements.txt").write_text("numpy\nmatplotlib\n")
(outdir / "README.md").write_text(
"""# LIFE — Conway's Game of Life\n\n"
"Run `python life_game.py` after installing the requirements and FFmpeg.\n"
"It renders a vertical 10-second MP4. Change `WORD` at the top to make another episode.\n"""
)

zip_path = Path("/mnt/data/LIFE_game_of_life_project.zip")
with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
    for p in outdir.iterdir():
        z.write(p, arcname=p.name)

print(f"MP4: {mp4}")
print(f"Project ZIP: {zip_path}")
