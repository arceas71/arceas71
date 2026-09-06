import os, textwrap, zipfile, math, random, subprocess, sys, shutil
from pathlib import Path

root = Path("/mnt/data/magnet_simulation")
root.mkdir(exist_ok=True)

script = r'''import math
import random
from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FFMpegWriter

# =========================
# 100-Magnet Physics Video
# =========================
N = 100
FPS = 60
SECONDS = 10
WIDTH, HEIGHT = 12.0, 7.0

random.seed(7)
np.random.seed(7)

# Physics tuning
DT = 0.018
SOFTENING = 0.18
MAGNET_STRENGTH = 0.90
ROTATION_STRENGTH = 0.045
DAMPING = 0.985
MAX_SPEED = 5.0

# Each magnet has position, velocity and orientation.
pos = np.column_stack([
    np.random.uniform(1.0, WIDTH - 1.0, N),
    np.random.uniform(0.8, HEIGHT - 0.8, N)
])
vel = np.random.normal(0, 0.35, (N, 2))
angle = np.random.uniform(0, 2 * np.pi, N)

def step():
    global pos, vel, angle

    force = np.zeros_like(pos)
    torque = np.zeros(N)

    # Pairwise magnetic interaction.
    for i in range(N):
        for j in range(i + 1, N):
            d = pos[j] - pos[i]
            r2 = float(np.dot(d, d)) + SOFTENING**2
            r = math.sqrt(r2)
            u = d / r

            # Simple dipole-like interaction:
            # nearby magnets strongly influence one another.
            ai = angle[i]
            aj = angle[j]
            mi = np.array([math.cos(ai), math.sin(ai)])
            mj = np.array([math.cos(aj), math.sin(aj)])

            alignment = float(np.dot(mi, mj))
            facing = float(np.dot(mi, u) * np.dot(mj, u))

            # Attractive/repulsive radial component.
            scalar = MAGNET_STRENGTH * (0.65 * alignment - 1.15 * facing) / r2
            fij = scalar * u

            force[i] += fij
            force[j] -= fij

            # Rotate magnets toward energetically favorable alignment.
            cross_ij = mi[0] * mj[1] - mi[1] * mj[0]
            torque[i] += ROTATION_STRENGTH * cross_ij / r2
            torque[j] -= ROTATION_STRENGTH * cross_ij / r2

    # Soft boundary force keeps the swarm on screen.
    margin = 0.55
    wall_k = 1.4
    for axis, limit in [(0, WIDTH), (1, HEIGHT)]:
        force[:, axis] += np.where(
            pos[:, axis] < margin,
            wall_k * (margin - pos[:, axis]),
            0
        )
        force[:, axis] -= np.where(
            pos[:, axis] > limit - margin,
            wall_k * (pos[:, axis] - (limit - margin)),
            0
        )

    vel += force * DT
    speed = np.linalg.norm(vel, axis=1)
    too_fast = speed > MAX_SPEED
    vel[too_fast] *= (MAX_SPEED / speed[too_fast])[:, None]
    vel *= DAMPING

    pos += vel * DT
    angle += torque * DT

    # Small amount of angular damping.
    angle %= 2 * np.pi

def make_video(output="100_magnets.mp4"):
    fig, ax = plt.subplots(figsize=(WIDTH, HEIGHT), dpi=100)
    fig.patch.set_facecolor("#07090d")
    ax.set_facecolor("#07090d")
    ax.set_xlim(0, WIDTH)
    ax.set_ylim(0, HEIGHT)
    ax.set_aspect("equal")
    ax.axis("off")

    # Glow-like layers.
    glow = ax.scatter(pos[:, 0], pos[:, 1], s=110, alpha=0.10, linewidths=0)
    dots = ax.scatter(pos[:, 0], pos[:, 1], s=38, alpha=0.95, linewidths=0)

    # Orientation lines.
    lines = [ax.plot([], [], lw=1.4, alpha=0.95)[0] for _ in range(N)]

    title = ax.text(
        0.035, 0.94, "100 MAGNETS",
        transform=ax.transAxes,
        fontsize=18, fontweight="bold",
        color="white", va="top"
    )
    subtitle = ax.text(
        0.035, 0.885, "released simultaneously",
        transform=ax.transAxes,
        fontsize=10, color="#b9c0cc", va="top"
    )

    # Use the installed ffmpeg executable.
    writer = FFMpegWriter(
        fps=FPS,
        metadata={"title": "100 Magnets Simulation"},
        bitrate=7000,
        codec="libx264",
        extra_args=["-pix_fmt", "yuv420p", "-movflags", "+faststart"]
    )

    with writer.saving(fig, output, dpi=100):
        for frame in range(FPS * SECONDS):
            # A tiny jitter makes the final state feel alive without exploding.
            if frame > FPS * 2:
                vel += np.random.normal(0, 0.006, vel.shape)

            step()

            glow.set_offsets(pos)
            dots.set_offsets(pos)

            # Give each magnet a two-pole look.
            for i, line in enumerate(lines):
                dx = 0.16 * math.cos(angle[i])
                dy = 0.16 * math.sin(angle[i])
                line.set_data(
                    [pos[i, 0] - dx, pos[i, 0] + dx],
                    [pos[i, 1] - dy, pos[i, 1] + dy]
                )

            writer.grab_frame()

    plt.close(fig)
    print(f"Saved: {Path(output).resolve()}")

if __name__ == "__main__":
    make_video()
'''

req = """numpy
matplotlib
"""

readme = r'''# 100 Magnets Simulation

Generates a 10-second, 60 FPS MP4 of 100 magnets interacting in a 2D physics-style simulation.

## Requirements

- Python 3.10+
- FFmpeg installed and available on PATH

Install Python packages:

```bash
pip install -r requirements.txt
