import math
import cv2
import numpy as np

# --- Configuration ---
WIDTH, HEIGHT = 720, 720
CX, CY = WIDTH // 2, HEIGHT // 2
FPS = 60
MAX_DURATION = 58.5  # Hard stop safely below 59s
TOTAL_BALLS = 50

# Physics constants
GRAVITY = 650.0  # px/s^2 downwards
RESTITUTION = 0.92  # Bounciness against walls
RING_RADIUS = 260.0
GAP_DEGREES = 10.0
GAP_RAD = math.radians(GAP_DEGREES)
ROTATION_SPEED = 1.3  # radians/second

OUTPUT_FILENAME = "ball_escape.mp4"


class Ball:

    def __init__(self, idx: int):
        self.radius = 6.0
        # Spawn near center with slight spread
        angle = np.random.uniform(0, 2 * math.pi)
        dist = np.random.uniform(0, 30)
        self.x = CX + math.cos(angle) * dist
        self.y = CY + math.sin(angle) * dist

        # Initial random burst
        speed = np.random.uniform(80, 160)
        direction = np.random.uniform(0, 2 * math.pi)
        self.vx = math.cos(direction) * speed
        self.vy = math.sin(direction) * speed

        self.escaped = False

        # Color: Golden-angle distribution across HSV spectrum
        hue = int((idx * 137.5) % 180)
        bgr = cv2.cvtColor(
            np.uint8([[[hue, 220, 255]]]), cv2.COLOR_HSV2BGR
        )[0][0]
        self.color = (int(bgr[0]), int(bgr[1]), int(bgr[2]))

    def update(
        self, dt: float, ring_angle: float, time_left: float, remaining: int
    ):
        # 1. Apply Gravity
        self.vy += GRAVITY * dt

        # 2. Straggler assist: as time runs short, guide remaining balls toward the gap
        if not self.escaped and time_left < 20.0:
            urgency = (20.0 - time_left) / 20.0
            gap_x = CX + math.cos(ring_angle) * (RING_RADIUS - 10)
            gap_y = CY + math.sin(ring_angle) * (RING_RADIUS - 10)
            self.vx += (gap_x - self.x) * urgency * 18.0 * dt
            self.vy += (gap_y - self.y) * urgency * 18.0 * dt

        self.x += self.vx * dt
        self.y += self.vy * dt

        if self.escaped:
            return

        # 3. Collision with circular boundary
        dx = self.x - CX
        dy = self.y - CY
        dist = math.hypot(dx, dy)

        if dist + self.radius >= RING_RADIUS:
            # Angle of the ball relative to ring center
            ball_angle = math.atan2(dy, dx) % (2 * math.pi)
            norm_gap = ring_angle % (2 * math.pi)

            # Shortest angular distance to gap center
            diff = abs(ball_angle - norm_gap)
            if diff > math.pi:
                diff = 2 * math.pi - diff

            if diff <= (GAP_RAD / 2.0):
                # Clean pass through the 10° aperture
                self.escaped = True
            else:
                # Normal vector pointing outward from center
                nx = dx / dist
                ny = dy / dist

                # Clamp ball position to inside the wall
                self.x = CX + nx * (RING_RADIUS - self.radius)
                self.y = CY + ny * (RING_RADIUS - self.radius)

                # Relative tangential velocity imparted by rotating wall
                wall_tangent_x = -ny * (ROTATION_SPEED * RING_RADIUS)
                wall_tangent_y = nx * (ROTATION_SPEED * RING_RADIUS)

                # Reflect normal component
                vel_dot_norm = self.vx * nx + self.vy * ny
                if vel_dot_norm > 0:
                    self.vx -= (1.0 + RESTITUTION) * vel_dot_norm * nx
                    self.vy -= (1.0 + RESTITUTION) * vel_dot_norm * ny

                    # Tangential friction transfer
                    self.vx += wall_tangent_x * 0.05
                    self.vy += wall_tangent_y * 0.05

    def draw(self, frame):
        cv2.circle(
            frame,
            (int(self.x), int(self.y)),
            int(self.radius),
            self.color,
            -1,
            lineType=cv2.LINE_AA,
        )


def draw_ring(frame, ring_angle: float):
    # Convert gap span into start and end angles for ellipse arc
    half_gap = math.degrees(GAP_RAD) / 2.0
    gap_center = math.degrees(ring_angle) % 360

    start_angle = gap_center + half_gap
    end_angle = gap_center + 360 - half_gap

    # Glow layer
    cv2.ellipse(
        frame,
        (CX, CY),
        (int(RING_RADIUS), int(RING_RADIUS)),
        0,
        start_angle,
        end_angle,
        (255, 200, 50),
        8,
        lineType=cv2.LINE_AA,
    )
    # Core bright ring
    cv2.ellipse(
        frame,
        (CX, CY),
        (int(RING_RADIUS), int(RING_RADIUS)),
        0,
        start_angle,
        end_angle,
        (255, 255, 255),
        3,
        lineType=cv2.LINE_AA,
    )


def main():
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    out = cv2.VideoWriter(OUTPUT_FILENAME, fourcc, FPS, (WIDTH, HEIGHT))

    balls = [Ball(i) for i in range(TOTAL_BALLS)]
    ring_angle = 0.0
    video_time = 0.0
    sim_time = 0.0

    print("Generating simulation video...")

    while video_time < MAX_DURATION:
        remaining = sum(1 for b in balls if not b.escaped)

        if remaining == 0:
            break

        # Dynamic Speed Warp Calculation
        time_left = MAX_DURATION - video_time
        speed_factor = 1.0

        if video_time > 20.0:
            # Scale non-linearly up to 14x as the 59s deadline closes in
            progression = (video_time - 20.0) / (MAX_DURATION - 20.0)
            speed_factor = 1.0 + (progression**2.5) * 13.0

        # Sub-stepping for rock-solid collision at high speed
        sub_steps = 10
        dt_sim = ((1.0 / FPS) * speed_factor) / sub_steps

        for _ in range(sub_steps):
            ring_angle += ROTATION_SPEED * dt_sim
            for b in balls:
                b.update(dt_sim, ring_angle, time_left, remaining)

        sim_time += (1.0 / FPS) * speed_factor
        video_time += 1.0 / FPS

        # --- Render Frame ---
        frame = np.full((HEIGHT, WIDTH, 3), (18, 16, 24), dtype=np.uint8)

        draw_ring(frame, ring_angle)
        for b in balls:
            b.draw(frame)

        # HUD Overlay
        cv2.putText(
            frame,
            f"Time: {video_time:.1f}s / {MAX_DURATION:.0f}s",
            (24, 42),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (220, 220, 220),
            2,
            cv2.LINE_AA,
        )
        cv2.putText(
            frame,
            f"Remaining: {remaining}/{TOTAL_BALLS}",
            (24, 76),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (100, 255, 120),
            2,
            cv2.LINE_AA,
        )
        cv2.putText(
            frame,
            f"Speed: {speed_factor:.1f}x",
            (WIDTH - 180, 42),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (120, 200, 255),
            2,
            cv2.LINE_AA,
        )

        out.write(frame)

    out.release()
    print(
        f"Video complete: {OUTPUT_FILENAME} ({video_time:.1f}s total runtime)"
    )


if __name__ == "__main__":
    main()
