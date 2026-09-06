import numpy as np
import cv2

# --- Video Config (9:16 YouTube Shorts) ---
WIDTH, HEIGHT = 1080, 1920
FPS = 60
MAX_DURATION = 58.0
MAX_FRAMES = int(FPS * MAX_DURATION)

CX = WIDTH // 2
CY = HEIGHT // 2
CIRCLE_RADIUS = 370.0
GAP_ANGLE_DEG = 12.0
GAP_RAD = np.radians(GAP_ANGLE_DEG)
CIRCLE_THICKNESS = 14

# --- Physics Constants ---
NUM_BALLS = 40                 # Slightly fewer so ball-ball collisions stay clean and visible
BALL_RADIUS = 12.0
GRAVITY = 720.0                # Downward pull creates parabolic arcs
RESTITUTION = 0.92             # Bounciness against wall
BALL_RESTITUTION = 0.90        # Bounciness between balls
WALL_FRICTION = 0.25           # Ring's rotation drags the ball tangentially
ROT_SPEED = 1.45               # Radians per sec of the spinning ring

# --- Initialize Ball States ---
np.random.seed(7)
pos = np.zeros((NUM_BALLS, 2), dtype=np.float64)
vel = np.zeros((NUM_BALLS, 2), dtype=np.float64)

# Spawn grouped in center with varied horizontal/vertical kicks
for i in range(NUM_BALLS):
    pos[i] = [CX + np.random.uniform(-40, 40), CY + np.random.uniform(-40, 40)]
    vel[i] = [np.random.uniform(-250, 250), np.random.uniform(-350, -50)]

escaped = np.zeros(NUM_BALLS, dtype=bool)

# Distinct bright neon colors (BGR)
colors = []
for i in range(NUM_BALLS):
    hue = int((i / NUM_BALLS) * 180)
    col = cv2.cvtColor(np.uint8([[[hue, 240, 255]]]), cv2.COLOR_HSV2BGR)[0][0]
    colors.append((int(col[0]), int(col[1]), int(col[2])))

fourcc = cv2.VideoWriter_fourcc(*'mp4v')
out = cv2.VideoWriter('circle_escape.mp4', fourcc, FPS, (WIDTH, HEIGHT))

canvas = np.zeros((HEIGHT, WIDTH, 3), dtype=np.uint8)
prev_pts = [None] * NUM_BALLS

circle_angle = 0.0
frame_idx = 0
dt_base = 1.0 / FPS

print("Simulating non-linear physics with gravity, friction & ball collisions...")

