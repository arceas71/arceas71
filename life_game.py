import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FFMpegWriter
from scipy.ndimage import gaussian_filter

W = 540
H = 960
FPS = 30
SECONDS = 24
N = 28000
G = 3.8
DT = 0.012

rng = np.random.default_rng(19)

y, x = np.mgrid[0:H, 0:W]
cx = W / 2
cy = H / 2

px = rng.uniform(-10.5, 10.5, N)
py = rng.uniform(-18, 18, N)

radius = np.sqrt(px * px + py * py)
radius = np.clip(radius, 2.5, 17.5)

angle = rng.uniform(0, np.pi * 2, N)

px = np.cos(angle) * radius
py = np.sin(angle) * radius

radial = rng.normal(0, 0.08, N)
orbital = np.sqrt(G / radius)

vx = -np.sin(angle) * orbital + np.cos(angle) * radial
vy = np.cos(angle) * orbital + np.sin(angle) * radial

vx *= 1.25
vy *= 1.25

alive = np.ones(N, dtype=bool)

fig = plt.figure(figsize=(9, 16), dpi=120, facecolor="#020208")
ax = fig.add_axes([0, 0, 1, 1], facecolor="#020208")
ax.set_xlim(-11, 11)
ax.set_ylim(-20, 20)
ax.set_aspect("equal")
ax.axis("off")

disk = ax.imshow(
    np.zeros((H, W)),
    extent=(-11, 11, -20, 20),
    cmap="inferno",
    vmin=0,
    vmax=1,
    interpolation="bicubic"
)

particles = ax.scatter(
    [], [],
    s=1.2,
    linewidths=0,
    alpha=0.9
)

writer = FFMpegWriter(
    fps=FPS,
    codec="libx264",
    bitrate=18000,
    extra_args=["-pix_fmt", "yuv420p", "-movflags", "+faststart"]
)

with writer.saving(fig, "black_hole.mp4", dpi=120):

    for frame in range(FPS * SECONDS):

        r = np.sqrt(px * px + py * py)
        theta = np.arctan2(py, px)

        r_safe = np.maximum(r, 0.35)

        gravity = G / (r_safe * r_safe)

        ax_force = -px / r_safe * gravity
        ay_force = -py / r_safe * gravity

        drag = 0.0025 / np.maximum(r_safe, 0.5)

        vx += ax_force * DT
        vy += ay_force * DT

        vx *= 1 - drag
        vy *= 1 - drag

        angular = 0.018 / np.maximum(r_safe, 0.5)

        vx += -np.sin(theta) * angular
        vy += np.cos(theta) * angular

        px += vx * DT
        py += vy * DT

        swallowed = r < 0.48

        alive[swallowed] = False

        px[swallowed] = np.nan
        py[swallowed] = np.nan
        vx[swallowed] = 0
        vy[swallowed] = 0

        r = np.sqrt(px * px + py * py)

        escaping = alive & (r > 19)

        alive[escaping] = False

        px[escaping] = np.nan
        py[escaping] = np.nan

        finite = np.isfinite(px) & np.isfinite(py)

        pxv = px[finite]
        pyv = py[finite]

        density = np.zeros((H, W), dtype=np.float32)

        if len(pxv):

            ix = ((pxv + 11) / 22 * (W - 1)).astype(np.int32)
            iy = ((pyv + 20) / 40 * (H - 1)).astype(np.int32)

            valid = (
                (ix >= 0) &
                (ix < W) &
                (iy >= 0) &
                (iy < H)
            )

            ix = ix[valid]
            iy = iy[valid]

            np.add.at(density, (iy, ix), 1)

        density = gaussian_filter(density, sigma=2.4)

        if np.max(density) > 0:
            density /= np.percentile(density[density > 0], 99.2)
            density = np.clip(density, 0, 1)

        inner = np.exp(
            -((x - cx) ** 2 + (y - cy) ** 2) /
            (2 * (H * 0.035) ** 2)
        )

        disk_frame = np.maximum(density, inner * 0.42)

        disk.set_data(disk_frame)

        if len(pxv):

            particle_r = np.sqrt(pxv * pxv + pyv * pyv)

            heat = np.clip(
                1.2 - particle_r / 15,
                0,
                1
            )

            colors = plt.cm.inferno(heat)

            particles.set_offsets(
                np.column_stack((pxv, pyv))
            )

            particles.set_color(colors)

            sizes = (
                0.5 +
                1.8 * heat +
                1.2 * np.exp(-particle_r / 3)
            )

            particles.set_sizes(sizes)

        writer.grab_frame()

plt.close(fig)
