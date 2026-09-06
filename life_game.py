import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FFMpegWriter

WIDTH = 1080
HEIGHT = 1920
FPS = 30
SECONDS = 20
PARTICLES = 18000
DT = 0.018
G = 0.85

rng = np.random.default_rng(42)

x = rng.normal(0, 1.0, PARTICLES)
y = rng.normal(0, 1.0, PARTICLES)

r = np.sqrt(x * x + y * y)
angle = np.arctan2(y, x)

x *= 2.0 + r * 0.9
y *= 2.0 + r * 0.9

speed = np.sqrt(G / np.maximum(np.sqrt(x * x + y * y), 0.25))
vx = -np.sin(angle) * speed
vy = np.cos(angle) * speed

vx += rng.normal(0, 0.025, PARTICLES)
vy += rng.normal(0, 0.025, PARTICLES)

mass = np.clip(r / 5.0, 0.2, 3.0)

fig = plt.figure(figsize=(9, 16), dpi=120, facecolor="#01020a")
ax = fig.add_axes([0, 0, 1, 1], facecolor="#01020a")
ax.set_xlim(-11, 11)
ax.set_ylim(-20, 20)
ax.set_aspect("equal")
ax.axis("off")

glow_layers = [
    ax.scatter([], [], s=10, alpha=0.025, linewidths=0),
    ax.scatter([], [], s=4, alpha=0.06, linewidths=0),
    ax.scatter([], [], s=1.8, alpha=0.85, linewidths=0)
]

cmap = plt.cm.magma

writer = FFMpegWriter(
    fps=FPS,
    codec="libx264",
    bitrate=18000,
    extra_args=["-pix_fmt", "yuv420p", "-movflags", "+faststart"]
)

with writer.saving(fig, "black_hole.mp4", dpi=120):
    for frame in range(FPS * SECONDS):
        radius = np.sqrt(x * x + y * y)

        safe_radius = np.maximum(radius, 0.22)

        acceleration = G / (safe_radius * safe_radius)

        ax_force = -x / safe_radius * acceleration
        ay_force = -y / safe_radius * acceleration

        vx += ax_force * DT
        vy += ay_force * DT

        vx *= 0.9995
        vy *= 0.9995

        x += vx * DT
        y += vy * DT

        escaped = radius > 18

        if np.any(escaped):
            angle_escape = np.arctan2(y[escaped], x[escaped])
            rr = rng.uniform(8, 12, np.count_nonzero(escaped))

            x[escaped] = np.cos(angle_escape) * rr
            y[escaped] = np.sin(angle_escape) * rr

            vx[escaped] *= 0.35
            vy[escaped] *= 0.35

        distance = np.sqrt(x * x + y * y)

        colors = cmap(
            np.clip(
                1.0 - distance / 13.0 + np.sin(frame * 0.03 + distance) * 0.08,
                0,
                1
            )
        )

        order = np.argsort(distance)

        px = x[order]
        py = y[order]
        pc = colors[order]

        glow_layers[0].set_offsets(np.column_stack((px, py)))
        glow_layers[0].set_color(pc)

        glow_layers[1].set_offsets(np.column_stack((px, py)))
        glow_layers[1].set_color(pc)

        glow_layers[2].set_offsets(np.column_stack((px, py)))
        glow_layers[2].set_color(pc)

        writer.grab_frame()

plt.close(fig)