while frame_idx < MAX_FRAMES:
    current_time = frame_idx / FPS
    remaining = np.sum(~escaped)

    # Outro when all escaped
    if remaining == 0:
        for _ in range(int(FPS * 1.5)):
            if frame_idx >= MAX_FRAMES:
                break
            f_end = canvas.copy()
            cv2.putText(f_end, "ALL ESCAPED!", (CX - 220, CY - 420),
                        cv2.FONT_HERSHEY_DUPLEX, 1.3, (0, 255, 180), 2, cv2.LINE_AA)
            out.write(f_end)
            frame_idx += 1
        break

    # Dynamic speed scaling so it always wraps up under 59s
    if current_time > 38.0:
        speed_mult = 1.0 + ((current_time - 38.0) / 10.0) ** 2.2 * (remaining / 8.0)
    else:
        speed_mult = 1.0

    substeps = max(10, int(10 * min(speed_mult, 8.0)))
    sub_dt = (dt_base * speed_mult) / substeps

    for _ in range(substeps):
        circle_angle = (circle_angle + ROT_SPEED * sub_dt) % (2 * np.pi)
        gap_start = (circle_angle - GAP_RAD / 2.0) % (2 * np.pi)
        gap_end = (circle_angle + GAP_RAD / 2.0) % (2 * np.pi)

        # 1. Apply gravity and movement
        for i in range(NUM_BALLS):
            vel[i, 1] += GRAVITY * sub_dt
            pos[i] += vel[i] * sub_dt

        # 2. Ball-to-ball collisions (inside circle only)
        for i in range(NUM_BALLS):
            if escaped[i]:
                continue
            for j in range(i + 1, NUM_BALLS):
                if escaped[j]:
                    continue
                d_vec = pos[j] - pos[i]
                d_sq = d_vec[0]**2 + d_vec[1]**2
                min_dist = 2 * BALL_RADIUS
                if 0 < d_sq < min_dist**2:
                    d = np.sqrt(d_sq)
                    n = d_vec / d
                    # Positional pushback
                    overlap = 0.5 * (min_dist - d)
                    pos[i] -= n * overlap
                    pos[j] += n * overlap

                    # Elastic impulse exchange
                    k = vel[i] - vel[j]
                    p = 2.0 * np.dot(k, n) / 2.0
                    vel[i] -= p * n * BALL_RESTITUTION
                    vel[j] += p * n * BALL_RESTITUTION

        # 3. Ring wall collision with friction + escape check
        for i in range(NUM_BALLS):
            if not escaped[i]:
                dx = pos[i, 0] - CX
                dy = pos[i, 1] - CY
                dist = np.hypot(dx, dy)

                if dist + BALL_RADIUS >= CIRCLE_RADIUS:
                    ball_ang = np.arctan2(dy, dx) % (2 * np.pi)

                    # Check gap pass-through
                    in_gap = (gap_start <= ball_ang <= gap_end) if gap_start < gap_end else (ball_ang >= gap_start or ball_ang <= gap_end)

                    if in_gap:
                        escaped[i] = True
                    else:
                        n = np.array([dx / dist, dy / dist])
                        t = np.array([-n[1], n[0]])  # Tangent vector

                        v_dot_n = np.dot(vel[i], n)
                        v_dot_t = np.dot(vel[i], t)
                        wall_speed = ROT_SPEED * CIRCLE_RADIUS

                        if v_dot_n > 0:
                            # Rebound on normal
                            v_n_new = -v_dot_n * RESTITUTION
                            # Dragged by spinning wall along tangent
                            v_t_new = v_dot_t + (wall_speed - v_dot_t) * WALL_FRICTION
                            vel[i] = v_n_new * n + v_t_new * t

                            pos[i] = np.array([CX, CY]) + n * (CIRCLE_RADIUS - BALL_RADIUS - 0.5)

    # --- Render ---
    # Fade background slightly for neon tracer ribbons
    canvas = (canvas * 0.94).astype(np.uint8)

    # Draw moving curved trails
    for i in range(NUM_BALLS):
        px, py = int(pos[i, 0]), int(pos[i, 1])
        if 0 <= px < WIDTH and 0 <= py < HEIGHT:
            if prev_pts[i] is not None:
                cv2.line(canvas, prev_pts[i], (px, py), colors[i], 3, cv2.LINE_AA)
            prev_pts[i] = (px, py)

    frame = canvas.copy()

    # Draw rotating circle with gap
    gap_mid_deg = np.degrees(circle_angle) % 360
    start_arc = gap_mid_deg + (GAP_ANGLE_DEG / 2.0)
    end_arc = gap_mid_deg + 360.0 - (GAP_ANGLE_DEG / 2.0)

    cv2.ellipse(frame, (CX, CY), (int(CIRCLE_RADIUS), int(CIRCLE_RADIUS)),
                0, start_arc, end_arc, (255, 255, 255), CIRCLE_THICKNESS, cv2.LINE_AA)

    # Draw balls with glowing centers
    for i in range(NUM_BALLS):
        px, py = int(pos[i, 0]), int(pos[i, 1])
        if 0 <= px < WIDTH and 0 <= py < HEIGHT:
            cv2.circle(frame, (px, py), int(BALL_RADIUS), colors[i], -1, cv2.LINE_AA)
            cv2.circle(frame, (px, py), int(BALL_RADIUS * 0.45), (255, 255, 255), -1, cv2.LINE_AA)

    # Counter overlay
    esc_count = np.sum(escaped)
    cv2.putText(frame, f"ESCAPED: {esc_count} / {NUM_BALLS}", (CX - 190, CY - 460),
                cv2.FONT_HERSHEY_DUPLEX, 1.1, (255, 255, 255), 2, cv2.LINE_AA)

    if speed_mult > 1.2:
        cv2.putText(frame, f"SPEED: {speed_mult:.1f}x", (CX - 90, CY + 480),
                    cv2.FONT_HERSHEY_DUPLEX, 0.9, (0, 140, 255), 2, cv2.LINE_AA)

    out.write(frame)
    frame_idx += 1

out.release()
print(f"Done! Exported in {frame_idx / FPS:.1f}s.")
