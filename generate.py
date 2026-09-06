import numpy as np
import cv2
from scipy.integrate import solve_ivp

# --- Video settings (9:16 Vertical Short) ---
WIDTH, HEIGHT = 1080, 1920
FPS = 60
DURATION = 15  # seconds
TOTAL_FRAMES = FPS * DURATION

# --- Customization Controls ---
N_PENDULUMS = 45          # Fewer pendulums for a cleaner, readable look
SPEED_FACTOR = 0.5        # < 1.0 slows down time (0.5 = half speed)
TRAIL_FADE = 0.955        # Higher = longer glowing trail persistence

# Physics constants
G = 9.81
L1, L2 = 1.0, 1.0
M1, M2 = 1.0, 1.0

# Pivot & Scaling (Calibrated so arms NEVER leave the 1080x1920 screen)
# Max reach is (L1 + L2) * scale = 2.0 * 220 = 440 px from center (safely within 540 px width)
scale = 220
center_x = WIDTH // 2
center_y = int(HEIGHT * 0.48)

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

    # Slow down time by scaling angular velocity derivatives
    return [w1 * SPEED_FACTOR, dw1_dt * SPEED_FACTOR, w2 * SPEED_FACTOR, dw2_dt * SPEED_FACTOR]

print("Simulating pendulum physics...")
t_eval = np.linspace(0, DURATION, TOTAL_FRAMES)
trajectories = []

base_angle = np.pi / 2  # Horizontal start
for i in range(N_PENDULUMS):
    th1 = base_angle + (i * 0.0003)
    th2 = base_angle
    sol = solve_ivp(derivatives, [0, DURATION], [th1, 0.0, th2, 0.0], t_eval=t_eval, rtol=1e-6)
    trajectories.append(sol.y)

# Rainbow neon spectrum
colors = []
for i in range(N_PENDULUMS):
    hue = int((i / N_PENDULUMS) * 180)
    col = cv2.cvtColor(np.uint8([[[hue, 255, 255]]]), cv2.COLOR_HSV2BGR)[0][0]
    colors.append((int(col[0]), int(col[1]), int(col[2])))

print("Rendering video...")
fourcc = cv2.VideoWriter_fourcc(*'mp4v')
out = cv2.VideoWriter('short_chaos.mp4', fourcc, FPS, (WIDTH, HEIGHT))

canvas = np.zeros((HEIGHT, WIDTH, 3), dtype=np.uint8)
prev_pts = [None] * N_PENDULUMS

for f in range(TOTAL_FRAMES):
    # Fading neon trail effect
    canvas = (canvas * TRAIL_FADE).astype(np.uint8)

    # Draw anchor point
    cv2.circle(canvas, (center_x, center_y), 5, (180, 180, 180), -1)

    for i in range(N_PENDULUMS):
        th1 = trajectories[i][0][f]
        th2 = trajectories[i][2][f]

        x1 = center_x + int(L1 * np.sin(th1) * scale)
        y1 = center_y + int(L1 * np.cos(th1) * scale)
        x2 = x1 + int(L2 * np.sin(th2) * scale)
        y2 = y1 + int(L2 * np.cos(th2) * scale)

        if prev_pts[i] is not None:
            # Slightly thicker lines (thickness=3) for better visibility
            cv2.line(canvas, prev_pts[i], (x2, y2), colors[i], 3, cv2.LINE_AA)

        prev_pts[i] = (x2, y2)

    frame = canvas.copy()
    
    # Draw bright glowing heads at pendulum tips
    for i in range(N_PENDULUMS):
        if prev_pts[i] is not None:
            cv2.circle(frame, prev_pts[i], 4, (255, 255, 255), -1)

    out.write(frame)

out.release()
print("Done! Ready for FFmpeg conversion.")
