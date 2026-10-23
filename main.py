import math
import random
import sys
import json
import datetime
import struct
from pathlib import Path
import pygame
pygame.init()

SOUND_ENABLED = True
SOUNDS = {}

def _make_tone(frequency=660, duration=0.09, volume=0.18, wave="sine"):
    try:
        sample_rate = 22050
        count = max(1, int(sample_rate * duration))
        samples = bytearray()
        for i in range(count):
            t = i / sample_rate
            envelope = min(1.0, i / max(1, sample_rate * 0.008), (count - i) / max(1, sample_rate * 0.025))
            value = math.sin(math.tau * frequency * t)
            if wave == "square":
                value = 1.0 if value >= 0 else -1.0
            sample = int(max(-1.0, min(1.0, value * volume * envelope)) * 32767)
            samples.extend(struct.pack("<h", sample))
        return pygame.mixer.Sound(buffer=bytes(samples))
    except (pygame.error, OSError):
        return None

def init_audio():
    global SOUND_ENABLED, SOUNDS
    try:
        if not pygame.mixer.get_init():
            pygame.mixer.init(frequency=22050, size=-16, channels=1, buffer=512)
        SOUNDS = {
            "hover": _make_tone(880, 0.025, 0.07),
            "click": _make_tone(620, 0.055, 0.13),
            "confirm": _make_tone(740, 0.10, 0.16),
            "alert": _make_tone(190, 0.22, 0.20, "square"),
            "success": _make_tone(990, 0.16, 0.15),
        }
        SOUND_ENABLED = True
    except pygame.error:
        SOUND_ENABLED = False
        SOUNDS = {}

def play_sound(name):
    if SOUND_ENABLED:
        sound = SOUNDS.get(name)
        if sound:
            try:
                sound.play()
            except pygame.error:
                pass

init_audio()
MUSIC_CHANNEL = None
MUSIC_SOUND = None
MUSIC_ENABLED = True
MUSIC_VOLUME = 0.22

def init_music():
    global MUSIC_CHANNEL, MUSIC_SOUND
    try:
        if not pygame.mixer.get_init():
            pygame.mixer.init(frequency=22050, size=-16, channels=1, buffer=512)
        music_file = Path(__file__).resolve().with_name("ironclad_theme.wav")
        if music_file.exists():
            MUSIC_SOUND = pygame.mixer.Sound(str(music_file))
        else:
            sample_rate = 22050
            seconds = 8.0
            total = int(sample_rate * seconds)
            samples = bytearray()
            beat_seconds = 0.75
            for i in range(total):
                t = i / sample_rate
                beat_phase = t % beat_seconds
                env = max(0.0, 1.0 - beat_phase / 0.28)
                bass_freq = (55.0, 65.4, 49.0, 73.4)[int(t / 2.0) % 4]
                bass = math.sin(math.tau * bass_freq * t) * 0.20
                sub = math.sin(math.tau * (bass_freq / 2) * t) * 0.14
                kick = math.sin(math.tau * (82.0 - 42.0 * min(1.0, beat_phase / 0.16)) * t) * env * 0.34
                tick_env = max(0.0, 1.0 - (t % (beat_seconds * 2)) / 0.035)
                tick = math.sin(math.tau * 1450 * t) * tick_env * 0.045
                edge = min(1.0, t / 0.12, (seconds - t) / 0.12)
                value = max(-0.95, min(0.95, (bass + sub + kick + tick) * max(0.0, edge)))
                samples.extend(struct.pack('<h', int(value * 32767)))
            MUSIC_SOUND = pygame.mixer.Sound(buffer=bytes(samples))
        MUSIC_SOUND.set_volume(MUSIC_VOLUME)
        MUSIC_CHANNEL = pygame.mixer.Channel(7)
    except (pygame.error, OSError):
        MUSIC_SOUND = None
        MUSIC_CHANNEL = None

def set_music_enabled(enabled):
    global MUSIC_ENABLED
    MUSIC_ENABLED = bool(enabled)
    if MUSIC_SOUND is None:
        init_music()
    if MUSIC_CHANNEL and MUSIC_SOUND:
        if MUSIC_ENABLED:
            MUSIC_CHANNEL.set_volume(MUSIC_VOLUME)
            if not MUSIC_CHANNEL.get_busy():
                MUSIC_CHANNEL.play(MUSIC_SOUND, loops=-1)
        else:
            MUSIC_CHANNEL.stop()

def set_music_volume(value):
    global MUSIC_VOLUME
    MUSIC_VOLUME = max(0.0, min(0.5, float(value)))
    if MUSIC_SOUND:
        MUSIC_SOUND.set_volume(MUSIC_VOLUME)
    if MUSIC_CHANNEL and MUSIC_ENABLED:
        MUSIC_CHANNEL.set_volume(MUSIC_VOLUME)

init_music()
set_music_enabled(True)
WIDTH, HEIGHT = 1440, 900
FPS = 60
TITLE = "IRONCLAD // Cyber Defense Initiative"
BG = (5, 10, 22)
PANEL = (10, 20, 38)
PANEL_LIGHT = (14, 29, 50)
CYAN = (45, 225, 255)
CYAN_DARK = (15, 118, 150)
WHITE = (225, 241, 250)
MUTED = (116, 148, 171)
GREEN = (74, 255, 170)
AMBER = (255, 190, 75)
RED = (255, 85, 110)
PURPLE = (170, 100, 255)
BORDER = (25, 65, 88)
screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
pygame.display.set_caption(TITLE)
clock = pygame.time.Clock()
FONT_CACHE = {}

def font(size, bold=False):
    key = (size, bold)
    if key not in FONT_CACHE:
        FONT_CACHE[key] = pygame.font.SysFont("consolas", size, bold=bold)
    return FONT_CACHE[key]

def text(surface, value, x, y, size=18, color=WHITE, bold=False):
    image = font(size, bold).render(str(value), True, color)
    surface.blit(image, (int(x), int(y)))
    return image.get_rect(topleft=(int(x), int(y)))

def panel(surface, rect, fill=PANEL, border=BORDER, radius=12, width=1):
    pygame.draw.rect(surface, fill, rect, border_radius=radius)
    pygame.draw.rect(surface, border, rect, width, border_radius=radius)

def glow_line(surface, start, end, color=CYAN, thickness=2):
    glow = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
    pygame.draw.line(glow, (*color, 22), start, end, thickness + 12)
    pygame.draw.line(glow, (*color, 45), start, end, thickness + 6)
    pygame.draw.line(glow, (*color, 100), start, end, thickness + 2)
    surface.blit(glow, (0, 0))
    pygame.draw.line(surface, color, start, end, thickness)

def draw_corner_marks(surface, rect, color=CYAN, length=15):
    x, y, w, h = rect
    lines = [
        ((x, y + length), (x, y), (x + length, y)),
        ((x + w - length, y), (x + w, y), (x + w, y + length)),
        ((x, y + h - length), (x, y + h), (x + length, y + h)),
        ((x + w - length, y + h), (x + w, y + h), (x + w, y + h - length)),
    ]
    for a, b, c in lines:
        pygame.draw.line(surface, color, a, b, 2)
        pygame.draw.line(surface, color, b, c, 2)

class Particle:
    def __init__(self):
        self.reset(random.uniform(0, HEIGHT))

    def reset(self, y=-10):
        self.x = random.uniform(0, WIDTH)
        self.y = y
        self.speed = random.uniform(12, 55)
        self.radius = random.choice([1, 1, 1, 2])
        self.phase = random.uniform(0, math.tau)

    def update(self, dt):
        self.y += self.speed * dt
        self.x += math.sin(self.y * 0.012 + self.phase) * 8 * dt
        if self.y > HEIGHT + 5:
            self.reset(-5)

    def draw(self, surface, elapsed):
        pulse = 0.55 + 0.45 * math.sin(elapsed * 2 + self.phase)
        color = (int(20 + 20 * pulse), int(110 + 100 * pulse), int(145 + 105 * pulse))
        pygame.draw.circle(surface, color, (int(self.x), int(self.y)), self.radius)

particles = [Particle() for _ in range(90)]

