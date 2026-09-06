import numpy as np
import cv2

WIDTH, HEIGHT = 1080, 1920
FPS = 60
MAX_DURATION = 45.0
MAX_FRAMES = int(FPS * MAX_DURATION)

CX, CY = WIDTH // 2, HEIGHT // 2
CORE_RADIUS = 65.0
SHIELD_RADIUS = 280.0
SHIELD_GAP_DEG = 40.0
SHIELD_GAP_RAD = np.radians(SHIELD_GAP_DEG)

NUM_PARTICLES = 65
GRAVITY = 650.0
RESTITUTION = 0.88
ROT_SPEED = 2.2

# Particle initialization
np.random.seed(42)
pos = np.zeros((NUM_PARTICLES, 2), dtype=np.float64)
vel = np.zeros((NUM_PARTICLES, 2), dtype=np.float64)

for i in range(NUM_PARTICLES):
    pos[i] = [CX + np.random.uniform(-300, 300), np.random.uniform(80, 400)]
    vel[i] = [np.random.uniform(-80, 80), np.random.uniform(20, 150)]

colors = []
for i in range(NUM_PARTICLES):
    hue = int((i / NUM_PARTICLES) * 180)
    col = cv2.cvtColor(np.uint8([[[hue, 240, 255]]]), cv2.COLOR_HSV2BGR)[0][0]
    colors.append((int(col[0]), int(col[1]), int(col[2])))

# Output directly as circle_escape.mp4 so your existing YAML workflow detects and transcodes it
fourcc = cv2.VideoWriter_fourcc(*'mp4v')
out = cv2.VideoWriter('circle_escape.mp4', fourcc, FPS, (WIDTH, HEIGHT))

canvas = np.zeros((HEIGHT, WIDTH, 3), dtype=np.uint8)
prev_pts = [None] * NUM_PARTICLES
shockwaves = []  # [x, y, radius, max_radius, color]

shield_angle = 0.0
absorbed_count = 0
frame_idx = 0
dt = 1.0 / FPS

print("Simulating Swarm vs Core...")

while frame_idx < MAX_FRAMES:
    shield_angle = (shield_angle + ROT_SPEED * dt) % (2 * np.pi)
    gap_start = (shield_angle - SHIELD_GAP_RAD / 2.0) % (2 * np.pi)
    gap_end = (shield_angle + SHIELD_GAP_RAD / 2.0) % (2 * np.pi)

    # Physics updates
    for i in range(NUM_PARTICLES):
        vel[i, 1] += GRAVITY * dt
        pos[i] += vel[i] * dt

        dx = pos[i, 0] - CX
        dy = pos[i, 1] - CY
        dist = np.hypot(dx, dy)

        # 1. Outer screen boundary rebounds
        if pos[i, 0] < 40 or pos[i, 0] > WIDTH - 40:
            vel[i, 0] *= -0.85
            pos[i, 0] = np.clip(pos[i, 0], 41, WIDTH - 41)
        if pos[i, 1] > HEIGHT - 60:
            vel[i, 1] *= -0.80
            pos[i, 1] = HEIGHT - 61

        # 2. Rotating shield collision
        if abs(dist - SHIELD_RADIUS) < 14.0:
            angle = np.arctan2(dy, dx) % (2 * np.pi)
            in_gap = (gap_start <= angle <= gap_end) if gap_start < gap_end else (angle >= gap_start or angle <= gap_end)
            
            if not in_gap:
                norm = np.array([dx / dist, dy / dist])
                vel[i] = (vel[i] - 2.0 * np.dot(vel[i], norm) * norm) * RESTITUTION
                pos[i] = np.array([CX, CY]) + norm * (SHIELD_RADIUS + (15.0 if dist > SHIELD_RADIUS else -15.0))
                shockwaves.append([int(pos[i, 0]), int(pos[i, 1]), 6, 45, (255, 255, 255)])

        # 3. Core impact & absorption
        if dist <= CORE_RADIUS + 10.0:
            absorbed_count += 1
            shockwaves.append([CX, CY, 10, 160, colors[i]])
            pos[i] = [CX + np.random.uniform(-250, 250), np.random.uniform(50, 180)]
            vel[i] = [np.random.uniform(-100, 100), np.random.uniform(50, 200)]
            prev_pts[i] = None

    # Render frame
    canvas = (canvas * 0.91).astype(np.uint8)

    for i in range(NUM_PARTICLES):
        px, py = int(pos[i, 0]), int(pos[i, 1])
        if 0 <= px < WIDTH and 0 <= py < HEIGHT:
            if prev_pts[i] is not None:
                cv2.line(canvas, prev_pts[i], (px, py), colors[i], 3, cv2.LINE_AA)
            prev_pts[i] = (px, py)

    frame = canvas.copy()

    # Draw shockwaves
    active_shocks = []
    for sw in shockwaves:
        x, y, r, max_r, col = sw
        if r < max_r:
            cv2.circle(frame, (x, y), int(r), col, 2, cv2.LINE_AA)
            active_shocks.append([x, y, r + 4, max_r, col])
    shockwaves = active_shocks

    # Draw rotating shield
    gap_deg = np.degrees(shield_angle) % 360
    cv2.ellipse(frame, (CX, CY), (int(SHIELD_RADIUS), int(SHIELD_RADIUS)),
                0, gap_deg + SHIELD_GAP_DEG / 2, gap_deg + 360 - SHIELD_GAP_DEG / 2,
                (255, 255, 255), 12, cv2.LINE_AA)

    # Draw central pulsing core
    pulse = int(6 * np.sin(frame_idx * 0.15))
    cv2.circle(frame, (CX, CY), int(CORE_RADIUS + pulse), (0, 165, 255), -1, cv2.LINE_AA)
    cv2.circle(frame, (CX, CY), int((CORE_RADIUS + pulse) * 0.5), (255, 255, 255), -1, cv2.LINE_AA)

    # Draw particles
    for i in range(NUM_PARTICLES):
        px, py = int(pos[i, 0]), int(pos[i, 1])
        if 0 <= px < WIDTH and 0 <= py < HEIGHT:
            cv2.circle(frame, (px, py), 9, colors[i], -1, cv2.LINE_AA)

    # HUD counter
    cv2.putText(frame, f"BREACHES: {absorbed_count}", (CX - 160, CY - 400),
                cv2.FONT_HERSHEY_DUPLEX, 1.2, (255, 255, 255), 2, cv2.LINE_AA)

    out.write(frame)
    frame_idx += 1

out.release()
print("Simulation complete!")
