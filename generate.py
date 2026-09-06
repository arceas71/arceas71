import numpy as np
import cv2
from scipy.integrate import solve_ivp

# Vertical Short resolution (9:16)
WIDTH, HEIGHT = 1080, 1920
FPS = 60
DURATION = 16
TOTAL_FRAMES = FPS * DURATION

PIVOT_X = WIDTH // 2
PIVOT_Y = int(HEIGHT * 0.22)   # Suspended from top-center
ROD_LEN = 1.0                  # Meters
SCALE = 700                    # Visual scale in pixels

# 3 Magnetic attractors placed near the bottom arc
MAGNET_COORDS = [
    (-0.65, 1.10),   # Left magnet
    (0.00,  1.18),   # Center magnet
    (0.65,  1.10)    # Right magnet
]

# Physical constants
G = 9.81
DAMPING = 0.08
C_MAG = 2.4
D_CLEARANCE = 0.22  # Distance above magnet plane

def pendulum_derivs(t, state):
    theta, omega = state
    
    # Gravitational restoring torque: - (g / L) * sin(theta)
    torque_grav = -(G / ROD_LEN) * np.sin(theta)
    torque_damping = -DAMPING * omega
    
    # Position of bob relative to pivot
    bx = ROD_LEN * np.sin(theta)
    by = ROD_LEN * np.cos(theta)
    
    # Magnetic torque contribution: r x F
    torque_mag = 0.0
    for mx, my in MAGNET_COORDS:
        dx = mx - bx
        dy = my - by
        dist_sq = dx*dx + dy*dy + D_CLEARANCE**2
        inv_dist3 = C_MAG / (dist_sq ** 1.5)
        
        fx = dx * inv_dist3
        fy = dy * inv_dist3
        # 2D cross product: bx * fy - by * fx
        torque_mag += (bx * fy - by * fx) / ROD_LEN
        
    d_omega = torque_grav + torque_damping + torque_mag
    return [omega, d_omega]

print("Simulating 3 magnetic pendulums under gravity...")
t_eval = np.linspace(0, DURATION, TOTAL_FRAMES)

# 3 distinct, high-angle starting positions (in radians):
# Pendulum 1: Far left (-75 deg)
# Pendulum 2: Mid right (+45 deg)
# Pendulum 3: Far right (+80 deg)
START_ANGLES = [-1.30, 0.78, 1.40]

trajectories = []
for th0 in START_ANGLES:
    sol = solve_ivp(pendulum_derivs, [0, DURATION], [th0, 0.0], t_eval=t_eval, rtol=1e-6)
    trajectories.append(sol.y[0])

# Colors (BGR)
COLORS = [
    (255, 230, 0),   # Neon Cyan
    (220, 30, 255),  # Hot Magenta
    (0, 255, 120)    # Vivid Lime
]

fourcc = cv2.VideoWriter_fourcc(*'mp4v')
out = cv2.VideoWriter('short_chaos.mp4', fourcc, FPS, (WIDTH, HEIGHT))

canvas = np.zeros((HEIGHT, WIDTH, 3), dtype=np.uint8)
prev_pts = [None] * 3

print("Rendering video...")
for f in range(TOTAL_FRAMES):
    canvas = (canvas * 0.965).astype(np.uint8)

    # Draw bottom magnetic attractors
    for mx, my in MAGNET_COORDS:
        px = PIVOT_X + int(mx * SCALE)
        py = PIVOT_Y + int(my * SCALE)
        cv2.circle(canvas, (px, py), 22, (40, 40, 40), -1)
        cv2.circle(canvas, (px, py), 28, (140, 140, 140), 2, cv2.LINE_AA)

    current_pts = []
    for i in range(3):
        th = trajectories[i][f]
        bx = PIVOT_X + int(ROD_LEN * np.sin(th) * SCALE)
        by = PIVOT_Y + int(ROD_LEN * np.cos(th) * SCALE)
        current_pts.append((bx, by))

        # Neon motion trail
        if prev_pts[i] is not None:
            cv2.line(canvas, prev_pts[i], (bx, by), COLORS[i], 4, cv2.LINE_AA)
        prev_pts[i] = (bx, by)

    frame = canvas.copy()

    # Draw central top mount
    cv2.circle(frame, (PIVOT_X, PIVOT_Y), 10, (220, 220, 220), -1)

    # Draw swinging arms and illuminated bobs
    for i in range(3):
        bx, by = current_pts[i]
        # Rigid rod
        cv2.line(frame, (PIVOT_X, PIVOT_Y), (bx, by), (160, 160, 160), 2, cv2.LINE_AA)
        # Glow edge
        cv2.circle(frame, (bx, by), 15, COLORS[i], -1, cv2.LINE_AA)
        # Core head
        cv2.circle(frame, (bx, by), 7, (255, 255, 255), -1, cv2.LINE_AA)

    out.write(frame)

out.release()
print("Render complete.")