def draw_background(surface, elapsed, dt):
    surface.fill(BG)
    grid = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
    horizon = int(HEIGHT * 0.58)
    drift = int((elapsed * 22) % 42)
    for x in range(-WIDTH, WIDTH * 2, 70):
        pygame.draw.line(grid, (20, 100, 135, 24), (WIDTH // 2 + (x - WIDTH // 2) // 2, horizon), (x, HEIGHT), 1)
    for i in range(1, 12):
        base = horizon + i * i * 2 + drift
        if base < HEIGHT:
            pygame.draw.line(grid, (20, 100, 135, max(4, 24 - i)), (0, base), (WIDTH, base), 1)
    surface.blit(grid, (0, 0))
    for x in range(0, WIDTH, 4):
        pygame.draw.line(surface, (7, 17, 29), (x, 0), (x, HEIGHT), 1)
    for particle in particles:
        particle.update(dt)
        particle.draw(surface, elapsed)
    beam_y = int((elapsed * 42) % (HEIGHT + 100)) - 50
    beam = pygame.Surface((WIDTH, 36), pygame.SRCALPHA)
    pygame.draw.rect(beam, (25, 210, 255, 8), (0, 0, WIDTH, 36))
    pygame.draw.line(beam, (45, 225, 255, 36), (0, 18), (WIDTH, 18), 1)
    surface.blit(beam, (0, beam_y))

NAV_ITEMS = [
    ("01", "COMMAND DECK"),
    ("02", "CAMPAIGN MAP"),
    ("03", "INVENTORY"),
    ("04", "INTEL ARCHIVE"),
    ("05", "ACHIEVEMENTS"),
    ("06", "SETTINGS"),
    ("07", "PROFILE & RANK"),
]

selected_campaign = 0
selected_nav = 0
operator_username = "Operator001"
selected_avatar = 0
editing_username = False
leaderboard_records = []
toast_message = "SYSTEM READY // AWAITING COMMANDER"
toast_until = 0.0
elapsed_total = 0.0
fullscreen = False
SAVE_FILE = Path(__file__).resolve().parent / "ironclad_save.json"
mission_open = False
mission_debrief = False
mission_response = None
mission_xp = 0
total_xp = 120
inspected_evidence = set()
selected_evidence = 0
mission_completed = False                                            
completed_levels = set()
current_level = 1

CAMPAIGN_THEMES = [
    "CYBERSECURITY FOUNDATIONS", "IDENTITY & ACCESS", "PHISHING & SOCIAL ENGINEERING",
    "SOC & SECURITY MONITORING", "NETWORK DEFENCE", "DIGITAL FORENSICS",
    "ENDPOINT DETECTION", "CLOUD SECURITY", "WEB APPLICATION DEFENCE",
    "MALWARE ANALYSIS", "RANSOMWARE RESPONSE", "THREAT INTELLIGENCE",
    "VULNERABILITY MANAGEMENT", "PRIVACY & DATA PROTECTION", "ZERO TRUST OPERATIONS",
    "CONTAINER SECURITY", "INCIDENT COMMAND", "CRITICAL INFRASTRUCTURE",
    "ADVERSARY SIMULATION", "FINAL DEFENCE EXERCISE"
 ]

CAMPAIGN_SUBTITLES = [
    "Learn the rules. Enter the SOC.", "Trace stolen credentials and access.",
    "Separate human trust from deception.", "Turn noisy logs into useful signals.",
    "Follow suspicious traffic across the grid.", "Preserve evidence. Reconstruct events.",
    "Investigate endpoint behaviour.", "Protect cloud identities and workloads.",
    "Defend applications and APIs.", "Understand suspicious code behaviour.",
    "Limit destructive impact and recover.", "Use threat context to prioritise action.",
    "Reduce exposure through risk-based fixes.", "Protect sensitive information.",
    "Verify every access request.", "Secure containers and orchestration.",
    "Coordinate response under pressure.", "Protect operational technology.",
    "Think like an adversary; defend ethically.", "Integrate every skill in a final exercise.",
]
CAMPAIGNS = [(f"{i+1:02d}", title, CAMPAIGN_SUBTITLES[i], "LOCKED", MUTED)
             for i, title in enumerate(CAMPAIGN_THEMES)]
LEVEL_BLUEPRINTS = [
    ("Identity Anomaly", "Investigate suspicious authentication activity", "j.chen", "unfamiliar region"),
    ("Credential Replay", "Trace repeated sign-ins and suspected credential reuse", "m.lee", "hosting provider"),
    ("MFA Fatigue", "Assess a burst of denied and approved MFA prompts", "r.patel", "new device"),
    ("Privileged Session", "Review an unexpected privileged session", "svc-admin", "unmanaged endpoint"),
    ("Impossible Travel", "Correlate sign-ins that cannot fit the travel timeline", "a.morgan", "distant region"),
    ("Phishing Report", "Validate a reported message and scope recipient exposure", "finance-team", "lookalike domain"),
    ("Suspicious DNS", "Investigate unusual DNS lookups and beacon-like timing", "ws-014", "newly seen domain"),
    ("Lateral Movement", "Reconstruct access between internal hosts", "ops-admin", "peer workstation"),
    ("Data Exfiltration", "Determine whether unusual outbound transfer is authorised", "analytics-07", "external storage"),
    ("Cloud Key Exposure", "Assess possible exposure of a cloud access key", "cloud-build", "unknown API client"),
    ("Endpoint Persistence", "Investigate a persistence alert on a workstation", "eng-laptop", "scheduled task"),
    ("Ransomware Signal", "Prioritise early indicators of destructive activity", "file-srv-02", "rapid file changes"),
    ("Web Exploit Attempt", "Triage suspicious requests against a public application", "web-prod", "crafted request"),
    ("Container Drift", "Investigate a workload that departed from its baseline", "cluster-node-3", "unexpected process"),
    ("Vulnerability Exposure", "Prioritise an exposed service with suspicious access", "edge-gateway", "unpatched service"),
    ("Insider Risk Signal", "Separate legitimate bulk work from suspicious data access", "analyst-12", "unusual download"),
    ("Supply Chain Alert", "Assess a dependency or vendor-originated security alert", "build-agent", "unverified package"),
    ("Certificate Warning", "Investigate an unexpected certificate and trust change", "api-gateway", "unknown issuer"),
    ("Backup Integrity", "Determine whether backup failures indicate tampering", "backup-node", "deletion attempts"),
    ("Incident Coordination", "Correlate multiple alerts and choose a proportionate response", "enterprise-core", "multi-host activity"),
]
LEVELS = []
for _n in range(1, 101):
    _theme_index = (_n - 1) // 5
    _stage = (_n - 1) % 5
    _blueprint = LEVEL_BLUEPRINTS[(_n - 1) % len(LEVEL_BLUEPRINTS)]
    _suffixes = ["Initial Signal", "Evidence Correlation", "Scope Assessment", "Containment Decision", "Recovery Validation"]
    LEVELS.append({
        "id": _n,
        "campaign": _theme_index + 1,
        "campaign_title": CAMPAIGN_THEMES[_theme_index],
        "title": _blueprint[0] if _stage == 0 else f"{_blueprint[0]}: {_suffixes[_stage]}",
        "objective": _blueprint[1],
        "entity": _blueprint[2],
        "indicator": _blueprint[3],
        "stage": _stage + 1,
    })

def evidence_for_level(level_number):
    if level_number == 1:
        return LEVEL1_EVIDENCE
    level = LEVELS[max(0, min(99, level_number - 1))]
    entity, indicator = level["entity"], level["indicator"]
    return [
        ("01", "EVENT TIMELINE", f"A sequence of events involves {entity}.",
         f"The timeline for {entity} contains activity relevant to {level['title'].lower()}. Establish what happened first, normalise timestamps, and correlate adjacent events before concluding that the activity is malicious.", AMBER),
        ("02", "ASSET / IDENTITY CONTEXT", f"Observed indicator: {indicator}.",
         f"The alert associates {indicator} with {entity}. Validate the asset owner, business function, and expected baseline. An unusual indicator increases suspicion but should be corroborated with independent telemetry.", RED),
        ("03", "AUDIT TELEMETRY", "Related authentication or control-plane events are available.",
         f"Review the relevant audit trail for the {level['campaign_title'].lower()} campaign. Look for privilege changes, denied actions, new sessions, process launches, or policy changes that align with the reported event. Preserve the original logs.", PURPLE),
        ("04", "SCOPE & IMPACT", "The incident scope is not yet confirmed.",
         f"Determine whether the activity is isolated to {entity} or affects related identities, endpoints, workloads, or data. Use the evidence to choose targeted containment, continued monitoring, or escalation; avoid disruptive actions without sufficient justification.", CYAN),
    ]


RESPONSE_PROTOCOLS = [
    [("REVOKE SESSIONS", "revoke", GREEN), ("MONITOR ONLY", "monitor", AMBER), ("DISABLE ALL USERS", "broad", RED)],
    [("QUARANTINE MESSAGE", "quarantine", GREEN), ("WARN USERS ONLY", "monitor", AMBER), ("DISABLE MAIL SERVICE", "broad", RED)],
    [("TUNE CORRELATED RULE", "tune", GREEN), ("SUPPRESS THE ALERT", "dismiss", AMBER), ("STOP ALL LOGGING", "broad", RED)],
    [("BLOCK INDICATOR", "block", GREEN), ("WATCH TRAFFIC", "monitor", AMBER), ("DISCONNECT THE SUBNET", "broad", RED)],
    [("PRESERVE FORENSIC IMAGE", "preserve", GREEN), ("RESTART THE HOST", "restart", AMBER), ("WIPE THE DEVICE", "broad", RED)],
    [("ISOLATE ENDPOINT", "isolate", GREEN), ("WAIT FOR MORE ALERTS", "monitor", AMBER), ("POWER OFF FLEET", "broad", RED)],
    [("REVOKE EXPOSED KEY", "revoke", GREEN), ("ROTATE LATER", "monitor", AMBER), ("SHUT DOWN CLOUD", "broad", RED)],
    [("APPLY TARGETED MITIGATION", "mitigate", GREEN), ("MONITOR REQUESTS", "monitor", AMBER), ("TAKE APP OFFLINE", "broad", RED)],
    [("ISOLATE AFFECTED WORKLOAD", "isolate", GREEN), ("COLLECT MORE TELEMETRY", "monitor", AMBER), ("STOP THE CLUSTER", "broad", RED)],
    [("CONTAIN AND VERIFY BACKUPS", "recover", GREEN), ("RESTORE IMMEDIATELY", "restart", AMBER), ("ERASE AFFECTED SYSTEMS", "broad", RED)],
    [("ENRICH IOC AND HUNT", "hunt", GREEN), ("CLOSE AS DUPLICATE", "dismiss", AMBER), ("BLOCK ALL EXTERNAL ACCESS", "broad", RED)],
    [("PATCH EXPOSED SERVICE", "patch", GREEN), ("DEFER TO NEXT WINDOW", "monitor", AMBER), ("DISABLE THE NETWORK EDGE", "broad", RED)],
    [("RESTRICT DATA ACCESS", "restrict", GREEN), ("AUDIT NEXT WEEK", "monitor", AMBER), ("LOCK ALL EMPLOYEES OUT", "broad", RED)],
    [("ENFORCE VERIFIED ACCESS", "verify", GREEN), ("TRUST CURRENT SESSION", "monitor", AMBER), ("DISABLE IDENTITY PROVIDER", "broad", RED)],
    [("ROLL BACK CHANGE", "rollback", GREEN), ("ACCEPT CONFIGURATION DRIFT", "monitor", AMBER), ("STOP ALL WORKLOADS", "broad", RED)],
    [("APPOINT INCIDENT LEAD", "escalate", GREEN), ("LET EACH TEAM ACT ALONE", "monitor", AMBER), ("DECLARE TOTAL SHUTDOWN", "broad", RED)],
    [("SEGMENT AFFECTED OT ZONE", "segment", GREEN), ("CHANGE NOTHING", "monitor", AMBER), ("POWER DOWN PLANT NETWORK", "broad", RED)],
    [("VALIDATE AND CONTAIN", "contain", GREEN), ("ASSUME FALSE POSITIVE", "dismiss", AMBER), ("ISOLATE THE ENTERPRISE", "broad", RED)],
    [("CORRELATE THEN RESPOND", "correlate", GREEN), ("CLOSE WITHOUT REVIEW", "dismiss", AMBER), ("DISABLE ALL CONTROLS", "broad", RED)],
]

def response_options_for_level(level_number):
    campaign_idx = min(19, max(0, (level_number - 1) // 5))
    return RESPONSE_PROTOCOLS[(level_number - 1) % len(RESPONSE_PROTOCOLS)]

def recommended_action_for_level(level_number):
    return response_options_for_level(level_number)[0][1]

def outcome_for_response(action, level_number):
    if action == recommended_action_for_level(level_number):
        return ("PROPORTIONATE RESPONSE — OBJECTIVE MET", GREEN,
                "You chose a targeted action aligned to this incident. Preserve evidence, verify the change worked, and continue monitoring for related activity.")
    if action == "broad":
        return ("RISK REDUCED — EXCESSIVE BLAST RADIUS", AMBER,
                "A broad shutdown can disrupt critical services and destroy useful context. Scope the affected identities, hosts, or workloads and escalate only when evidence justifies wider action.")
    if action in ("dismiss", "monitor"):
        return ("INSUFFICIENT RESPONSE — RISK REMAINS", RED,
                "Monitoring or dismissal alone does not reduce the confirmed risk. Correlate the evidence and take a proportionate action when the indicators justify it.")
    return ("PARTIAL MITIGATION — VALIDATE THE RESULT", AMBER,
            "This action may help, but it does not fully address the incident as presented. Revisit the evidence, confirm scope, and select the incident-specific control before declaring containment.")

def load_progress():
    global total_xp, mission_completed, completed_levels, current_level, operator_username, leaderboard_records, selected_avatar
    try:
        if SAVE_FILE.exists():
            with SAVE_FILE.open("r", encoding="utf-8") as save_file:
                data = json.load(save_file)
            total_xp = max(0, int(data.get("total_xp", total_xp)))
            mission_completed = bool(data.get("mission_01_completed", False))
            raw_completed = data.get("completed_levels", [1] if mission_completed else [])
            completed_levels = {int(v) for v in raw_completed if 1 <= int(v) <= 100}
            if mission_completed:
                completed_levels.add(1)
            current_level = next((n for n in range(1, 101) if n not in completed_levels), 100)
            operator_username = str(data.get("operator_username", "Operator001"))[:18] or "Operator001"
            selected_avatar = max(0, min(14, int(data.get("selected_avatar", 0))))
            raw_board = data.get("leaderboard_records", [])
            if isinstance(raw_board, list):
                leaderboard_records = [r for r in raw_board if isinstance(r, dict) and isinstance(r.get("username"), str)][:50]
    except (OSError, ValueError, TypeError, json.JSONDecodeError):
        pass


def save_progress():
    global leaderboard_records
    current_record = {"username": operator_username[:18] or "Operator001", "xp": int(total_xp), "missions": len(completed_levels), "selected_avatar": int(selected_avatar)}
    leaderboard_records = [r for r in leaderboard_records if str(r.get("username", "")).casefold() != current_record["username"].casefold()]
    leaderboard_records.append(current_record)
    leaderboard_records.sort(key=lambda r: (int(r.get("xp", 0)), int(r.get("missions", 0))), reverse=True)
    leaderboard_records = leaderboard_records[:50]
    data = {
        "version": 2,
        "total_xp": int(total_xp),
        "mission_01_completed": bool(mission_completed),
        "completed_levels": sorted(completed_levels),
        "unlocked_campaigns": min(20, max(1, (max(completed_levels, default=0) + 4) // 5 + 1)),
        "operator_username": operator_username,
        "selected_avatar": int(selected_avatar),
        "leaderboard_records": leaderboard_records[:50],
    }
    try:
        temporary_file = SAVE_FILE.with_suffix(".tmp")
        with temporary_file.open("w", encoding="utf-8") as save_file:
            json.dump(data, save_file, indent=2)
        temporary_file.replace(SAVE_FILE)
    except OSError:
        pass


load_progress()
selected_campaign = min((current_level - 1) // 5, len(CAMPAIGNS) - 1)

LEVEL1_EVIDENCE = [
    ("01", "AUTHENTICATION TIMELINE", "4 failed logins, then a successful login at 02:13.",
     "The account received four failed authentication attempts followed by a successful sign-in. This pattern can indicate password guessing or use of stolen credentials. Correlate it with device and location data before deciding.", AMBER),
    ("02", "DEVICE TRUST", "Successful sign-in came from an unregistered device.",
     "The endpoint is not registered in the organisation's device inventory. An unfamiliar device raises the risk, but it is not proof of compromise by itself. Preserve sign-in and endpoint telemetry.", RED),
    ("03", "MFA EVENT", "An MFA challenge was approved shortly before access.",
     "MFA approval does not automatically mean the sign-in was legitimate. The user may have approved a prompt under pressure, or an attacker may have used an MFA fatigue or social-engineering technique. Verify with the account owner through a trusted channel.", PURPLE),
    ("04", "USER BASELINE", "Sign-in time and region differ from the user's normal pattern.",
     "The 02:13 sign-in is outside the user's normal activity window and originates from an unusual region. Combined with failed attempts and an untrusted device, this supports treating the event as a likely account compromise.", CYAN),
]

def draw_button(surface, rect, label, mouse_pos, active=False, enabled=True, small=False):
    hovered = rect.collidepoint(mouse_pos)
    fill = (13, 43, 61) if hovered or active else (8, 22, 39)
    border = CYAN if hovered or active else BORDER
    if not enabled:
        fill, border = (9, 17, 29), (24, 43, 56)
    pygame.draw.rect(surface, fill, rect, border_radius=7)
    pygame.draw.rect(surface, border, rect, 1, border_radius=7)
    if hovered and enabled:
        draw_corner_marks(surface, rect, CYAN, 7)
    size = 13 if small else 15
    color = WHITE if enabled else MUTED
    label_img = font(size, True).render(label, True, color)
    surface.blit(label_img, label_img.get_rect(center=rect.center))
    return hovered

def draw_sidebar(surface, w, h, mouse_pos):
    sidebar_w = 238
    pygame.draw.rect(surface, (6, 14, 28), (0, 0, sidebar_w, h))
    pygame.draw.line(surface, BORDER, (sidebar_w, 0), (sidebar_w, h), 1)
    mark = [(28, 34), (47, 25), (66, 34), (66, 55), (47, 66), (28, 55)]
    pygame.draw.polygon(surface, CYAN, mark, 2)
    text(surface, "I", 42, 33, 25, WHITE, True)
    text(surface, "IRONCLAD", 79, 28, 23, WHITE, True)
    text(surface, "CYBER DEFENSE INITIATIVE", 80, 53, 8, CYAN)
    glow_line(surface, (22, 86), (216, 86), CYAN_DARK, 1)
    text(surface, "OPERATOR MENU", 25, 108, 11, MUTED, True)
    nav_rects = []
    for i, (num, label) in enumerate(NAV_ITEMS):
        y = 143 + i * 51
        rect = pygame.Rect(17, y, 204, 40)
        nav_rects.append(rect)
        active = i == selected_nav
        hovered = rect.collidepoint(mouse_pos)
        if active or hovered:
            pygame.draw.rect(surface, (10, 38, 54), rect, border_radius=6)
            pygame.draw.rect(surface, CYAN if active else CYAN_DARK, rect, 1, border_radius=6)
            pygame.draw.rect(surface, CYAN, (17, y + 7, 3, 26), border_radius=2)
        text(surface, num, 29, y + 12, 11, CYAN if active else MUTED)
        text(surface, label, 57, y + 11, 12, WHITE if active else MUTED, active)
    card = pygame.Rect(17, h - 144, 204, 119)
    panel(surface, card, fill=(8, 24, 40), border=BORDER, radius=9)
    pygame.draw.circle(surface, CYAN_DARK, (43, h - 112), 16, 2)
    pygame.draw.circle(surface, CYAN, (43, h - 112), 7, 1)
    text(surface, "OPERATOR 001", 68, h - 128, 11, WHITE, True)
    text(surface, "CADET / LEVEL 01", 68, h - 108, 10, CYAN)
    text(surface, "XP", 29, h - 78, 9, MUTED)
    pygame.draw.rect(surface, (22, 48, 65), (29, h - 59, 178, 5), border_radius=3)
    xp_progress = min(178, int(178 * min(total_xp, 500) / 500))
    pygame.draw.rect(surface, CYAN, (29, h - 59, xp_progress, 5), border_radius=3)
    text(surface, f"{total_xp} / 500", 29, h - 47, 10, MUTED)
    return nav_rects

def draw_topbar(surface, w):
    text(surface, "SECURITY OPERATIONS CENTER", 270, 27, 12, CYAN, True)
    text(surface, "// TRAINING SIMULATION  •  100-LEVEL CAMPAIGN  •  BUILD 0.2.0", 270, 48, 9, MUTED)
    pygame.draw.circle(surface, GREEN, (w - 224, 35), 4)
    text(surface, "ALL SYSTEMS NOMINAL", w - 211, 28, 10, GREEN, True)
    text(surface, "UTC  //  SIMULATED", w - 211, 45, 9, MUTED)
    pygame.draw.line(surface, BORDER, (260, 72), (w - 28, 72), 1)

def draw_dashboard(surface, w, h, mouse_pos, elapsed):
    content_x = 270
    content_w = w - content_x - 30
    hero = pygame.Rect(content_x, 94, content_w, 174)
    panel(surface, hero, fill=(7, 22, 39), border=(23, 87, 112), radius=12)
    draw_corner_marks(surface, hero, CYAN_DARK, 17)
    cx, cy = w - 135, 178
    radar = pygame.Surface((190, 190), pygame.SRCALPHA)
    for radius in (36, 60, 84):
        pygame.draw.circle(radar, (30, 180, 220, 45), (95, 95), radius, 1)
    angle = elapsed * 0.8
    end = (95 + math.cos(angle) * 82, 95 + math.sin(angle) * 82)
    pygame.draw.line(radar, (45, 225, 255, 180), (95, 95), end, 2)
    pygame.draw.circle(radar, (45, 225, 255, 220), (95, 95), 3)
    surface.blit(radar, (cx - 95, cy - 95))
    text(surface, "WELCOME BACK, COMMANDER.", content_x + 26, 116, 12, CYAN, True)
    text(surface, "The network is waiting.", content_x + 26, 141, 31, WHITE, True)
    text(surface, "Every alert tells a story. Find the evidence.", content_x + 27, 184, 15, MUTED)
    text(surface, "Investigate. Contain. Recover. Learn.", content_x + 27, 207, 13, MUTED)
    launch_rect = pygame.Rect(content_x + 27, 230, 178, 27)
    draw_button(surface, launch_rect, "RESUME TRAINING  >", mouse_pos, active=True, small=True)
    gap = 14
    card_y = 286
    card_h = 85
    card_w = (content_w - 2 * gap) // 3
    campaigns_cleared = min(20, max(1, (len(completed_levels) + 4) // 5 + 1))
    missions_cleared = len(completed_levels)
    stats = [
        ("CAMPAIGNS", f"{campaigns_cleared:02d} / 20", "20 CAMPAIGNS // 5 LEVELS EACH", CYAN),
        ("MISSIONS CLEARED", f"{missions_cleared:02d} / 100", "ALL LEVELS TRACKED LOCALLY", GREEN),
        ("THREAT LEVEL", "LOW", "SIMULATION STABLE", AMBER),
    ]
    for i, (label, value, sub, color) in enumerate(stats):
        rect = pygame.Rect(content_x + i * (card_w + gap), card_y, card_w, card_h)
        panel(surface, rect, fill=(8, 21, 37), border=BORDER, radius=9)
        text(surface, label, rect.x + 16, rect.y + 12, 10, MUTED, True)
        text(surface, value, rect.x + 16, rect.y + 29, 22, color, True)
        text(surface, sub, rect.x + 16, rect.y + 60, 9, MUTED)

    text(surface, "MISSION SELECT", content_x, 398, 16, WHITE, True)
    text(surface, "20 CAMPAIGNS  //  5 LEVELS EACH  //  100 LEVELS TOTAL", content_x, 421, 10, MUTED)
    text(surface, "SELECT A CAMPAIGN TO VIEW BRIEFING", w - 355, 405, 10, CYAN)

    cards_top = 449
    card_gap = 13
    card_width = (content_w - 2 * card_gap) // 3
    card_height = min(132, max(112, (h - cards_top - 38) // 2))
    campaign_rects = []
    for i, (number, title, subtitle, status, status_color) in enumerate(CAMPAIGNS):
        row, col = divmod(i, 3)
        x = content_x + col * (card_width + card_gap)
        y = cards_top + row * (card_height + 13)
        rect = pygame.Rect(x, y, card_width, card_height)
        campaign_rects.append(rect)
        active_campaign_index = min((current_level - 1) // 5, len(CAMPAIGNS) - 1)
        campaign_first_level = i * 5 + 1
        campaign_last_level = i * 5 + 5
        campaign_is_complete = all(n in completed_levels for n in range(campaign_first_level, campaign_last_level + 1))
        unlocked = i <= active_campaign_index
        if campaign_is_complete:
            status, status_color = "COMPLETE", GREEN
        elif unlocked and i == active_campaign_index:
            status, status_color = "IN PROGRESS", CYAN
        elif unlocked:
            status, status_color = "UNLOCKED", CYAN
        hovered = rect.collidepoint(mouse_pos)
        chosen = i == selected_campaign
        fill = (11, 35, 51) if hovered or chosen else (7, 19, 34)
        border = CYAN if chosen or hovered else BORDER
        panel(surface, rect, fill=fill, border=border, radius=9)
        if chosen or hovered:
            draw_corner_marks(surface, rect, CYAN, 10)
        text(surface, f"CAMPAIGN {number}", x + 15, y + 13, 10, CYAN if unlocked else MUTED, True)
        pygame.draw.circle(surface, status_color, (x + card_width - 20, y + 18), 4)
        text(surface, title, x + 15, y + 36, 13, WHITE if unlocked else MUTED, True)
        text(surface, subtitle, x + 15, y + 59, 10, MUTED)
        pygame.draw.line(surface, BORDER, (x + 15, y + 83), (x + card_width - 15, y + 83), 1)
        text(surface, status, x + 15, y + 94, 10, status_color, True)
        text(surface, "5 MISSIONS", x + card_width - 100, y + 94, 9, MUTED)

    footer_y = h - 22
    text(surface, "IRONCLAD // LEARN TO DEFEND WHAT MATTERS", content_x, footer_y, 9, MUTED)
    text(surface, "DEMO BUILD 0.1.0", w - 155, footer_y, 9, CYAN_DARK)
    return campaign_rects, pygame.Rect(content_x + 27, 230, 178, 27)

def draw_briefing(surface, w, h, campaign_index, mouse_pos):
    shade = pygame.Surface((w, h), pygame.SRCALPHA)
    shade.fill((2, 7, 16, 205))
    surface.blit(shade, (0, 0))
    box_w, box_h = min(680, w - 60), 390
    rect = pygame.Rect((w - box_w) // 2, (h - box_h) // 2, box_w, box_h)
    panel(surface, rect, fill=(7, 22, 39), border=CYAN, radius=14, width=2)
    draw_corner_marks(surface, rect, CYAN, 20)
    number, title, subtitle, status, _ = CAMPAIGNS[campaign_index]
    text(surface, "MISSION BRIEFING // CLASSIFIED TRAINING", rect.x + 28, rect.y + 28, 11, CYAN, True)
    text(surface, f"CAMPAIGN {number}", rect.x + 28, rect.y + 62, 12, MUTED)
    text(surface, title, rect.x + 28, rect.y + 88, 22, WHITE, True)
    text(surface, subtitle, rect.x + 28, rect.y + 125, 13, MUTED)
    pygame.draw.line(surface, BORDER, (rect.x + 28, rect.y + 158), (rect.right - 28, rect.y + 158), 1)
    active_campaign_index = min((current_level - 1) // 5, len(CAMPAIGNS) - 1)
    if campaign_index <= active_campaign_index:
        campaign_start = campaign_index * 5 + 1
        campaign_end = campaign_index * 5 + 5
        completed_in_campaign = sum(1 for n in range(campaign_start, campaign_end + 1) if n in completed_levels)
        if campaign_index < active_campaign_index:
            text(surface, "CAMPAIGN CLEARED", rect.x + 28, rect.y + 190, 14, GREEN, True)
            text(surface, f"Levels {campaign_start:03d}–{campaign_end:03d} completed.", rect.x + 28, rect.y + 222, 12, WHITE)
            text(surface, "Select the active campaign to continue your progression.", rect.x + 28, rect.y + 246, 11, MUTED)
            start_rect = pygame.Rect(rect.x + 28, rect.y + 302, 140, 42)
            draw_button(surface, start_rect, "VIEW STATUS", mouse_pos, active=True)
        else:
            text(surface, "ACCESS GRANTED // CAMPAIGN ACTIVE", rect.x + 28, rect.y + 190, 12, GREEN, True)
            text(surface, f"Next available mission: LEVEL {current_level:03d} / 100", rect.x + 28, rect.y + 222, 12, WHITE)
            text(surface, f"Campaign progress: {completed_in_campaign}/5 levels cleared.", rect.x + 28, rect.y + 246, 11, MUTED)
            start_rect = pygame.Rect(rect.x + 28, rect.y + 302, 220, 42)
            draw_button(surface, start_rect, f"START LEVEL {current_level:03d}  >", mouse_pos, active=True)
    else:
        text(surface, "ACCESS RESTRICTED", rect.x + 28, rect.y + 190, 14, AMBER, True)
        text(surface, "Complete the current campaign to unlock this area.", rect.x + 28, rect.y + 222, 12, MUTED)
        start_rect = pygame.Rect(rect.x + 28, rect.y + 302, 140, 42)
        draw_button(surface, start_rect, "UNDERSTOOD", mouse_pos, active=True)

    close_rect = pygame.Rect(rect.right - 150, rect.y + 302, 120, 42)
    draw_button(surface, close_rect, "CLOSE  [X]", mouse_pos)
    return start_rect, close_rect


def draw_level1(surface, w, h, mouse_pos):
    level = LEVELS[max(0, min(99, current_level - 1))]
    x0 = 270
    content_w = w - x0 - 30
    text(surface, f"CAMPAIGN {level['campaign']:02d}  /  LEVEL {current_level:03d} OF 100", x0, 94, 11, CYAN, True)
    text(surface, level["title"].upper(), x0, 116, 25, WHITE, True)
    text(surface, level["objective"] + ". Review evidence before choosing a response.", x0, 151, 12, MUTED)
    alert = pygame.Rect(x0, 184, content_w, 104)
    panel(surface, alert, fill=(35, 16, 29), border=RED, radius=10)
    draw_corner_marks(surface, alert, RED, 12)
    pygame.draw.circle(surface, RED, (alert.x + 25, alert.y + 28), 6)
    text(surface, "HIGH PRIORITY  //  AUTHENTICATION ALERT", alert.x + 43, alert.y + 17, 11, RED, True)
    text(surface, f"Entity: {level['entity']}  |  Indicator: {level['indicator']}  |  Event: {datetime.datetime.now().strftime('%H:%M:%S')}", alert.x + 22, alert.y + 46, 12, WHITE)
    text(surface, "SIMULATED TELEMETRY — NO REAL SYSTEMS ARE CONNECTED", alert.x + 22, alert.y + 73, 9, MUTED)
    evidence_items = evidence_for_level(current_level)
    text(surface, "EVIDENCE LOCKER", x0, 310, 14, WHITE, True)
    text(surface, f"{len(inspected_evidence)}/4 SOURCES REVIEWED", w - 275, 313, 10, CYAN, True)
    gap = 12
    card_w = (content_w - gap) // 2
    card_h = 100
    evidence_rects = []
    for i, item in enumerate(evidence_items):
        num, title, summary, detail, color = item
        row, col = divmod(i, 2)
        rect = pygame.Rect(x0 + col * (card_w + gap), 338 + row * (card_h + 12), card_w, card_h)
        evidence_rects.append(rect)
        seen = i in inspected_evidence
        hovered = rect.collidepoint(mouse_pos)
        panel(surface, rect, fill=(10, 35, 49) if (hovered or i == selected_evidence) else (7, 21, 37),
              border=GREEN if seen else (color if hovered or i == selected_evidence else BORDER), radius=8)
        text(surface, f"[{num}]", rect.x + 13, rect.y + 12, 10, color, True)
        text(surface, title, rect.x + 50, rect.y + 11, 11, WHITE, True)
        text(surface, summary, rect.x + 13, rect.y + 39, 10, MUTED)
        text(surface, "REVIEWED ✓" if seen else "CLICK TO INSPECT  >", rect.x + 13, rect.y + 72, 9, GREEN if seen else CYAN, True)
    detail_rect = pygame.Rect(x0, 570, content_w, 91)
    panel(surface, detail_rect, fill=(7, 19, 34), border=BORDER, radius=8)
    selected = evidence_items[selected_evidence]
    text(surface, "INTEL DETAIL  //  " + selected[1], detail_rect.x + 15, detail_rect.y + 12, 10, selected[4], True)
    detail = selected[3]
    words, lines, line = detail.split(), [], ""
    max_width = content_w - 34
    for word in words:
        trial = (line + " " + word).strip()
        if font(10).size(trial)[0] > max_width and line:
            lines.append(line)
            line = word
        else:
            line = trial
    if line:
        lines.append(line)
    for j, line_text in enumerate(lines[:3]):
        text(surface, line_text, detail_rect.x + 15, detail_rect.y + 34 + j * 15, 10, WHITE if j == 0 else MUTED)
    text(surface, "RESPONSE PROTOCOL", x0, 681, 12, WHITE, True)
    text(surface, "Choose the least disruptive action that adequately reduces risk.", x0, 701, 10, MUTED)
    btn_y = 728
    btn_w = (content_w - 24) // 3
    responses = response_options_for_level(current_level)
    response_rects = []
    for i, (label, action, color) in enumerate(responses):
        rect = pygame.Rect(x0 + i * (btn_w + 12), btn_y, btn_w, 43)
        response_rects.append((rect, action))
        draw_button(surface, rect, label, mouse_pos, active=(action == "contain"), enabled=True)
        pygame.draw.rect(surface, color, (rect.x + 8, rect.y + 8, 3, rect.height - 16), border_radius=2)
    text(surface, "Select the control that matches this incident; validate impact before closing.", x0, 783, 10, MUTED)
    return evidence_rects, response_rects


def draw_level1_debrief(surface, w, h, mouse_pos):
    shade = pygame.Surface((w, h), pygame.SRCALPHA)
    shade.fill((2, 7, 16, 225))
    surface.blit(shade, (0, 0))
    box_w, box_h = min(760, w - 50), min(610, h - 50)
    rect = pygame.Rect((w - box_w) // 2, (h - box_h) // 2, box_w, box_h)
    panel(surface, rect, fill=(7, 22, 39), border=CYAN, radius=14, width=2)
    draw_corner_marks(surface, rect, CYAN, 18)
    text(surface, f"MISSION DEBRIEF  //  LEVEL {current_level:03d} OF 100", rect.x + 28, rect.y + 25, 11, CYAN, True)
    headline, color, explanation = outcome_for_response(mission_response, current_level)
    text(surface, headline, rect.x + 28, rect.y + 61, 16, color, True)
    text(surface, explanation, rect.x + 28, rect.y + 91, 11, WHITE)
    pygame.draw.line(surface, BORDER, (rect.x + 28, rect.y + 121), (rect.right - 28, rect.y + 121), 1)
    text(surface, "WHAT THE EVIDENCE TOLD YOU", rect.x + 28, rect.y + 141, 11, CYAN, True)
    level_data = LEVELS[max(0, min(99, current_level - 1))]
    lessons = [
        f"• Incident: {level_data['title']} — campaign {level_data['campaign']:02d}.",
        f"• Primary entity: {level_data['entity']}; indicator: {level_data['indicator']}.",
        "• Correlate independent telemetry; an anomaly alone is not proof of compromise.",
        "• Preserve evidence, scope impact, validate the response, and document decisions.",
    ]
    for i, lesson in enumerate(lessons):
        text(surface, lesson, rect.x + 28, rect.y + 172 + i * 28, 10, WHITE)
    text(surface, "MISSION SCORE", rect.x + 28, rect.y + 306, 11, CYAN, True)
    text(surface, f"+{mission_xp} XP", rect.x + 28, rect.y + 332, 29, GREEN if mission_xp >= 100 else AMBER, True)
    text(surface, f"Evidence reviewed: {len(inspected_evidence)}/4", rect.x + 190, rect.y + 340, 12, MUTED)
    text(surface, "XP is awarded once per level. Review evidence and choose a proportionate response.", rect.x + 28, rect.y + 383, 10, MUTED)
    replay_rect = pygame.Rect(rect.x + 28, rect.bottom - 67, 190, 40)
    dashboard_rect = pygame.Rect(rect.right - 218, rect.bottom - 67, 190, 40)
    draw_button(surface, replay_rect, "REPLAY LEVEL", mouse_pos, active=True)
    next_label = "CAMPAIGN COMPLETE" if current_level >= 100 and current_level in completed_levels else ("NEXT LEVEL  >" if current_level in completed_levels else "RETURN TO SOC")
    draw_button(surface, dashboard_rect, next_label, mouse_pos)
    return replay_rect, dashboard_rect



AVATAR_PALETTES = [
    ((255, 45, 70), (24, 32, 48)), ((35, 150, 255), (14, 35, 68)),
    ((255, 75, 58), (43, 43, 50)), ((207, 55, 255), (35, 18, 52)),
    ((255, 174, 55), (45, 33, 20)), ((50, 255, 150), (12, 43, 37)),
    ((255, 45, 100), (45, 15, 28)), ((95, 90, 255), (18, 24, 62)),
    ((255, 30, 40), (45, 15, 20)), ((35, 235, 255), (12, 40, 53)),
    ((220, 230, 255), (38, 43, 60)), ((225, 40, 255), (36, 15, 51)),
    ((255, 170, 30), (40, 32, 20)), ((40, 120, 255), (14, 27, 48)),
    ((255, 40, 180), (39, 12, 40)),
]


def draw_cyborg_avatar(surface, rect, avatar_id, selected=False, scale=1.0):
    accent, dark = AVATAR_PALETTES[avatar_id % len(AVATAR_PALETTES)]
    cx, cy = rect.center
    radius = max(7, min(rect.width, rect.height) // 2 - 3)
    pygame.draw.circle(surface, (3, 11, 22), (cx, cy), radius + 2)
    pygame.draw.circle(surface, accent, (cx, cy), radius + 2, 2 if selected else 1)
    pygame.draw.circle(surface, dark, (cx, cy), radius - 2)
    shoulder_y = cy + int(radius*.47)
    pygame.draw.polygon(surface, (12, 25, 39), [(cx-radius*.70, cy+radius*.80), (cx-radius*.48, shoulder_y), (cx, cy+radius*.48), (cx+radius*.48, shoulder_y), (cx+radius*.70, cy+radius*.80)])
    pygame.draw.lines(surface, accent, False, [(cx-radius*.55, cy+radius*.65),(cx-radius*.30, shoulder_y+2),(cx, cy+radius*.55),(cx+radius*.30, shoulder_y+2),(cx+radius*.55, cy+radius*.65)], 2)
    head_w, head_h = radius*.83, radius*.98
    head = pygame.Rect(int(cx-head_w/2), int(cy-head_h*.62), int(head_w), int(head_h))
    pygame.draw.rect(surface, (16, 27, 42), head, border_radius=max(3, radius//4))
    pygame.draw.polygon(surface, accent, [(head.left,head.top+radius*.2),(cx-radius*.36,head.top-radius*.08),(cx+radius*.30,head.top-radius*.08),(head.right,head.top+radius*.2),(head.right-radius*.08,cy+radius*.22),(cx,cy+radius*.42),(head.left+radius*.08,cy+radius*.22)], 2)
    eye_y = cy-int(radius*.05)
    if avatar_id % 3 == 0:
        pygame.draw.line(surface, accent, (cx-radius*.30,eye_y), (cx+radius*.30,eye_y), max(2,radius//7))
        pygame.draw.line(surface, (255,220,225), (cx-radius*.14,eye_y), (cx+radius*.14,eye_y), 1)
    elif avatar_id % 3 == 1:
        pygame.draw.polygon(surface, accent, [(cx-radius*.34,eye_y-radius*.08),(cx-radius*.04,eye_y),(cx-radius*.32,eye_y+radius*.10)], 0)
        pygame.draw.polygon(surface, accent, [(cx+radius*.34,eye_y-radius*.08),(cx+radius*.04,eye_y),(cx+radius*.32,eye_y+radius*.10)], 0)
    else:
        pygame.draw.line(surface, accent, (cx-radius*.28,eye_y-radius*.05),(cx-radius*.05,eye_y+radius*.02), max(2,radius//8))
        pygame.draw.line(surface, accent, (cx+radius*.05,eye_y+radius*.02),(cx+radius*.28,eye_y-radius*.05), max(2,radius//8))
    pygame.draw.line(surface, accent, (head.left-radius*.10,cy-radius*.12),(head.left-radius*.10,cy+radius*.23), 2)
    pygame.draw.line(surface, accent, (head.right+radius*.10,cy-radius*.12),(head.right+radius*.10,cy+radius*.23), 2)
    for k in range(3):
        yy=cy+radius*.20+k*max(1,radius*.07)
        pygame.draw.line(surface, (80,120,145), (cx-radius*.13, int(yy)), (cx+radius*.13, int(yy)), 1)
    if avatar_id % 5 == 0:
        pygame.draw.polygon(surface, accent, [(cx,head.top-radius*.28),(cx-radius*.14,head.top+radius*.04),(cx+radius*.14,head.top+radius*.04)])
    elif avatar_id % 5 == 1:
        pygame.draw.line(surface, accent, (head.right,head.top+radius*.05),(head.right+radius*.22,head.top-radius*.25),2)
    elif avatar_id % 5 == 2:
        pygame.draw.circle(surface, accent, (int(cx),int(head.top+radius*.02)), max(2,radius//8), 1)
    elif avatar_id % 5 == 3:
        pygame.draw.line(surface, accent, (head.left,head.top+radius*.1),(head.left-radius*.2,head.top-radius*.18),2)
    else:
        pygame.draw.line(surface, accent, (cx-radius*.18,head.top-radius*.10),(cx+radius*.18,head.top-radius*.10),2)


def draw_module(surface, w, h, mouse_pos):
    global module_click_rects
    module_click_rects = []
    x, width = 270, w - 300
    titles = {1: "CAMPAIGN MAP", 2: "INVENTORY", 3: "INTEL ARCHIVE", 4: "ACHIEVEMENTS", 5: "SETTINGS", 6: "PROFILE & LEADERBOARD"}
    title = titles.get(selected_nav, "COMMAND DECK")
    text(surface, f"OPERATOR SYSTEMS  //  {title}", x, 96, 21, WHITE, True)
    text(surface, "IRONCLAD FIELD INTERFACE  //  LOCAL OPERATOR PROFILE", x, 126, 10, MUTED)
    active_idx = min(19, (current_level - 1) // 5)

    def card(rect, heading, lines, accent=CYAN):
        panel(surface, rect, fill=(7, 22, 39), border=BORDER, radius=10)
        draw_corner_marks(surface, rect, accent, 10)
        text(surface, heading, rect.x + 15, rect.y + 13, 12, accent, True)
        for j, line in enumerate(lines):
            text(surface, line[:84], rect.x + 15, rect.y + 39 + j * 21, 10, WHITE if j == 0 else MUTED)

    def progress_bar(rect, fraction, color=CYAN):
        pygame.draw.rect(surface, (17, 43, 58), rect, border_radius=4)
        pygame.draw.rect(surface, color, (rect.x, rect.y, int(rect.width * max(0, min(1, fraction))), rect.height), border_radius=4)

    if selected_nav == 1:                                                          
        text(surface, f"TACTICAL WORLD MAP  //  ACTIVE THEATRE: REGION {(active_idx // 5) + 1}", x, 158, 12, GREEN, True)
        map_rect = pygame.Rect(x, 185, width, min(405, h - 300))
        panel(surface, map_rect, fill=(4, 17, 31), border=BORDER, radius=12)
        for gx in range(map_rect.x + 20, map_rect.right - 10, 42):
            pygame.draw.line(surface, (12, 42, 58), (gx, map_rect.y + 12), (gx, map_rect.bottom - 12), 1)
        for gy in range(map_rect.y + 18, map_rect.bottom - 10, 34):
            pygame.draw.line(surface, (12, 42, 58), (map_rect.x + 12, gy), (map_rect.right - 12, gy), 1)
        rng = random.Random(481)
        for _ in range(75):
            sx = rng.randint(map_rect.x + 8, map_rect.right - 8)
            sy = rng.randint(map_rect.y + 8, map_rect.bottom - 8)
            pygame.draw.circle(surface, (35, 94, 115), (sx, sy), 1)
        mw, mh = map_rect.width, map_rect.height
        continents = [
            [(0.08,.25),(.15,.15),(.25,.18),(.29,.28),(.24,.36),(.22,.49),(.15,.46),(.12,.36)],
            [(.29,.51),(.36,.45),(.42,.54),(.41,.66),(.36,.82),(.31,.69)],
            [(.43,.20),(.53,.15),(.62,.22),(.66,.33),(.60,.41),(.55,.36),(.48,.40),(.42,.31)],
            [(.56,.46),(.66,.42),(.73,.49),(.76,.61),(.70,.76),(.62,.69),(.59,.57)],
            [(.73,.25),(.81,.20),(.91,.27),(.89,.39),(.82,.43),(.77,.35)],
        ]
        for poly in continents:
            pts = [(map_rect.x + int(a * mw), map_rect.y + int(b * mh)) for a,b in poly]
            pygame.draw.polygon(surface, (9, 46, 57), pts)
            pygame.draw.polygon(surface, (18, 105, 119), pts, 1)
        region_names = ["NORTH ATLANTIC // FOUNDATIONS", "EUROPE // DETECTION", "ASIA-PACIFIC // RESPONSE", "SOUTHERN FRONT // ADVANCED OPS"]
        anchors = [(0.21,.29),(0.49,.29),(0.66,.56),(0.80,.32)]
        region_colors = [CYAN, GREEN, AMBER, PURPLE]
        for region, (ax,ay) in enumerate(anchors):
            cx, cy = map_rect.x + int(ax*mw), map_rect.y + int(ay*mh)
            node_positions=[]
            for j in range(5):
                ang = math.tau*j/5 - math.pi/2
                nx, ny = cx + int(math.cos(ang)*58), cy + int(math.sin(ang)*42)
                node_positions.append((nx,ny))
                pygame.draw.line(surface, (22, 116, 143), (cx,cy), (nx,ny), 1)
            pygame.draw.circle(surface, (7,29,43), (cx,cy), 14)
            pygame.draw.circle(surface, region_colors[region], (cx,cy), 14, 2)
            text(surface, f"R{region+1}", cx-8, cy-5, 9, WHITE, True)
            for j,(nx,ny) in enumerate(node_positions):
                camp_idx=region*5+j
                cleared=sum(n in completed_levels for n in range(camp_idx*5+1,camp_idx*5+6))
                unlocked=camp_idx <= active_idx
                col=GREEN if cleared==5 else (region_colors[region] if unlocked else (54,76,91))
                radius=8 if camp_idx==active_idx else 6
                pygame.draw.circle(surface,(5,19,32),(nx,ny),radius+3)
                pygame.draw.circle(surface,col,(nx,ny),radius)
                if camp_idx==active_idx:
                    pygame.draw.circle(surface,WHITE,(nx,ny),radius+4,1)
                node_rect=pygame.Rect(nx-13,ny-13,26,26)
                module_click_rects.append((node_rect, ("campaign",camp_idx)))
                if j in (0,2,4):
                    lab=f"C{camp_idx+1:02d}"
                    text(surface,lab,nx-14,ny+11,8,col,True)
            text(surface, region_names[region], cx-90, cy+70, 8, region_colors[region], True)
        text(surface, "SOLID NODE: ACTIVE/UNLOCKED   //   GREEN NODE: CLEARED   //   DIM NODE: LOCKED", map_rect.x+16,map_rect.bottom-22,8,MUTED)
        ry=map_rect.bottom+12
        first,last=active_idx*5+1,active_idx*5+5
        cleared=sum(n in completed_levels for n in range(first,last+1))
        card(pygame.Rect(x,ry,width,65),f"ACTIVE CAMPAIGN {active_idx+1:02d} // {CAMPAIGN_THEMES[active_idx]}",[f"LEVELS {first:03d}–{last:03d}  •  {cleared}/5 CLEARED  •  NEXT OBJECTIVE: LEVEL {current_level:03d}"],GREEN)
    elif selected_nav == 2:             
        text(surface, "FIELD KIT  //  OPERATOR TOOLS AND EVIDENCE", x, 158, 12, CYAN, True)
        items = [
            ("EVIDENCE READER", f"{len(inspected_evidence)}/4 sources inspected in current operation", CYAN, "EV"),
            ("INCIDENT PLAYBOOK", "Containment • preserve telemetry • validate recovery", GREEN, "IR"),
            ("THREAT INTEL KIT", "Indicators • baselines • audit trails • scope", PURPLE, "TI"),
            ("OPERATOR XP", f"{total_xp:,} XP • {len(completed_levels)}/100 missions cleared", AMBER, "XP"),
        ]
        for i,(heading,detail,color,symbol) in enumerate(items):
            col,row=i%2,i//2
            rect=pygame.Rect(x+col*(width//2+12),190+row*178,width//2-12,154)
            card(rect,heading,[detail,"STATUS: READY FOR DEPLOYMENT"],color)
            cx,cy=rect.right-55,rect.y+72
            pygame.draw.circle(surface,(8,35,50),(cx,cy),27)
            pygame.draw.circle(surface,color,(cx,cy),27,2)
            text(surface,symbol,cx-14,cy-9,13,color,True)
                                                      
            for k in range(4):
                bh=10+((i*7+k*11)%29)
                pygame.draw.rect(surface,color,(rect.x+18+k*15,rect.bottom-28-bh,7,bh),border_radius=2)
            progress_bar(pygame.Rect(rect.x+18,rect.bottom-16,rect.width-36,5),
                         (len(inspected_evidence)/4 if i==0 else min(1,len(completed_levels)/100 if i==3 else 0.72)),color)
    elif selected_nav == 3:                 
        text(surface, "FORENSIC RECORDS  //  COMPLETED INCIDENTS", x, 158, 12, CYAN, True)
        radar_center=(x+width-95,208)
        for r in (24,40,56): pygame.draw.circle(surface,(17,87,112),radar_center,r,1)
        pygame.draw.line(surface,GREEN,(radar_center[0]-56,radar_center[1]),(radar_center[0]+56,radar_center[1]),1)
        pygame.draw.line(surface,GREEN,(radar_center[0],radar_center[1]-56),(radar_center[0],radar_center[1]+56),1)
        pygame.draw.circle(surface,GREEN,radar_center,4)
        archive_levels=sorted(completed_levels,reverse=True)[:10]
        if not archive_levels:
            card(pygame.Rect(x,190,width-125,110),"ARCHIVE AWAITING FIRST REPORT",["Complete an incident to create a local record.","No real systems or external telemetry are accessed."],AMBER)
        for i,level_no in enumerate(archive_levels):
            lv=LEVELS[level_no-1]
            col,row=i%2,i//2
            rect=pygame.Rect(x+col*(width//2+12),320+row*72,width//2-12,60)
            card(rect,f"CASE IR-{level_no:04d}  //  {lv['title']}",[f"{lv['campaign_title']}  •  {lv['entity']}  •  IOC: {lv['indicator']}"],GREEN)
            pygame.draw.circle(surface,GREEN,(rect.right-17,rect.y+18),4)
    elif selected_nav == 4:                
        total=len(completed_levels)
        text(surface,"OPERATOR COMMENDATIONS  //  PERFORMANCE RECORD",x,158,12,CYAN,True)
        achievements=[
            ("FIRST RESPONSE",total>=1,"Complete your first incident.","01",CYAN),
            ("EVIDENCE DISCIPLINE",len(inspected_evidence)==4,"Inspect all four evidence sources.","EV",GREEN),
            ("CAMPAIGN BREAKER",any(all(n in completed_levels for n in range(c*5+1,c*5+6)) for c in range(20)),"Clear all five levels in a campaign.","C5",PURPLE),
            ("VETERAN OPERATOR",total>=25,"Clear 25 missions.","25",AMBER),
            ("CENTURY DEFENDER",total>=100,"Clear all 100 missions.","100",RED),
        ]
        for i,(name,earned,desc,mark,color) in enumerate(achievements):
            col,row=i%2,i//2
            rect=pygame.Rect(x+col*(width//2+12),190+row*112,width//2-12,92)
            panel(surface,rect,fill=(8,27,42) if earned else (6,15,27),border=color if earned else BORDER,radius=10)
            cx,cy=rect.x+35,rect.y+45
            pygame.draw.circle(surface,color if earned else (40,57,69),(cx,cy),21,3)
            text(surface,mark,cx-13,cy-7,10,color if earned else MUTED,True)
            text(surface,name,rect.x+68,rect.y+16,11,WHITE if earned else MUTED,True)
            text(surface,desc,rect.x+68,rect.y+39,9,MUTED)
            text(surface,"UNLOCKED" if earned else "NOT YET EARNED",rect.x+68,rect.y+65,8,GREEN if earned else MUTED,True)
    elif selected_nav == 5:            
        text(surface,"SYSTEM CONFIGURATION  //  AUDIO AND OPERATOR DATA",x,158,12,CYAN,True)
        audio_rect=pygame.Rect(x,190,width,190)
        panel(surface,audio_rect,fill=(6,20,36),border=CYAN_DARK,radius=12)
        draw_corner_marks(surface,audio_rect,CYAN,14)
        text(surface,"AUDIO MIXER",x+20,207,13,CYAN,True)
        text(surface,"PROCEDURAL DARK TACTICAL SCORE",x+20,232,10,MUTED)
        for i in range(24):
            bh=8+int((math.sin(elapsed_total*2.3+i*0.71)+1)*17)
            bx=x+22+i*11
            pygame.draw.rect(surface,(16,61,79),(bx,265,7,36),border_radius=2)
            pygame.draw.rect(surface,CYAN if MUSIC_ENABLED else MUTED,(bx,301-bh,7,bh),border_radius=2)
        text(surface,f"MUSIC {'ON' if MUSIC_ENABLED else 'OFF'}",x+310,209,11,GREEN if MUSIC_ENABLED else MUTED,True)
        text(surface,f"VOLUME {int(MUSIC_VOLUME*200)}%",x+310,234,10,WHITE)
        music_rect=pygame.Rect(x+310,260,150,38)
        draw_button(surface,music_rect,"MUSIC: ON" if MUSIC_ENABLED else "MUSIC: OFF",mouse_pos,active=MUSIC_ENABLED)
        module_click_rects.append((music_rect,("music",None)))
        volume_down_rect = pygame.Rect(x + 310, 310, 42, 30)
        volume_up_rect = pygame.Rect(x + 418, 310, 42, 30)
        draw_button(surface, volume_down_rect, "−", mouse_pos, small=True)
        draw_button(surface, volume_up_rect, "+", mouse_pos, small=True)
        module_click_rects.extend([
            (volume_down_rect, ("volume", -0.05)),
            (volume_up_rect, ("volume", 0.05)),
        ])

        volume_bar = pygame.Rect(x + 366, 321, 43, 7)
        progress_bar(volume_bar, MUSIC_VOLUME / 0.5, CYAN)
        text(surface,"Sound effects",x+500,232,10,WHITE)
        sfx_rect=pygame.Rect(x+500,260,170,38)
        draw_button(surface,sfx_rect,"SFX: ON" if SOUND_ENABLED else "SFX: OFF",mouse_pos,active=SOUND_ENABLED)
        module_click_rects.append((sfx_rect,("sound",None)))
        text(surface,"All music is generated locally; no external audio assets required.",x+20,343,9,MUTED)
        prog=pygame.Rect(x,402,width,125)
        panel(surface,prog,fill=(7,22,39),border=BORDER,radius=10)
        text(surface,"OPERATOR PROFILE",x+18,417,12,AMBER,True)
        text(surface,f"MISSIONS CLEARED  {len(completed_levels):03d}/100",x+18,446,10,WHITE)
        text(surface,f"EXPERIENCE  {total_xp:,} XP",x+18,469,10,WHITE)
        progress_bar(pygame.Rect(x+18,493, min(380,width-36),7),len(completed_levels)/100,AMBER)
        text(surface,"RESET WILL DELETE LOCAL PROGRESSION",x+width-300,446,9,RED)
        reset_rect=pygame.Rect(x+width-220,469,190,38)
        draw_button(surface,reset_rect,"RESET PROGRESS",mouse_pos)
        module_click_rects.append((reset_rect,("reset",None)))
        if confirm_reset:
            confirm_rect=pygame.Rect(x+width-350,535,320,72)
            panel(surface,confirm_rect,fill=(40,13,24),border=RED,radius=9)
            text(surface,"CONFIRM RESET? THIS CANNOT BE UNDONE",confirm_rect.x+12,confirm_rect.y+10,9,RED,True)
            yes_rect=pygame.Rect(confirm_rect.x+12,confirm_rect.y+34,130,28)
            no_rect=pygame.Rect(confirm_rect.x+157,confirm_rect.y+34,130,28)
            draw_button(surface,yes_rect,"YES, RESET",mouse_pos)
            draw_button(surface,no_rect,"CANCEL",mouse_pos)
            module_click_rects.extend([(yes_rect,("confirm_reset",True)),(no_rect,("confirm_reset",False))])
    elif selected_nav == 6:                                                              
        global selected_avatar
        text(surface, "OPERATOR IDENTITY  //  PERSONAL PROFILE & PERFORMANCE RANK", x, 158, 12, CYAN, True)
        profile_rect = pygame.Rect(x, 185, width, 150)
        panel(surface, profile_rect, fill=(6, 20, 36), border=CYAN_DARK, radius=12)
        draw_corner_marks(surface, profile_rect, CYAN, 14)
        avatar_rect = pygame.Rect(profile_rect.x+22, profile_rect.y+22, 94, 94)
        draw_cyborg_avatar(surface, avatar_rect, selected_avatar, selected=True)
        text(surface, f"AVATAR {selected_avatar+1:02d}", profile_rect.x+27, profile_rect.y+119, 9, CYAN, True)
        text(surface, "OPERATOR USERNAME", profile_rect.x+145, profile_rect.y+23, 10, MUTED, True)
        text(surface, operator_username, profile_rect.x+145, profile_rect.y+43, 25, WHITE, True)
        text(surface, "LOCAL PROFILE  //  SAVED ON THIS DEVICE", profile_rect.x+145, profile_rect.y+75, 9, MUTED)
        edit_rect = pygame.Rect(profile_rect.x+145, profile_rect.y+96, 190, 34)
        draw_button(surface, edit_rect, "EDIT USERNAME" if not editing_username else "TYPE NAME + ENTER", mouse_pos, active=editing_username)
        module_click_rects.append((edit_rect, ("edit_username", None)))
        text(surface, f"{total_xp:,} XP", profile_rect.x+390, profile_rect.y+47, 20, GREEN, True)
        text(surface, f"{len(completed_levels)}/100 MISSIONS", profile_rect.x+520, profile_rect.y+53, 11, CYAN, True)

        text(surface, "CHOOSE YOUR CYBORG AVATAR  //  15 ORIGINAL VECTOR PORTRAITS", x, 355, 12, CYAN, True)
        grid_rect = pygame.Rect(x, 378, width, 145)
        panel(surface, grid_rect, fill=(4, 15, 28), border=BORDER, radius=10)
        tile_w = min(66, max(48, (width-55)//15))
        gap = max(5, (width - 30 - tile_w*5)//4)
        tile_w = min(68, (width-36-4*gap)//5)
        tile_h = 61
        for avatar_id in range(15):
            row, col = divmod(avatar_id, 5)
            tx = grid_rect.x+15+col*(tile_w+gap)
            ty = grid_rect.y+8+row*43
            tile = pygame.Rect(tx,ty,tile_w,39)
            accent = AVATAR_PALETTES[avatar_id][0]
            pygame.draw.rect(surface, (7,22,37), tile, border_radius=5)
            pygame.draw.rect(surface, accent if selected_avatar == avatar_id else BORDER, tile, 2 if selected_avatar == avatar_id else 1, border_radius=5)
            icon_rect = pygame.Rect(tile.x+tile.width//2-17, tile.y+2, 34, 34)
            draw_cyborg_avatar(surface, icon_rect, avatar_id, selected=(selected_avatar == avatar_id))
            text(surface, f"{avatar_id+1:02d}", tile.x+3, tile.y+tile.height-11, 8, accent, True)
            module_click_rects.append((tile, ("select_avatar", avatar_id)))
        text(surface, "CLICK ANY PORTRAIT TO EQUIP IT  //  ALL AVATARS ARE DRAWN IN CODE", x+12, grid_rect.bottom+5, 8, MUTED)

        text(surface, "LOCAL LEADERBOARD  //  RANKED BY XP", x, 548, 12, CYAN, True)
        board_rect = pygame.Rect(x, 570, width, max(100, min(240, h-625)))
        panel(surface, board_rect, fill=(5, 17, 31), border=BORDER, radius=10)
        headers = [("RANK", x+18), ("OPERATOR", x+105), ("XP", x+width-220), ("MISSIONS", x+width-112)]
        for label, hx in headers:
            text(surface, label, hx, board_rect.y+12, 9, MUTED, True)
        pygame.draw.line(surface, BORDER, (board_rect.x+15, board_rect.y+32), (board_rect.right-15, board_rect.y+32), 1)
        rows = [{"username": operator_username, "xp": total_xp, "missions": len(completed_levels), "current": True, "avatar": selected_avatar}]
        for record in leaderboard_records:
            if record.get("username", "").casefold() != operator_username.casefold():
                rows.append({"username": str(record.get("username", "Operator"))[:18], "xp": max(0, int(record.get("xp", 0))), "missions": max(0, int(record.get("missions", 0))), "current": False, "avatar": max(0,min(14,int(record.get("selected_avatar",0))))})
        rows.sort(key=lambda r: (r["xp"], r["missions"]), reverse=True)
        rows = rows[:5]
        for i, row in enumerate(rows):
            yy = board_rect.y + 39 + i*28
            if row.get("current"):
                pygame.draw.rect(surface, (8, 40, 53), (board_rect.x+10, yy-2, board_rect.width-20, 25), border_radius=4)
            rank_color = AMBER if i == 0 else (CYAN if row.get("current") else MUTED)
            text(surface, f"#{i+1:02d}", x+20, yy+3, 10, rank_color, True)
            mini = pygame.Rect(x+75, yy-1, 24, 24)
            draw_cyborg_avatar(surface, mini, row.get("avatar",0), selected=row.get("current",False))
            text(surface, row["username"] + ("  // YOU" if row.get("current") else ""), x+108, yy+4, 9, WHITE if row.get("current") else MUTED, row.get("current", False))
            text(surface, f"{row['xp']:,}", x+width-220, yy+4, 10, GREEN if row.get("current") else WHITE, True)
            text(surface, f"{row['missions']}/100", x+width-112, yy+4, 10, MUTED)
        text(surface, "LOCAL ONLY — no online accounts or network connection are used.", x, board_rect.bottom+7, 8, MUTED)
    text(surface,"IRONCLAD // SELECT A MODULE FROM THE LEFT OPERATOR MENU",x,h-35,9,CYAN_DARK)


def draw_title_screen(surface, w, h, mouse_pos, elapsed):
    center_x = w // 2
    center_y = int(h * 0.43)
    radar = pygame.Surface((min(w, 760), min(h, 620)), pygame.SRCALPHA)
    rw, rh = radar.get_size()
    rc = (rw // 2, rh // 2)
    pulse = int(5 * (1 + math.sin(elapsed * 1.6)))
    for radius in (105, 155, 210, 265):
        pygame.draw.circle(radar, (30, 190, 225, 24), rc, radius + pulse, 1)
    for angle_step in range(0, 360, 30):
        angle = math.radians(angle_step + elapsed * 7)
        end = (int(rc[0] + math.cos(angle) * 265), int(rc[1] + math.sin(angle) * 265))
        pygame.draw.line(radar, (25, 135, 170, 25), rc, end, 1)
    surface.blit(radar, radar.get_rect(center=(center_x, center_y)))
    badge_y = center_y - 150
    hex_size = 38 + int(2 * math.sin(elapsed * 2.2))
    points = []
    for i in range(6):
        angle = math.radians(60 * i - 30)
        points.append((center_x + math.cos(angle) * hex_size, badge_y + math.sin(angle) * hex_size))
    pygame.draw.polygon(surface, (7, 28, 45), points)
    pygame.draw.polygon(surface, CYAN, points, 2)
    pygame.draw.line(surface, CYAN, (center_x - 12, badge_y - 12), (center_x + 12, badge_y + 12), 3)
    pygame.draw.line(surface, CYAN, (center_x + 12, badge_y - 12), (center_x - 12, badge_y + 12), 3)
    title = "IRONCLAD"
    title_img = font(max(48, min(82, w // 15)), True).render(title, True, WHITE)
    title_rect = title_img.get_rect(center=(center_x, center_y - 48))
    glow_img = font(max(48, min(82, w // 15)), True).render(title, True, CYAN_DARK)
    surface.blit(glow_img, title_rect.move(3, 3))
    surface.blit(title_img, title_rect)
    tagline = "DEFEND  •  INVESTIGATE  •  RESPOND  •  LEARN"
    tagline_img = font(16, True).render(tagline, True, CYAN)
    surface.blit(tagline_img, tagline_img.get_rect(center=(center_x, center_y + 8)))
    description = "A CYBERSECURITY INCIDENT RESPONSE RPG"
    desc_img = font(13).render(description, True, MUTED)
    surface.blit(desc_img, desc_img.get_rect(center=(center_x, center_y + 39)))
    pillars = [("01", "INVESTIGATE", "Read the evidence"),
               ("02", "MAKE DECISIONS", "Choose your response"),
               ("03", "LEARN", "Understand the why")]
    card_w, card_h, gap = min(220, (w - 100) // 3), 68, 14
    total_w = card_w * 3 + gap * 2
    start_x = center_x - total_w // 2
    card_y = center_y + 78
    for i, (num, heading, subheading) in enumerate(pillars):
        rect = pygame.Rect(start_x + i * (card_w + gap), card_y, card_w, card_h)
        panel(surface, rect, fill=(7, 21, 37), border=BORDER, radius=8)
        text(surface, num, rect.x + 12, rect.y + 11, 10, CYAN, True)
        text(surface, heading, rect.x + 43, rect.y + 10, 11, WHITE, True)
        text(surface, subheading, rect.x + 43, rect.y + 34, 10, MUTED)

    button_w, button_h = 250, 54
    start_rect = pygame.Rect(center_x - button_w // 2, card_y + 100, button_w, button_h)
    hovered = start_rect.collidepoint(mouse_pos)
    if hovered:
        glow = pygame.Surface((button_w + 40, button_h + 40), pygame.SRCALPHA)
        pygame.draw.rect(glow, (45, 225, 255, 30), glow.get_rect(), border_radius=12)
        surface.blit(glow, (start_rect.x - 20, start_rect.y - 20))
    draw_button(surface, start_rect, "START MISSION  >", mouse_pos, active=True)

    hint = "PRESS ENTER OR CLICK START"
    hint_img = font(10, True).render(hint, True, MUTED)
    surface.blit(hint_img, hint_img.get_rect(center=(center_x, start_rect.bottom + 23)))
    text(surface, "IRONCLAD TRAINING SIMULATION  //  100 LEVEL CAMPAIGN", 24, h - 27, 9, CYAN_DARK)
    status = "SYSTEM READY  ●"
    status_img = font(9, True).render(status, True, GREEN)
    surface.blit(status_img, (w - status_img.get_width() - 24, h - 27))
    return start_rect


def draw_cinematic(surface, w, h, elapsed):
    t = elapsed
    surface.fill((2, 5, 13))
    if t < 5.5:
        progress = min(1.0, t / 5.5)
        for i in range(115):
            x = (i * 97 + int(t * (35 + i % 5) * 4)) % max(w, 1)
            y = (i * 53 + int(t * (100 + i % 7) * 3)) % max(h, 1)
            pygame.draw.line(surface, (18, 65, 88), (x, y), (x - 5, y + 13), 1)
        ground = int(h * 0.78)
        building_width = max(35, w // 18)
        for i, x in enumerate(range(-10, w + building_width, building_width)):
            bh = int(h * (0.18 + ((i * 37) % 47) / 100))
            rect = pygame.Rect(x, ground - bh, building_width - 5, bh)
            pygame.draw.rect(surface, (7, 17, 31), rect)
            pygame.draw.line(surface, (18, 67, 88), rect.topleft, (rect.right, rect.top), 1)
            for wx in range(rect.x + 7, rect.right - 5, 13):
                for wy in range(rect.y + 10, rect.bottom - 8, 17):
                    flicker = (i * 11 + wx + int(t * 8)) % 9
                    if flicker < 3 and t < 3.7:
                        pygame.draw.rect(surface, (35, 135, 155), (wx, wy, 4, 7))
        if t > 2.5:
            darkness = pygame.Surface((w, h), pygame.SRCALPHA)
            alpha = min(205, int((t - 2.5) * 90))
            darkness.fill((0, 0, 5, alpha))
            surface.blit(darkness, (0, 0))

        caption = "SYDNEY  //  " + datetime.datetime.now().astimezone().strftime("%I:%M:%S %p")
        sub = "MULTIPLE SYSTEMS OFFLINE  //  LOCAL SYSTEM TIME"
        text(surface, caption, 52, int(h * .69), 15, CYAN, True)
        text(surface, sub, 52, int(h * .73), 25, WHITE, True)
        if t > 4.0:
            text(surface, "CONNECTION LOST", 52, int(h * .79), 12, RED, True)
    elif t < 11.5:
        local = t - 5.5
        center = (w // 2, int(h * .43))
        for i in range(15):
            x = int(i * w / 14)
            pygame.draw.line(surface, (12, 65, 88), center, (x, h), 1)
        for i in range(1, 10):
            y = int(h * .43 + i * i * h * .006)
            if y < h:
                pygame.draw.line(surface, (12, 65, 88), (0, y), (w, y), 1)
        console = pygame.Rect(int(w * .08), int(h * .17), int(w * .84), int(h * .56))
        panel(surface, console, fill=(5, 15, 29), border=CYAN_DARK, radius=8)
        text(surface, "SOC // LIVE INCIDENT FEED", console.x + 25, console.y + 20, 13, CYAN, True)
        rows = [
            ("02:13:04", "AUTHENTICATION ANOMALY", "MEDIUM", AMBER),
            ("02:13:09", "UNUSUAL OUTBOUND TRAFFIC", "HIGH", RED),
            ("02:13:12", "PRIVILEGED ACCOUNT ACTIVITY", "CRITICAL", RED),
            ("02:13:17", "MULTIPLE HOSTS UNREACHABLE", "CRITICAL", RED),
            ("02:13:21", "INCIDENT CORRELATION STARTED", "ACTIVE", GREEN),
        ]
        for i, (stamp, message, severity, color) in enumerate(rows):
            y = console.y + 68 + i * 54
            row_rect = pygame.Rect(console.x + 18, y, console.width - 36, 42)
            pygame.draw.rect(surface, (8, 27, 43), row_rect, border_radius=4)
            pygame.draw.rect(surface, color, (row_rect.x, row_rect.y, 3, row_rect.height))
            text(surface, stamp, row_rect.x + 12, row_rect.y + 13, 10, MUTED)
            text(surface, message, row_rect.x + 105, row_rect.y + 12, 12, WHITE, True)
            if i <= min(4, int(local * 1.1)):
                text(surface, severity, row_rect.right - 92, row_rect.y + 12, 10, color, True)
        pulse = int(35 + 30 * (0.5 + 0.5 * math.sin(local * 8)))
        warning = pygame.Surface((w, h), pygame.SRCALPHA)
        pygame.draw.rect(warning, (255, 25, 60, pulse), (0, 0, w, h), 5)
        surface.blit(warning, (0, 0))
        text(surface, "THIS IS NOT A DRILL.", 52, int(h * .82), 24, RED, True)
    elif t < 17.5:
        local = t - 11.5
        center = (w // 2, int(h * .44))
        for i in range(7):
            radius = int((local * 125 + i * 58) % max(w, h))
            if radius > 0:
                alpha = max(20, 180 - radius // 3)
                ring = pygame.Surface((w, h), pygame.SRCALPHA)
                pygame.draw.circle(ring, (35, 220, 255, alpha), center, radius, 2)
                surface.blit(ring, (0, 0))
        nodes = []
        for i in range(18):
            angle = i * math.tau / 18 + local * 0.12
            radius = min(w, h) * (0.12 + 0.23 * ((i % 3) / 2))
            nx = int(center[0] + math.cos(angle) * radius)
            ny = int(center[1] + math.sin(angle) * radius)
            nodes.append((nx, ny))
        for i, node in enumerate(nodes):
            pygame.draw.line(surface, (15, 115, 155), center, node, 1)
            pygame.draw.circle(surface, CYAN, node, 3 + (i % 3 == 0))
        pygame.draw.circle(surface, (8, 36, 57), center, 53)
        pygame.draw.circle(surface, CYAN, center, 53, 2)
        points = []
        for i in range(6):
            angle = math.radians(60 * i - 30)
            points.append((center[0] + math.cos(angle) * 32, center[1] + math.sin(angle) * 32))
        pygame.draw.polygon(surface, CYAN, points, 3)
        text(surface, "DEFENSIVE PROTOCOL", 52, int(h * .76), 13, CYAN, True)
        text(surface, "IRONCLAD SYSTEMS ONLINE", 52, int(h * .80), 24, WHITE, True)
        text(surface, "CONTAINMENT NETWORK ESTABLISHED", 52, int(h * .85), 11, GREEN)
    else:
        local = t - 17.5
        center_x, center_y = w // 2, int(h * .43)
        sweep_x = int((local * 1.7 % 1.4 - 0.2) * w)
        glow = pygame.Surface((w, h), pygame.SRCALPHA)
        pygame.draw.line(glow, (35, 220, 255, 45), (sweep_x, 0), (sweep_x - 100, h), 30)
        surface.blit(glow, (0, 0))
        for radius in (75, 110, 145, 180):
            pygame.draw.circle(surface, (20, 105, 140), (center_x, center_y - 65), radius, 1)
        for i in range(8):
            angle = local * 1.1 + i * math.tau / 8
            end = (int(center_x + math.cos(angle) * 175), int(center_y - 65 + math.sin(angle) * 175))
            pygame.draw.line(surface, (20, 110, 145), (center_x, center_y - 65), end, 1)
        title_size = max(48, min(94, w // 13))
        title_img = font(title_size, True).render("IRONCLAD", True, WHITE)
        title_rect = title_img.get_rect(center=(center_x, center_y - 55))
        surface.blit(font(title_size, True).render("IRONCLAD", True, CYAN_DARK), title_rect.move(4, 4))
        surface.blit(title_img, title_rect)
        if int(local * 9) % 7 in (0, 1):
            glitch_y = title_rect.y + int((local * 83) % max(1, title_rect.height))
            glitch_h = 2 + int((local * 11) % 5)
            glitch_rect = pygame.Rect(title_rect.x - 18, glitch_y, title_rect.width + 36, glitch_h)
            glitch_surface = pygame.Surface((glitch_rect.width, glitch_rect.height), pygame.SRCALPHA)
            glitch_surface.fill((45, 225, 255, 115))
            surface.blit(glitch_surface, glitch_rect.topleft)
            pygame.draw.line(surface, RED, (glitch_rect.x + 12, glitch_y + glitch_h),
                             (glitch_rect.right - 8, glitch_y + glitch_h), 1)
        scan_y = int((elapsed * 95) % max(1, h))
        scan_surface = pygame.Surface((w, 8), pygame.SRCALPHA)
        scan_surface.fill((45, 225, 255, 14))
        surface.blit(scan_surface, (0, scan_y))
        tagline = font(16, True).render("DEFEND  •  INVESTIGATE  •  RESPOND  •  LEARN", True, CYAN)
        surface.blit(tagline, tagline.get_rect(center=(center_x, center_y + 8)))
        quote = font(15).render("ONE NETWORK. ONE INCIDENT. EVERY DECISION MATTERS.", True, MUTED)
        surface.blit(quote, quote.get_rect(center=(center_x, center_y + 45)))
        if local > 1.2:
            prompt = font(12, True).render("PRESS ENTER OR SPACE TO ENTER THE SOC", True, GREEN)
            surface.blit(prompt, prompt.get_rect(center=(center_x, int(h * .78))))
    hint = font(10, True).render("ESC  //  SKIP CINEMATIC", True, (105, 145, 165))
    surface.blit(hint, (w - hint.get_width() - 24, h - 27))


def main():
    global screen, fullscreen, selected_campaign, selected_nav, toast_message, toast_until, elapsed_total
    global mission_open, mission_debrief, mission_response, mission_xp, total_xp
    global inspected_evidence, selected_evidence, mission_completed, current_level, completed_levels
    global sound_setting, confirm_reset, selected_nav, total_xp, mission_response, mission_xp, SOUND_ENABLED, MUSIC_ENABLED, MUSIC_VOLUME, operator_username, editing_username, leaderboard_records, selected_avatar

    running = True
    title_screen = True
    cinematic_active = False
    cinematic_elapsed = 0.0
    briefing_open = False
    current_briefing = 0
    nav_rects = []
    campaign_rects = []
    launch_rect = pygame.Rect(0, 0, 0, 0)
    start_rect = close_rect = pygame.Rect(0, 0, 0, 0)
    evidence_rects = []
    response_rects = []
    debrief_replay_rect = debrief_dashboard_rect = pygame.Rect(0, 0, 0, 0)
    confirm_reset = False

    while running:
        dt = min(clock.tick(FPS) / 1000.0, 0.05)
        elapsed_total += dt
        w, h = screen.get_size()
        mouse_pos = pygame.mouse.get_pos()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.TEXTINPUT and editing_username:
                cleaned = "".join(ch for ch in event.text if ch.isalnum() or ch in " _-")
                if cleaned:
                    operator_username = (operator_username + cleaned)[:18]
            elif event.type == pygame.KEYDOWN:
                if editing_username:
                    if event.key == pygame.K_BACKSPACE:
                        operator_username = operator_username[:-1]
                    elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                        operator_username = operator_username.strip()[:18] or "Operator001"
                        editing_username = False
                        save_progress()
                    elif event.key == pygame.K_ESCAPE:
                        editing_username = False
                elif event.key == pygame.K_ESCAPE:
                    if cinematic_active:
                        cinematic_active = False
                        title_screen = False
                    elif mission_debrief:
                        mission_debrief = False
                        mission_open = False
                    elif mission_open:
                        mission_open = False
                    elif briefing_open:
                        briefing_open = False
                    elif title_screen:
                        running = False
                    else:
                        title_screen = True
                elif event.key in (pygame.K_RETURN, pygame.K_SPACE) and cinematic_active:
                    cinematic_active = False
                    title_screen = False
                elif event.key == pygame.K_RETURN and title_screen:
                    title_screen = False
                    cinematic_active = True
                    cinematic_elapsed = 0.0
                    play_sound("alert")
                elif event.key == pygame.K_F11:
                    fullscreen = not fullscreen
                    if fullscreen:
                        screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
                    else:
                        screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)

            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                play_sound("click")
                if title_screen:
                    if title_start_rect.collidepoint(event.pos):
                        title_screen = False
                        cinematic_active = True
                        cinematic_elapsed = 0.0
                elif briefing_open:
                    if close_rect.collidepoint(event.pos):
                        briefing_open = False
                    elif start_rect.collidepoint(event.pos):
                        active_campaign_index = min((current_level - 1) // 5, len(CAMPAIGNS) - 1)
                        if current_briefing == active_campaign_index:
                            briefing_open = False
                            mission_open = True
                            mission_debrief = False
                            mission_response = None
                            mission_xp = 0
                            inspected_evidence = set()
                            selected_evidence = 0
                        elif current_briefing < active_campaign_index:
                            briefing_open = False
                            toast_message = "CAMPAIGN ALREADY CLEARED // SELECT THE ACTIVE CAMPAIGN"
                            toast_until = elapsed_total + 3.0
                        else:
                            briefing_open = False
                            toast_message = "CAMPAIGN LOCKED // CLEAR FIVE LEVELS TO ADVANCE"
                            toast_until = elapsed_total + 3.0
                elif mission_debrief:
                    if debrief_replay_rect.collidepoint(event.pos):
                        mission_debrief = False
                        mission_open = True
                        mission_response = None
                        mission_xp = 0
                        inspected_evidence = set()
                        selected_evidence = 0
                    elif debrief_dashboard_rect.collidepoint(event.pos):
                        mission_debrief = False
                        mission_open = False
                        if current_level in completed_levels and current_level < 100:
                            previous_campaign = (current_level - 1) // 5
                            current_level += 1
                            selected_campaign = min((current_level - 1) // 5, len(CAMPAIGNS) - 1)
                            if (current_level - 1) // 5 > previous_campaign:
                                toast_message = f"CAMPAIGN {selected_campaign + 1:02d} UNLOCKED // {CAMPAIGNS[selected_campaign][1]}"
                            else:
                                toast_message = f"LEVEL {current_level:03d} UNLOCKED // {LEVELS[current_level - 1]['title'].upper()}"
                            play_sound("success")
                        elif current_level >= 100 and current_level in completed_levels:
                            toast_message = "IRONCLAD // ALL 100 LEVELS COMPLETE"
                            play_sound("success")
                        else:
                            toast_message = "PROGRESS SAVED // RETURNING TO SOC"
                        save_progress()
                        toast_until = elapsed_total + 3.0
                elif mission_open:
                    handled = False
                    for i, rect in enumerate(evidence_rects):
                        if rect.collidepoint(event.pos):
                            selected_evidence = i
                            if i not in inspected_evidence:
                                inspected_evidence.add(i)
                                mission_xp += 25
                                if len(inspected_evidence) == 4:
                                    mission_xp += 50
                            handled = True
                            break
                    if not handled:
                        for rect, action in response_rects:
                            if rect.collidepoint(event.pos):
                                mission_response = action
                                if action == recommended_action_for_level(current_level):
                                    mission_xp += 100
                                elif action == "broad":
                                    mission_xp += 10
                                elif action not in ("dismiss", "monitor"):
                                    mission_xp += 25
                                                                                                        
                                if current_level not in completed_levels:
                                    total_xp += mission_xp
                                    completed_levels.add(current_level)
                                    if current_level == 1:
                                        mission_completed = True
                                    save_progress()
                                play_sound("success" if action == recommended_action_for_level(current_level) else "alert")
                                mission_debrief = True
                                mission_open = False
                                handled = True
                                break
                else:
                    nav_clicked = False
                    for i, rect in enumerate(nav_rects):
                        if rect.collidepoint(event.pos):
                            selected_nav = i
                            nav_clicked = True
                            if i == 0:
                                confirm_reset = False
                            break

                    if not nav_clicked and selected_nav != 0:
                        for rect, action_data in module_click_rects:
                            if rect.collidepoint(event.pos):
                                action, value = action_data
                                if action == "campaign":
                                    selected_campaign = value
                                    current_briefing = value
                                    briefing_open = True
                                    selected_nav = 0
                                elif action == "sound":
                                    SOUND_ENABLED = not SOUND_ENABLED
                                    if SOUND_ENABLED and not SOUNDS:
                                        init_audio()
                                    toast_message = f"SOUND EFFECTS {'ON' if SOUND_ENABLED else 'OFF'}"
                                    toast_until = elapsed_total + 2.0
                                elif action == "music":
                                    set_music_enabled(not MUSIC_ENABLED)
                                    toast_message = f"MUSIC {'ON' if MUSIC_ENABLED else 'OFF'}"
                                    toast_until = elapsed_total + 2.0
                                elif action == "volume":
                                    set_music_volume(MUSIC_VOLUME + value)
                                    toast_message = f"MUSIC VOLUME {int(MUSIC_VOLUME*200)}%"
                                    toast_until = elapsed_total + 2.0
                                elif action == "select_avatar":
                                    selected_avatar = max(0, min(14, int(value)))
                                    save_progress()
                                    toast_message = f"AVATAR {selected_avatar+1:02d} EQUIPPED"
                                    toast_until = elapsed_total + 1.8
                                elif action == "edit_username":
                                    editing_username = not editing_username
                                    if editing_username:
                                        operator_username = ""
                                        pygame.key.start_text_input()
                                    else:
                                        operator_username = operator_username.strip()[:18] or "Operator001"
                                        pygame.key.stop_text_input()
                                        save_progress()
                                elif action == "reset":
                                    confirm_reset = True
                                elif action == "confirm_reset" and value:
                                    total_xp = 0
                                    completed_levels.clear()
                                    current_level = 1
                                    leaderboard_records = []
                                    mission_completed = False
                                    inspected_evidence = set()
                                    confirm_reset = False

                                    try:
                                        if SAVE_FILE.exists():
                                            SAVE_FILE.unlink()
                                    except OSError:
                                                                                                               
                                        pass
                                    selected_campaign = 0
                                    toast_message = "PROGRESSION RESET // NEW OPERATOR PROFILE"
                                    toast_until = elapsed_total + 3.0
                                elif action == "confirm_reset":
                                    confirm_reset = False
                                break
                    if not nav_clicked and selected_nav == 0:
                        for i, rect in enumerate(campaign_rects):
                            if rect.collidepoint(event.pos):
                                selected_campaign = i
                                current_briefing = i
                                briefing_open = True
                                break
                        if launch_rect.collidepoint(event.pos):
                            current_briefing = 0
                            briefing_open = True

        draw_background(screen, elapsed_total, dt)
        if cinematic_active:
            cinematic_elapsed += dt
            draw_cinematic(screen, w, h, cinematic_elapsed)
            if cinematic_elapsed >= 23.0:
                cinematic_active = False
                title_screen = False
        elif title_screen:
            title_start_rect = draw_title_screen(screen, w, h, mouse_pos, elapsed_total)
        else:
            nav_rects = draw_sidebar(screen, w, h, mouse_pos)
            draw_topbar(screen, w)
            if mission_open:
                evidence_rects, response_rects = draw_level1(screen, w, h, mouse_pos)
            elif selected_nav != 0:
                draw_module(screen, w, h, mouse_pos)
            else:
                campaign_rects, launch_rect = draw_dashboard(screen, w, h, mouse_pos, elapsed_total)
                if briefing_open:
                    start_rect, close_rect = draw_briefing(screen, w, h, current_briefing, mouse_pos)
            if mission_debrief:
                debrief_replay_rect, debrief_dashboard_rect = draw_level1_debrief(screen, w, h, mouse_pos)

        if elapsed_total < toast_until:
            toast_rect = pygame.Rect(w // 2 - 235, h - 62, 470, 35)
            panel(screen, toast_rect, fill=(8, 34, 48), border=CYAN_DARK, radius=7)
            toast_img = font(11, True).render(toast_message, True, CYAN)
            screen.blit(toast_img, toast_img.get_rect(center=toast_rect.center))

        pygame.display.flip()

    if MUSIC_CHANNEL:
        MUSIC_CHANNEL.stop()
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
