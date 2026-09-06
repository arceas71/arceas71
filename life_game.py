import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation, FFMpegWriter
import shutil

SEED = 1337
np.random.seed(SEED)

WIDTH = 1080
HEIGHT = 1920
FPS = 30
CELL_SIZE = 4
GRID_W = WIDTH // CELL_SIZE
GRID_H = HEIGHT // CELL_SIZE

HOLD_SECONDS = 1.0
EVOLVE_SECONDS = 14.0
HOLD_FRAMES = int(HOLD_SECONDS * FPS)
EVOLVE_FRAMES = int(EVOLVE_SECONDS * FPS)
TOTAL_FRAMES = HOLD_FRAMES + EVOLVE_FRAMES

ARM_COUNT = 5
PETAL_COUNT = 10
SPIRAL_TWIST = 0.12
RING_FREQ = 0.6
ARM_THRESH = 0.75
RING_THRESH = 0.8
PETAL_THRESH = 0.3
CORE_RADIUS = 5.0
MAX_RADIUS_FACTOR = 0.9
DILATE_ITERATIONS = 2

ZOOM_MARGIN = 1.25

AGE_CAP = 40
GLOW_STRENGTH = 0.55
GLOW_RADIUS = 4

BACKGROUND_COLOR = np.array([0.02, 0.02, 0.06])
CELL_COLOR = np.array([0.72, 0.18, 0.92])
GLOW_COLOR = CELL_COLOR
MIN_BRIGHTNESS = 0.78

OUTPUT_FILENAME = "game_of_life.mp4"

def build_mandala(grid_h, grid_w):
    cy = grid_h / 2.0
    cx = grid_w / 2.0
    y, x = np.indices((grid_h, grid_w)).astype(np.float64)
    dx = x - cx
    dy = y - cy
    r = np.sqrt(dx * dx + dy * dy)
    theta = np.arctan2(dy, dx)
    max_r = MAX_RADIUS_FACTOR * min(grid_h, grid_w) / 2.0

    arm_phase = ARM_COUNT * theta + SPIRAL_TWIST * r
    arm_val = np.cos(arm_phase)
    ring_val = np.cos(RING_FREQ * r)
    petal_val = np.cos(PETAL_COUNT * theta)

    mask_core = r <= CORE_RADIUS
    mask_arms = (arm_val > ARM_THRESH) & (r <= max_r) & (r >= CORE_RADIUS * 1.5)
    mask_rings = (ring_val > RING_THRESH) & (r <= max_r)
    mask_petals = (petal_val > PETAL_THRESH) & (r <= max_r * 0.85)

    alive = mask_core | mask_arms | (mask_rings & mask_petals)
    alive = dilate(alive, DILATE_ITERATIONS)
    return alive

def dilate(mask, iterations):
    result = mask.copy()
    for _ in range(iterations):
        up = np.roll(result, -1, axis=0)
        down = np.roll(result, 1, axis=0)
        left = np.roll(result, -1, axis=1)
        right = np.roll(result, 1, axis=1)
        result = result | up | down | left | right
    return result

def step_life(grid):
    g = grid.astype(np.uint8)
    padded = np.pad(g, 1, mode="constant")
    neighbors = (
        padded[0:-2, 0:-2] + padded[0:-2, 1:-1] + padded[0:-2, 2:] +
        padded[1:-1, 0:-2]                      + padded[1:-1, 2:] +
        padded[2:, 0:-2]   + padded[2:, 1:-1]   + padded[2:, 2:]
    )
    survive = grid & ((neighbors == 2) | (neighbors == 3))
    born = (~grid) & (neighbors == 3)
    return survive | born

def box_blur(arr, radius):
    if radius <= 0:
        return arr
    padded = np.pad(arr, ((radius, radius), (0, 0)), mode="constant")
    cumsum = np.cumsum(padded, axis=0)
    window = cumsum[2 * radius:] - cumsum[:-2 * radius]
    blurred_v = window / (2 * radius)
    padded = np.pad(blurred_v, ((0, 0), (radius, radius)), mode="constant")
    cumsum = np.cumsum(padded, axis=1)
    window = cumsum[:, 2 * radius:] - cumsum[:, :-2 * radius]
    blurred = window / (2 * radius)
    return blurred

def compose_frame(alive, age):
    age_norm = np.clip(age, 0, AGE_CAP) / AGE_CAP
    brightness = MIN_BRIGHTNESS + (1.0 - MIN_BRIGHTNESS) * age_norm
    cell_rgb = CELL_COLOR.reshape(1, 1, 3) * brightness[:, :, None]

    glow = box_blur(alive.astype(np.float64), GLOW_RADIUS)
    glow = np.clip(glow, 0.0, 1.0)

    frame = BACKGROUND_COLOR.reshape(1, 1, 3) * (1.0 - glow[:, :, None] * GLOW_STRENGTH)
    frame = frame + GLOW_COLOR.reshape(1, 1, 3) * glow[:, :, None] * GLOW_STRENGTH
    frame = np.clip(frame, 0.0, 1.0)

    frame[alive] = cell_rgb[alive]
    return frame

def main():
    ffmpeg_path = shutil.which("ffmpeg")
    if ffmpeg_path:
        matplotlib.rcParams["animation.ffmpeg_path"] = ffmpeg_path

    grid = build_mandala(GRID_H, GRID_W)
    age = np.zeros((GRID_H, GRID_W), dtype=np.float64)
    age[grid] = 1.0

    dpi = 100
    fig = plt.figure(figsize=(WIDTH / dpi, HEIGHT / dpi), dpi=dpi)
    fig.patch.set_facecolor(tuple(BACKGROUND_COLOR))
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_facecolor(tuple(BACKGROUND_COLOR))

    cx = GRID_W / 2.0
    cy = GRID_H / 2.0
    max_r = MAX_RADIUS_FACTOR * min(GRID_H, GRID_W) / 2.0
    half_h = max_r * ZOOM_MARGIN
    half_w = half_h * (GRID_W / GRID_H)
    ax.set_xlim(cx - half_w, cx + half_w)
    ax.set_ylim(cy + half_h, cy - half_h)
    ax.axis("off")

    initial_frame = compose_frame(grid, age)
    im = ax.imshow(initial_frame, interpolation="bilinear", origin="upper", extent=[0, GRID_W, GRID_H, 0], animated=True)

    state = {"grid": grid, "age": age}

    def update(frame_idx):
        if frame_idx >= HOLD_FRAMES:
            new_grid = step_life(state["grid"])
            new_age = state["age"] + 1.0
            new_age[~new_grid] = 0.0
            state["grid"] = new_grid
            state["age"] = new_age
        composed = compose_frame(state["grid"], state["age"])
        im.set_data(composed)
        return (im,)

    anim = FuncAnimation(fig, update, frames=TOTAL_FRAMES, blit=True, interval=1000 / FPS)

    writer = FFMpegWriter(
        fps=FPS,
        codec="libx264",
        bitrate=-1,
        extra_args=["-pix_fmt", "yuv420p", "-movflags", "+faststart", "-crf", "16"],
    )
    anim.save(OUTPUT_FILENAME, writer=writer, dpi=dpi)
    plt.close(fig)

if __name__ == "__main__":
    main()
