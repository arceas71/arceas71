import numpy as np
import cv2
from scipy.integrate import solve_ivp

# Vertical Short resolution (9:16)
WIDTH, HEIGHT = 1080, 1920
FPS = 60
DURATION = 16
TOTAL_FRAMES = FPS * DURATION

N_TRAJECTORIES = 36
TRAIL_FADE = 0.965

# Screen center & coordinates
CX = WIDTH // 2
CY = HEIGHT // 2
SCALE = 380

# 3 Magnetic attractors in an equilateral triangle
angles = np.array([0, 2 * np.pi / 3, 4 * np.pi / 3]) - np.pi / 2
R_MAG = 1.05
magnets = np.column_stack([R_MAG * np.cos(angles), R_MAG * np.sin(angles)])
# Distinct neon colors for the 3 magnets (BGR)
MAG_COLORS = [(255, 220, 0), (220, 20, 255), (0, 255, 255)]

# Physical parameters: damping, gravity return, magnetic strength, magnet height
DAMPING = 0.18
GRAV = 0.45
C_MAG = 1.6
D = 0.28  # vertical distance to magnet plane

def equations(t, state):
    # state: [x, vx, y, vy]
    x, vx, y, vy = state
    
    # Restoring spring/gravity force towards center
    fx = -GRAV * x - DAMPING * vx
    fy = -GRAV * y - DAMPING * vy
    
    # Add pull from all 3 magnets: F = C * (r_mag - r) / (dist^2 + d^2)^(3/2)
    for mx, my in magnets:
        dx = mx - x
        dy = my - y
        dist_sq = dx*dx + dy*dy + D*D
        inv_dist3 = C_MAG / (dist_sq ** 1.5)
        fx += dx * inv_dist3
        fy += dy * inv_dist3
        
    return [vx, fx, vy, fy]

print("Simulating 36 high-angle magnetic chaos paths...")
t_eval = np.linspace(0, DURATION, TOTAL_FRAMES)
trajectories = []

# Wide angle variation: initial positions arranged in a radial circle
start_radius = 1.15
for i in range(N_TRAJECTORIES):
    theta = (i / N_TRAJECTORIES) * 2 * np.pi
    x0 = start_radius * np.cos(theta)
    y0 = start_radius * np.sin(theta)
    
    # Slight initial tangential velocity for swirling entry
    vx0 = -0.3 * np.sin(theta)
    vy0 = 0.3 * np.cos(theta)
    
    sol = solve_ivp(equations, [0, DURATION], [x0, vx0, y0, vy0], t_eval=t_eval, rtol=1e-5)
    trajectories.append((sol.y[0], sol.y[2]))

# Render setup
fourcc = cv2.VideoWriter_fourcc(*'mp4v')
out = cv2.VideoWriter('short_chaos.mp4', fourcc, FPS, (WIDTH, HEIGHT))

canvas = np.zeros((HEIGHT, WIDTH, 3), dtype=np.uint8)
prev_pts = [None] * N_TRAJECTORIES

print("Rendering magnetic fractal animation...")
for f in range(TOTAL_FRAMES):
    canvas = (canvas * TRAIL_FADE).astype(np.uint8)

    # Draw the 3 glowing magnetic anchor poles
    for idx, (mx, my) in enumerate(magnets):
        px = CX + int(mx * SCALE)
        py = CY + int(my * SCALE)
        cv2.circle(canvas, (px, py), 16, MAG_COLORS[idx], -1)
        cv2.circle(canvas, (px, py), 26, (255, 255, 255), 2, cv2.LINE_AA)

    # Draw trajectories and calculate dynamic color based on closest attractor
    for i in range(N_TRAJECTORIES):
        x = trajectories[i][0][f]
        y = trajectories[i][1][f]
        
        px = CX + int(x * SCALE)
        py = CY + int(y * SCALE)
        
        # Determine color based on closest magnet
        dists = [np.hypot(x - mx, y - my) for mx, my in magnets]
        closest = int(np.argmin(dists))
        color = MAG_COLORS[closest]

        if prev_pts[i] is not None:
            cv2.line(canvas, prev_pts[i], (px, py), color, 3, cv2.LINE_AA)

        prev_pts[i] = (px, py)

    frame = canvas.copy()

    # Draw white glowing heads on moving pendulum bobs
    for i in range(N_TRAJECTORIES):
        if prev_pts[i] is not None:
            cv2.circle(frame, prev_pts[i], 5, (255, 255, 255), -1)

    out.write(frame)

out.release()
print("Done! Ready for GitHub workflow.")
