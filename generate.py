import numpy as np
import cv2
from scipy.integrate import solve_ivp

# Vertical resolution for YouTube Shorts (9:16)
WIDTH, HEIGHT = 1080, 1920
FPS = 60
DURATION = 16
TOTAL_FRAMES = FPS * DURATION

CX = WIDTH // 2
CY = HEIGHT // 2
SCALE = 420

# 3 Magnetic Attractors arranged in an equilateral triangle
MAG_ANGLES = np.array([0, 2 * np.pi / 3, 4 * np.pi / 3]) - np.pi / 2
R_MAG = 1.05
magnets = np.column_stack([R_MAG * np.cos(MAG_ANGLES), R_MAG * np.sin(MAG_ANGLES)])

# Physical parameters
DAMPING = 0.12
GRAV = 0.50
C_MAG = 1.75
D = 0.28  # Vertical clearance above magnet plane

def equations(t, state):
    x, vx, y, vy = state
    fx = -GRAV * x - DAMPING * vx
    fy = -GRAV * y - DAMPING * vy
    for mx, my in magnets:
        dx = mx - x
        dy = my - y
        dist_sq = dx*dx + dy*dy + D*D
        fx += dx * (C_MAG / (dist_sq ** 1.5))
        fy += dy * (C_MAG / (dist_sq ** 1.5))
    return [vx, fx, vy, fy]

print("Simulating 3 distinct magnetic pendulums...")
t_eval = np.linspace(0, DURATION, TOTAL_FRAMES)

# 3 Pendulums: Cyan, Magenta, Lime (BGR format)
PENDULUM_COLORS = [
    (255, 230, 0),   # Neon Cyan
    (200, 30, 255),  # Hot Magenta
    (50, 255, 120)   # Vivid Lime
]

# 3 distinct, high-angle starting positions (120 degrees apart)
START_ANGLES = [np.pi / 6, 5 * np.pi / 6, 3 * np.pi / 2]
R_START = 1.25

trajectories = []
for ang in START_ANGLES:
    x0 = R_START * np.cos(ang)
    y0 = R_START * np.sin(ang)
    vx0 = -0.45 * np.sin(ang)
    vy0 = 0.45 * np.cos(ang)
    sol = solve_ivp(equations, [0, DURATION], [x0, vx0, y0, vy0], t_eval=t_eval, rtol=1e-5)
    trajectories.append((sol.y[0], sol.y[2]))

# Rendering setup
fourcc = cv2.VideoWriter_fourcc(*'mp4v')
out = cv2.VideoWriter('short_chaos.mp4', fourcc, FPS, (WIDTH, HEIGHT))

canvas = np.zeros((HEIGHT, WIDTH, 3), dtype=np.uint8)
prev_pts = [None] * 3

print("Rendering frames...")
for f in range(TOTAL_FRAMES):
    # Smooth trail decay
    canvas = (canvas * 0.972).astype(np.uint8)

    # Draw the fixed magnetic attractor basins
    for mx, my in magnets:
        px = CX + int(mx * SCALE)
        py = CY + int(my * SCALE)
        cv2.circle(canvas, (px, py), 18, (45, 45, 45), -1)
        cv2.circle(canvas, (px, py), 26, (120, 120, 120), 2, cv2.LINE_AA)

    current_pts = []
    for i in range(3):
        x = trajectories[i][0][f]
        y = trajectories[i][1][f]
        px = CX + int(x * SCALE)
        py = CY + int(y * SCALE)
        current_pts.append((px, py))

        # Render neon ribbon trails
        if prev_pts[i] is not None:
            cv2.line(canvas, prev_pts[i], (px, py), PENDULUM_COLORS[i], 4, cv2.LINE_AA)
        prev_pts[i] = (px, py)

    frame = canvas.copy()

    # Draw center anchor point
    cv2.circle(frame, (CX, CY), 8, (200, 200, 200), -1)

    # Draw mechanical suspension arms and illuminated bobs
    for i in range(3):
        px, py = current_pts[i]
        # Semi-transparent pendulum cord
        cv2.line(frame, (CX, CY), (px, py), (110, 110, 110), 2, cv2.LINE_AA)
        # Colored outer glow
        cv2.circle(frame, (px, py), 14, PENDULUM_COLORS[i], -1, cv2.LINE_AA)
        # White hot center
        cv2.circle(frame, (px, py), 7, (255, 255, 255), -1, cv2.LINE_AA)

    out.write(frame)

out.release()
print("Rendering complete.")
