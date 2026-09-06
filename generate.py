import numpy as np
import cv2

# --- Video Configuration (9:16 YouTube Shorts) ---
WIDTH, HEIGHT = 1080, 1920
FPS = 60
MAX_DURATION = 58.0          # Max duration in seconds (< 59s)
MAX_FRAMES = int(FPS * MAX_DURATION)

# Center and dimensions
CX = WIDTH // 2
CY = HEIGHT // 2
CIRCLE_RADIUS = 360.0
GAP_ANGLE_DEG = 10.0         # 10 degree opening
GAP_RAD = np.radians(GAP_ANGLE_DEG)
CIRCLE_THICKNESS = 14

# --- Ball Configuration ---
NUM_BALLS = 50
BALL_RADIUS = 10.0
RESTITUTION = 0.99           # Elasticity of bounce
ROT_SPEED = 1.35             # Radians per second of circle rotation

# Particle states
np.random.seed(42)
angles = np.random.uniform(0, 2 * np.pi, NUM_BALLS)
speeds = np.random.uniform(280.0, 460.0, NUM_BALLS)

# Position, velocity, and status
pos = np.zeros((NUM_BALLS, 2), dtype=np.float64)
pos[:, 0] = CX + np.random.uniform(-15, 15, NUM_BALLS)
pos[:, 1] = CY + np.random.uniform(-15, 15, NUM_BALLS)

vel = np.zeros((NUM_BALLS, 2), dtype=np.float64)
vel[:, 0] = speeds * np.cos(angles)
vel[:, 1] = speeds * np.sin(angles)

escaped = np.zeros(NUM_BALLS, dtype=bool)

# Distinct vibrant neon colors for balls (BGR)
colors = []
for i in range(NUM_BALLS):
    hue = int((i / NUM_BALLS) * 180)
    col = cv2.cvtColor(np.uint8([[[hue, 240, 255]]]), cv2.COLOR_HSV2BGR)[0][0]
    colors.append((int(col[0]), int(col[1]), int(col[2])))

# Setup Video Writer
fourcc = cv2.VideoWriter_fourcc(*'mp4v')
out = cv2.VideoWriter('circle_escape.mp4', fourcc, FPS, (WIDTH, HEIGHT))

print("Simulating and rendering physics animation...")

circle_angle = 0.0
frame_idx = 0
dt_base = 1.0 / FPS

while frame_idx < MAX_FRAMES:
    current_time = frame_idx / FPS
    remaining_inside = np.sum(~escaped)

    # If all escaped, add a 1.5s outro and break
    if remaining_inside == 0:
        for _ in range(int(FPS * 1.5)):
            if frame_idx >= MAX_FRAMES:
                break
            # Render final lingering frames
            frame = np.zeros((HEIGHT, WIDTH, 3), dtype=np.uint8)
            cv2.putText(frame, "ALL ESCAPED!", (CX - 220, CY - 420),
                        cv2.FONT_HERSHEY_DUPLEX, 1.3, (0, 255, 180), 2, cv2.LINE_AA)
            out.write(frame)
            frame_idx += 1
        break

    # Dynamic speed-up factor: speeds up if time > 40s to guarantee finishing < 59s
    if current_time > 40.0:
        speed_mult = 1.0 + ((current_time - 40.0) / 10.0) ** 2.5 * (remaining_inside / 10.0)
    else:
        speed_mult = 1.0

    # Sub-stepping for stable collision resolution
    substeps = max(8, int(8 * min(speed_mult, 10.0)))
    sub_dt = (dt_base * speed_mult) / substeps

    for _ in range(substeps):
        circle_angle = (circle_angle + ROT_SPEED * sub_dt) % (2 * np.pi)

        # Gap angular boundaries
        gap_start = (circle_angle - GAP_RAD / 2.0) % (2 * np.pi)
        gap_end = (circle_angle + GAP_RAD / 2.0) % (2 * np.pi)

        for i in range(NUM_BALLS):
            pos[i] += vel[i] * sub_dt

            if not escaped[i]:
                dx = pos[i, 0] - CX
                dy = pos[i, 1] - CY
                dist = np.hypot(dx, dy)

                if dist + BALL_RADIUS >= CIRCLE_RADIUS:
                    # Angle of the ball relative to circle center
                    ball_angle = np.arctan2(dy, dx) % (2 * np.pi)

                    # Check if ball hits within the 10-degree opening
                    is_in_gap = False
                    if gap_start < gap_end:
                        is_in_gap = (gap_start <= ball_angle <= gap_end)
                    else:
                        is_in_gap = (ball_angle >= gap_start or ball_angle <= gap_end)

                    if is_in_gap:
                        # Ball has reached the gap and escapes
                        escaped[i] = True
                    else:
                        # Elastic rebound off circular wall
                        normal = np.array([dx / dist, dy / dist])
                        v_dot_n = np.dot(vel[i], normal)

                        if v_dot_n > 0:
                            # Reflect velocity across normal
                            vel[i] = (vel[i] - 2.0 * v_dot_n * normal) * RESTITUTION
                            # Reposition inside boundary
                            pos[i] = np.array([CX, CY]) + normal * (CIRCLE_RADIUS - BALL_RADIUS - 0.5)

    # --- Frame Rendering ---
    frame = np.zeros((HEIGHT, WIDTH, 3), dtype=np.uint8)

    # 1. Draw Rotating Hollow Circle with 10-degree gap
    gap_mid_deg = np.degrees(circle_angle) % 360
    start_arc = gap_mid_deg + (GAP_ANGLE_DEG / 2.0)
    end_arc = gap_mid_deg + 360.0 - (GAP_ANGLE_DEG / 2.0)

    cv2.ellipse(
        frame,
        (CX, CY),
        (int(CIRCLE_RADIUS), int(CIRCLE_RADIUS)),
        0,
        start_arc,
        end_arc,
        (255, 255, 255),
        CIRCLE_THICKNESS,
        cv2.LINE_AA
    )

    # 2. Draw Balls and Motion Halos
    for i in range(NUM_BALLS):
        px, py = int(pos[i, 0]), int(pos[i, 1])
        if 0 <= px < WIDTH and 0 <= py < HEIGHT:
            # Outer colored aura
            cv2.circle(frame, (px, py), int(BALL_RADIUS + 2), colors[i], -1, cv2.LINE_AA)
            # Inner bright spot
            cv2.circle(frame, (px, py), int(BALL_RADIUS * 0.5), (255, 255, 255), -1, cv2.LINE_AA)

    # 3. HUD Counters for engagement
    escaped_count = np.sum(escaped)
    cv2.putText(frame, f"ESCAPED: {escaped_count} / {NUM_BALLS}", (CX - 190, CY - 460),
                cv2.FONT_HERSHEY_DUPLEX, 1.1, (255, 255, 255), 2, cv2.LINE_AA)

    if speed_mult > 1.2:
        cv2.putText(frame, f"SPEED: {speed_mult:.1f}x", (CX - 90, CY + 480),
                    cv2.FONT_HERSHEY_DUPLEX, 0.9, (0, 140, 255), 2, cv2.LINE_AA)

    out.write(frame)
    frame_idx += 1

out.release()
print(f"Render complete! Total frames: {frame_idx} ({frame_idx / FPS:.1f}s).")
