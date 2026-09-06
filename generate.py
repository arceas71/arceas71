import numpy as np
import cv2
from scipy.integrate import solve_ivp

# Video settings (9:16 aspect ratio for YouTube Shorts)
WIDTH, HEIGHT = 1080, 1920
FPS = 60
DURATION = 15  # seconds
TOTAL_FRAMES = FPS * DURATION
N_PENDULUMS = 150

# Physics constants
G = 9.81
L1, L2 = 1.0, 1.0
M1, M2 = 1.0, 1.0

def derivatives(t, y):
    th1, w1, th2, w2 = y
    delta = th1 - th2

    den1 = L1 * (2 * M1 + M2 - M2 * np.cos(2 * th1 - 2 * th2))
    num1 = -G * (2 * M1 + M2) * np.sin(th1) - M2 * G * np.sin(th1 - 2 * th2) \
           - 2 * np.sin(delta) * M2 * (w2**2 * L2 + w1**2 * L1 * np.cos(delta))
    dw1_dt = num1 / den1

    den2 = L2 * (2 * M1 + M2 - M2 * np.cos(2 * th1 - 2 * th2))
    num2 = 2 * np.sin(delta) * (w1**2 * L1 * (M1 + M2) + G * (M1 + M2) * np.cos(th1) \
           + w2**2 * L2 * M2 * np.cos(delta))
    dw2_dt = num2 / den2

    return [w1, dw1_dt, w2, dw2_dt]

print("Simulating physics trajectories...")
t_eval = np.linspace(0, DURATION, TOTAL_FRAMES)
trajectories = []

base_angle = np.pi / 2
for i in range(N_PENDULUMS):
    th1 = base_angle + (i * 0.0001)
    th2 = base_angle
    sol = solve_ivp(derivatives, [0, DURATION], [th1, 0.0, th2, 0.0], t_eval=t_eval, rtol=1e-6)
    trajectories.append(sol.y)

# Color palettes (rainbow spectrum across pendulums in BGR)
colors = []
for i in range(N_PENDULUMS):
    hue = int((i / N_PENDULUMS) * 180)
    col = cv2.cvtColor(np.uint8([[[hue, 255, 255]]]), cv2.COLOR_HSV2BGR)[0][0]
    colors.append((int(col[0]), int(col[1]), int(col[2])))

print("Rendering video to short_chaos.mp4...")
fourcc = cv2.VideoWriter_fourcc(*'mp4v')
out = cv2.VideoWriter('short_chaos.mp4', fourcc, FPS, (WIDTH, HEIGHT))

canvas = np.zeros((HEIGHT, WIDTH, 3), dtype=np.uint8)
center_x = WIDTH // 2
center_y = int(HEIGHT * 0.38)
scale = 360  # Pixel scale

prev_pts = [None] * N_PENDULUMS

for f in range(TOTAL_FRAMES):
    # Trail fade: slowly dim previous frames to create neon trails
    canvas = (canvas * 0.94).astype(np.uint8)

    for i in range(N_PENDULUMS):
        th1 = trajectories[i][0][f]
        th2 = trajectories[i][2][f]

        x1 = center_x + int(L1 * np.sin(th1) * scale)
        y1 = center_y + int(L1 * np.cos(th1) * scale)
        x2 = x1 + int(L2 * np.sin(th2) * scale)
        y2 = y1 + int(L2 * np.cos(th2) * scale)

        if prev_pts[i] is not None:
            cv2.line(canvas, prev_pts[i], (x2, y2), colors[i], 2, cv2.LINE_AA)

        prev_pts[i] = (x2, y2)

    # Frame display copy to draw the active pendulum heads
    frame = canvas.copy()
    for i in range(0, N_PENDULUMS, 3):
        if prev_pts[i] is not None:
            cv2.circle(frame, prev_pts[i], 3, (255, 255, 255), -1)

    out.write(frame)
    if f % (FPS * 2) == 0:
        print(f"Rendered {f // FPS}s / {DURATION}s")

out.release()
print("Done! Exported short_chaos.mp4")
