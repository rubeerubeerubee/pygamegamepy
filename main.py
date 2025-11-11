import pygame, sys, os, json, random, math
 
from dataclasses import dataclass, field
from typing import List, Dict, Any
from copy import deepcopy
try:
    from gtts import gTTS
except ImportError:
    gTTS = None
    print("Warning: gTTS (Google Text-to-Speech) is not installed. Voice features will be disabled.")

# ---------- การตั้งค่าเบื้องต้น ----------
pygame.init()
WIDTH, HEIGHT = 1100,800
screen = pygame.display.set_mode((WIDTH,HEIGHT))
pygame.display.set_caption('Duolinger')
clock = pygame.time.Clock()
 
#โหลด font
def load_thai_font(preferred_path="assets/fonts/Itim-Regular.ttf", size=28, bold=False):
    try:
        if os.path.exists(preferred_path,):
            return pygame.font.Font(preferred_path, size)
    except Exception:
        pass
    try:
        return pygame.font.SysFont("tahoma", size, bold=bold)   
    except Exception:
        return pygame.font.SysFont(None, size, bold=bold)

FONT = load_thai_font(size=28)
BIG  = load_thai_font(size=36, bold=True)
MED  = load_thai_font(size=32, bold=True) 

# ---------- ข้อความ ----------
def draw_text(text, x, y, color=(41, 68, 99), center=False, font=FONT):
    surf = font.render(text, True, color)
    rect = surf.get_rect()
    if center:
        rect.center = (x, y)
    else:
        rect.topleft = (x, y)
    screen.blit(surf, rect)

def draw_wrapped_text(text, x, y, max_width, font=FONT, color=(41,68,99), line_spacing=6, align='center'):
    #สร้างบรรทัดให้พอดีกับความกว้าง
    words = str(text).split()
    if not words:
        return
    lines = []
    cur = words[0]
    for w in words[1:]:
        test = cur + ' ' + w
        if font.size(test)[0] <= max_width:
            cur = test
        else:
            lines.append(cur)
            cur = w
    lines.append(cur)

    # เรนเดอร์บรรทัดและจัดแนวนอนโดยอิงตำแหน่ง x
    fh = font.get_linesize()
    for i, line in enumerate(lines):
        surf = font.render(line, True, color)
        rect = surf.get_rect()
        if align == 'center':
            rect.centerx = x
        elif align == 'left':
            rect.x = x
        else:
            rect.centerx = x
        rect.y = y + i * (fh + line_spacing)
        screen.blit(surf, rect)


def draw_raised_button(text, rect, mouse, clicked, *,
                       enabled=True,
                        color=(60, 150, 255),
                        text_color=(255, 255, 255), 
                        radius=20, 
                        font=None,
                        active=False,
                        active_border=(80, 170, 255),
                        active_tint=1.06):
    if font is None: 
        font = FONT
    # สถานะ
    hover   = rect.collidepoint(mouse) and enabled # ชี้อยู่บนปุ่ม
    held    = hover and pygame.mouse.get_pressed()[0]  # กดยุบลง
    offset  = 2 if held else (1 if hover else 0) # เลื่อนปุ่มลง
    # สีพื้นตามสถานะ
    if not enabled:
        base = (160,160,160) # เทาเมื่อปุ่มปิด
    else:
        base = color
        if active: # เลือกไว้
            base = tuple(min(255, int(c * active_tint)) for c in base)  # สว่างขึ้นนิด
        if hover: # ชี้อยู่
            base = (max(0, int(base[0]*0.95)),
                    max(0, int(base[1]*0.95)),
                    max(0, int(base[2]*0.95)))
    # เงาด้านล่าง (ยกนูน)
    shadow = rect.move(0, 3)
    pygame.draw.rect(screen, (87, 96, 111), shadow, border_radius=radius)
    # ตัวปุ่ม (เลื่อนลงเล็กน้อยตอนกด/ชี้)
    btn = rect.move(0, offset)
    pygame.draw.rect(screen, base, btn, border_radius=radius)
     # กรอบ/ไฮไลต์
    if active:
        pygame.draw.rect(screen, active_border, btn, width=3, border_radius=radius)  # กรอบหนาเมื่อ active
    else:
        pygame.draw.rect(screen, (255,255,255), btn, width=1, border_radius=radius)  # กรอบบางปกติ
    # ข้อความกลางปุ่ม (ขยับลงตาม offset)
    draw_text(text, btn.centerx, btn.centery, color=text_color, center=True, font=font)
    # คลิกสำเร็จ: ใช้สัญญาณ just_clicked ของน้ำ เพื่อกันยิงซ้ำทุกเฟรม
    return enabled and clicked and hover
# --------กรอบ
def draw_screen_frame(pad=28, *, color=(120,150,180), width=3, radius=24, shadow=True):
    # พื้นที่กรอบด้านใน (ห่างขอบจอด้วย padding)
    rect = pygame.Rect(pad, pad, WIDTH - pad*2, HEIGHT - pad*2)
    # เงานุ่ม ๆ รอบกรอบ (ไม่บังคับ)
    if shadow:
        sh = pygame.Surface((rect.w+16, rect.h+16), pygame.SRCALPHA)
        pygame.draw.rect(sh, (255, 255, 255,95), sh.get_rect(), border_radius=radius+8)
        screen.blit(sh, (rect.x-8, rect.y-4))  # เลื่อนลงนิดให้ดูยก

    # กรอบหลัก
    pygame.draw.rect(screen, color, rect, width=width, border_radius=radius)
    # เส้นไฮไลต์ด้านในบาง ๆ ให้ดูใสขึ้น
    pygame.draw.rect(screen, (255,255,255,70), rect.inflate(-6,-6), width=1, border_radius=max(0, radius-4))

# ---------- สุ่มข้อ ----------
def randomize_lesson(lesson, k=None, seed=None):
    if seed is not None:
        random.seed(seed)
    data = deepcopy(lesson)
    random.shuffle(data)
    if k is not None:
        data = data[:k]
    for q in data:
        if 'choices' in q:
            random.shuffle(q['choices'])
            q['answer_index']=q['choices'].index(q['answer'])
    return data
# ---------- เลือกข้อที่ยังไม่เคยเจอ (ยังไม่ได้เอาไปใช้ y-y) ----------
def pick_without_seen(lesson, seen_ids, k):
    unseen = [q for q in lesson if q['id'] not in seen_ids]
    if len(unseen) < k:
        unseen = list(lesson)
        seen_ids.clear()
    random.shuffle(unseen)
    chosen = unseen[:k]
    seen_ids.update(q["id"] for q in chosen)
    return chosen
# ---------- เรียกอ่านไฟล์โจทย์  ----------
def load_lessons_json(path: str):
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, list):
            raise ValueError(f"lessons file {path} must be a JSON list")
        return data
    except FileNotFoundError:
        print(f"Warning: lessons file not found: {path}; using empty list")
        return []
    except json.JSONDecodeError as e:
        print(f"Warning: JSON decode error in {path}: {e}; using empty list")
        return []
    except Exception as e:
        print(f"Warning: failed to load lessons from {path}: {e}; using empty list")
        return []
LESSON_choices = load_lessons_json("assets/lessons/choices.json")
LESSON_sentence = load_lessons_json("assets/lessons/sentence.json")
LESSON_construct = load_lessons_json("assets/lessons/construct.json")

# ตรวจสอบให้แต่ละข้อมี id คงที่ (ใช้ติดตามการใช้งาน/ความไม่ซ้ำ)
def _ensure_ids(lessons, prefix: str):
    for i, q in enumerate(lessons):
        if not isinstance(q, dict):
            continue
        if 'id' not in q:
            q['id'] = f"{prefix}-{i}"

_ensure_ids(LESSON_choices, 'choice')
_ensure_ids(LESSON_sentence, 'sentence')
_ensure_ids(LESSON_construct, 'construct')
# ---------- กลไกเกม ----------

@dataclass
class Progress:
    score: int = 0
    streak: int = 0
    lives:  int = 5
    current_index: int = 0
    highest_streak: int = 0

    def correct(self):
        self.score += 10
        self.streak += 1
        if self.streak > self.highest_streak:
            self.highest_streak = self.streak

    def wrong(self):
        self.streak = 0
        self.lives  -= 1

    def total_score(self):
        return round(self.score + (self.lives * 5) + (self.highest_streak * 3.7))
    
@dataclass
class QuestionEngine:
    items: List[Dict[str, Any]]
    progress: Progress = field(default_factory=Progress)
    
    def current(self):
        if self.progress.current_index < len(self.items):
            return self.items[self.progress.current_index]
        return None

    # ตรวจคำตอบ
    def evaluate_choice(self, idx):
        q = self.current()
        if q and q.get("type") == "choice":
            good = (q["choices"][idx] == q["answer"])
            if good: self.progress.correct()
            else:    self.progress.wrong()
            return good
    # ตรวจคำตอบ (ประโยค)
    def evaluate_text(self, sentence):
        q = self.current()
        if q and q.get("type") == "sentence":
            good = (sentence.strip().lower() == q["answer_text"].lower())
            if good: self.progress.correct()
            else:    self.progress.wrong()
            return good
    # ไปข้อถัดไป
    def advance(self): 
        self.progress.current_index += 1
    #ขก.เปลี่ยนชื่อฟังชัน
    def answer_choice(self, idx): return self.evaluate_choice(idx)
    def answer_text(self, sentence): return self.evaluate_text(sentence)
    #จบเกม
    def done(self):
        return self.progress.current_index >= len(self.items) or self.progress.lives <= 0

LOBBY, MENU, QUIZ, SENTENCE, CONSTRUCT, RESULT = 'LOBBY','MENU','QUIZ','SENTENCE','CONSTRUCT','RESULT'

class Game:
    def __init__(self):
        self.state = LOBBY
        self.engine = QuestionEngine(LESSON_choices)
        self.feedback_timer = 0
        self.feedback_color = (0,0,0)
        self.text_buffer = ""
        self.just_clicked = False
        self.mouse_pos = (0, 0)
        self.heart_img = pygame.transform.smoothscale(pygame.image.load("assets/ui/heart.png").convert_alpha(), (18, 18))
        pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=4096)
        pygame.mixer.music.set_volume(1.0)
        self.voice_dir = "assets/voice"
        os.makedirs(self.voice_dir, exist_ok=True)
        self.selected_index = None
        os.makedirs(self.voice_dir, exist_ok=True)
        self.mode_review = False   # เมื่อเป็น True หมายถึงเพิ่งตรวจเสร็จ กำลังรอให้กด "ไปต่อ"
        self.last_good = None
        self.chosen_words = []  # สำหรับโหมดสร้างประโยค
        self.current_construct = []  # คำที่ห้เลือก
        self.sentence_focused = False
        self.seen_sentence_ids = set()
        self.seen_construct_ids = set()
        # ความถี่การกระพริบของเคอร์เซอร์เมื่อพิมพ์ 
        self.cursor_blink_ms = 500
        # โหลดเสียงต่างๆ
        self.sounds = {
                        "correct": pygame.mixer.Sound("assets/sounds/correct.mp3"),
                        "wrong": pygame.mixer.Sound("assets/sounds/wrong.mp3"),
                        "ui": pygame.mixer.Sound("assets/sounds/ui_sound.mp3"),
                        "cilck": pygame.mixer.Sound("assets/sounds/game_start.mp3"),
                        "lobby": pygame.mixer.Sound("assets/sounds/lobby.mp3"),
                        "result": pygame.mixer.Sound("assets/sounds/result.mp3"),
                    }
        self.bg_lobby = pygame.image.load("assets/background/bg_lobby.png").convert_alpha() # พื้นหลัง
        self.bg_lobby = pygame.transform.smoothscale(self.bg_lobby, (WIDTH, HEIGHT))
        self.bg = pygame.image.load("assets/background/bg1.png").convert_alpha()
        self.bg = pygame.transform.smoothscale(self.bg, (WIDTH, HEIGHT))
        self.bg2 = pygame.image.load("assets/background/bg2.png").convert_alpha()
        self.bg2 = pygame.transform.smoothscale(self.bg2, (WIDTH, HEIGHT))

    #สร้างเสียงเก็บไว้ใน voices และเรียกอ่านเสียง
    def speak_word(self, word: str, lang='en'):
        safe = "".join(c for c in word.strip().lower() if c.isalnum() or c in ("_", "-")) #เปลี่ยนตัวแปลกๆให้เป็น " "
        if not safe:
            safe = "tts"  #ถ้ามันแปกจนอ่านไม่ได้
        path = os.path.join(self.voice_dir, f"{safe}.mp3")
        if not os.path.exists(path): #ถ้ายังไม่ม่มีไฟล์ให้สร้างและเก็บไว้ตาม path
            try:
                tts = gTTS(word, lang=lang)
                tts.save(path)
            except Exception as e:
                print("TTS error:", e)
                return False
        try:
            pygame.mixer.music.stop()
            pygame.mixer.music.load(path)
            pygame.mixer.music.play()
            return True
        except Exception as e:
            print("play error:", e)
            return False
    #feedback ตอบผิดถูก
    def draw_feedback_bar(self):
        if not self.mode_review:
            return
        q = self.engine.current()
        correct = self.last_good

        bar_h = 110
        bar_rect = pygame.Rect(0, HEIGHT - bar_h, WIDTH, bar_h)
        color = (92, 201, 115) if correct else (235, 102, 102)
        pygame.draw.rect(screen, color, bar_rect)

        if correct:
            draw_text("ดี!", 24, HEIGHT - bar_h + 22, color=(255,255,255), font=BIG)
        else:
            draw_text("คำตอบที่ถูกต้อง", 24, HEIGHT - bar_h + 14, color=(255,255,255), font=FONT)
            ans = q.get("answer") if q.get("type") == "choice" else q.get("answer_text", "")
            draw_text(str(ans), 24, HEIGHT - bar_h + 52, color=(255,255,255), font=MED)

    def run_lobby(self):    #หน้าแรก
        screen.blit(self.bg_lobby, (0, 0))
        draw_screen_frame(pad=280, color=(224, 234, 247), width=3, radius=28)
        mouse = self.mouse_pos
        clicked = self.just_clicked
        btn = pygame.Rect(WIDTH//2-120, 370, 240, 60)
        if draw_raised_button("START", btn, mouse, clicked, font=FONT,):
            self.sounds["cilck"].play()
            self.state = MENU
        draw_text("Press ESC to exit.", WIDTH//2, 480, center=True,color=(255,255,255))

    def run_menu(self): #เลือก part
        screen.blit(self.bg, (0,0))
        draw_screen_frame(pad=50, color=(224, 234, 247), width=3, radius=28)
        draw_text("เลือกรูปแบบแบบทดสอบ", WIDTH//2, 120, center=True, font=BIG)
        mouse = self.mouse_pos
        clicked = self.just_clicked

    #แปลคำศัพท์
        if draw_raised_button("แปลคำศัพท์", pygame.Rect(WIDTH//2-120, 370, 240, 60), mouse, clicked):
            self.sounds["cilck"].play()
            items = randomize_lesson(LESSON_choices, k=20, seed=random.randint(0,9999))
            self.engine = QuestionEngine(items)
            self.feedback_timer = 0
            self.text_buffer = ""
            self.state = QUIZ

    #แปลประโยค
        if draw_raised_button("แปลประโยค", pygame.Rect(WIDTH//2-120, 500, 240, 60), mouse, clicked):
            self.sounds["cilck"].play()
            # ถ้าไม่มีข้อแบบประโยค อย่าเปลี่ยนไปโหมด SENTENCE
            if not LESSON_sentence:
                print("No sentence lessons found; staying in menu")
            else:
                # เลือกข้อประโยคที่ยังไม่เคยเห็นจำนวน k ข้อ (หลีกเลี่ยงการซ้ำจนกว่าจะหมดชุด)
                items = pick_without_seen(LESSON_sentence, self.seen_sentence_ids, 10)
                self.engine = QuestionEngine(items)
                self.feedback_timer = 0
                self.text_buffer = ""
                self.mode_review = False
                self.sentence_sound_played = False
                self.state = SENTENCE

        # สร้างประโยค
        if draw_raised_button("สร้างประโยค", pygame.Rect(WIDTH//2-140, 630, 280, 60), mouse, clicked):
            self.sounds["cilck"].play()
            # อย่าเปลี่ยนถ้าไม่มีบทเรียนแบบสร้างประโยค
            if not LESSON_construct:
                print("No construct lessons found; staying in menu")
            else:
                # เลือกข้อที่ยังไม่เคยเห็นเพื่อหลีกเลี่ยงการซ้ำ
                items = pick_without_seen(LESSON_construct, self.seen_construct_ids, 10)
                if not items:
                    print("No construct items available; staying in menu")
                else:
                    self.engine = QuestionEngine(items)
                    # รีเซ็ตค่าสำหรับโหมดใหม่
                    self.feedback_timer = 0
                    self.text_buffer = ""
                    self.chosen_words = [] # <-- (ต้องเพิ่มตัวแปรนี้ใน __init__)
                    self.current_construct = [] # <-- (ต้องเพิ่มตัวแปรนี้ใน __init__)
                    self.state = CONSTRUCT
            
    def draw_header(self):
        pygame.draw.rect(screen, (148, 163, 184), (0,0,WIDTH,80))
        draw_text(f"คะแนน: {self.engine.progress.score}", 20, 10)
        draw_text(f"สตรีค: {self.engine.progress.streak}", 160, 10)
        n = self.engine.progress.lives
        x0 = WIDTH - 20 - n*22
        for i in range(n):
            screen.blit(self.heart_img, (x0 + i*22, 14))
        total = len(self.engine.items)
        cur = min(self.engine.progress.current_index, total)
        bar_w = 0 if total == 0 else int((cur/total) * (WIDTH-40))
        pygame.draw.rect(screen, (237, 237, 237), (20, 45, WIDTH-40, 8), border_radius=4)
        pygame.draw.rect(screen, (22, 163, 74), (20, 45, bar_w, 8), border_radius=4)

    def run_quiz(self):
        screen.blit(self.bg, (0,0))            # พื้นหลังรูป
        draw_screen_frame(pad=50, color=(224, 234, 247), width=3, radius=28)  # ⬅️ กรอบล้อม
        self.draw_header()
        frame_w, frame_h = 500, 300   # ขนาดกรอบ

        frame_rect = pygame.Rect(WIDTH//2 - frame_w//2, 160, frame_w, frame_h)
        pygame.draw.rect(screen, (255, 255, 255), frame_rect, border_radius=28)
        q = self.engine.current()

        img_surface = None
        if q:
            # ใช้ image ที่ให้มา ถ้าไม่มีให้เดาคือ
            base_name = (q.get("image") or f"{q.get('answer','')}.png").strip()
            cand = [os.path.basename(base_name)]

            for filename in cand:
                for folder in ("assets/images", "assets/img", "assets/pics", "assets"):
                    img_path = os.path.join(folder, filename)
                    if os.path.exists(img_path):
                        try:
                            raw = pygame.image.load(img_path).convert_alpha()
                            pad = 24
                            max_w = frame_rect.w - 2*pad
                            max_h = frame_rect.h - 2*pad
                            iw, ih = raw.get_size()
                            scale = min(max_w/iw, max_h/ih, 1.0)
                            img_surface = pygame.transform.smoothscale(
                                raw, (max(1, int(iw*scale)), max(1, int(ih*scale)))
                            )
                        except Exception as e:
                            print("Image load error:", e)
                        break
                if img_surface:
                    break

        # วาดรูปหรือแจ้งเตือน
        if img_surface:
            screen.blit(img_surface, img_surface.get_rect(center=frame_rect.center))
        else:
            # โชว์ชื่อไฟล์ที่พยายามหา
            fallback_name = (q.get("image") or f"{q.get('answer','')}.png")
            draw_text(f"missing: {fallback_name}", frame_rect.centerx, frame_rect.centery,
                    center=True, font=MED, color=(180,60,60))
        if not q:
            self.state = RESULT
            return

        draw_text(q["prompt"], WIDTH//2, 120, center=True, font=BIG)

        if q["type"] == "choice": 
            mouse = self.mouse_pos
            clicked = self.just_clicked
        # วาดตัวเลือก 4 ปุ่ม
            for i, choice in enumerate(q["choices"]):
                x = WIDTH//2 - 250 + (i % 2) * 260
                y = 475 + (i // 2) * 75
                rect = pygame.Rect(x, y, 240, 60)
                enabled = not self.mode_review
                if draw_raised_button(f"{i+1}. {choice}", rect, mouse, clicked,
                            enabled=enabled, active=(self.selected_index == i),text_color=(41, 68, 99),color=(241, 245, 249), font=FONT):
                    if not self.mode_review:
                        self.selected_index = i
                        self.speak_word(choice, lang='en')  # เล่นเสียงคำภาษาอังกฤษ
         # ปุ่มส่งคำตอบ / ไปต่อ
            submit = pygame.Rect(WIDTH//2 - 120, 620, 240, 60)
            if not self.mode_review:
                can_submit = (self.selected_index is not None)
                if draw_raised_button("ส่งคำตอบ", submit, self.mouse_pos, self.just_clicked,
                                    enabled=can_submit, color=(70,200,90,), font=FONT):
                    good = self.engine.evaluate_choice(self.selected_index)
                    self.last_good = good
                    (self.sounds["correct"] if good else self.sounds["wrong"]).play()
                    self.mode_review = True
            else:
                if draw_raised_button("ไปต่อ", submit, self.mouse_pos, self.just_clicked,
                                    enabled=True, color=(60,150,255), font=FONT):
                    self.engine.advance()
                    self.selected_index = None
                    self.mode_review = False
            if self.mode_review:
                self.draw_feedback_bar()
    
    def run_construct(self):
        screen.blit(self.bg, (0,0)) # หรือ self.bg2
        draw_screen_frame(pad=50, color=(224, 234, 247), width=3, radius=28)
        self.draw_header()

        q = self.engine.current()
        if not q:
            self.state = RESULT
            return

        # 0. เช็กว่าขึ้นข้อใหม่หรือยัง ถ้าใช่ ให้สุ่มคลังคำใหม่
        # (คุณต้องเพิ่ม self.last_q_index = -1 ใน __init__ ด้วย)
        if not hasattr(self, 'last_q_index') or self.last_q_index != self.engine.progress.current_index:
            self.current_construct = deepcopy(q["construct"])
            random.shuffle(self.current_construct)
            self.chosen_words = []
            self.last_q_index = self.engine.progress.current_index
            # เล่นประโยคทั้งประโยค (TTS) เมื่อขึ้นข้อใหม่
            try:
                # พยายามเฉพาะเมื่อ gTTS มีอยู่
                if gTTS is not None:
                    # สร้าง/เล่นไฟล์เสียงประโยค
                    self.speak_word(q.get("answer_sentence", ""), lang='en')
            except Exception as e:
                print("Construct TTS error:", e)

        mouse = self.mouse_pos
        clicked = self.just_clicked

        # 1. วาดคำถาม (รูปภาพ)
        # แสดงคำถามภาษาไทย (question_text) ถ้ามี
        draw_text(q.get("question_text", q.get("prompt", "")), WIDTH//2, 120, center=True, font=BIG)
        # ปุ่มเล่นซ้ำประโยค (ไอคอนลำโพงเล็ก)
        replay_rect = pygame.Rect(WIDTH//2 + 260, 100, 36, 36)
        pygame.draw.rect(screen, (250,250,250), replay_rect, border_radius=8)
        # ไอคอนลำโพงรูปสามเหลี่ยม
        pygame.draw.polygon(screen, (60,60,60), [(replay_rect.x+8, replay_rect.y+9), (replay_rect.x+8, replay_rect.y+27), (replay_rect.x+24, replay_rect.y+18)])
        # คลิกเพื่อเล่นประโยคซ้ำ
        if self.just_clicked and replay_rect.collidepoint(self.mouse_pos):
            try:
                if gTTS is not None:
                    self.speak_word(q.get("answer_sentence", ""), lang='en')
            except Exception as e:
                print("Replay TTS error:", e)

        # 2. วาดกล่องคำตอบ (ที่ว่างๆ)
        answer_box_rect = pygame.Rect(WIDTH//2 - 400, 380, 800, 70)
        pygame.draw.rect(screen, (255, 255, 255), answer_box_rect, border_radius=12)
        pygame.draw.rect(screen, (220, 220, 220), answer_box_rect, width=2, border_radius=12)
        
        # วาดคำที่เลือกแล้ว (self.chosen_words) ลงในกล่องนี้
        built_sentence = " ".join(self.chosen_words)
        draw_text(built_sentence, answer_box_rect.x + 15, answer_box_rect.y + 15 , answer_box_rect.centery, center=False, font=MED)

        # 3. วาดคลังคำ (ปุ่มที่คลิกได้)
        word_x, word_y = WIDTH//2 - 400, 480
        word_buttons = [] # เก็บ (rect, word)
        
        # วาดปุ่ม "Reset" (เอาคำคืนทั้งหมด)
        reset_rect = pygame.Rect(WIDTH - 150, answer_box_rect.y, 100, 60)
        if draw_raised_button("Reset", reset_rect, mouse, clicked, color=(220, 220, 220), text_color=(0,0,0)):
             # ย้ายคำทั้งหมดจาก chosen_words กลับไป current_construct
             self.current_construct.extend(self.chosen_words)
             self.chosen_words.clear()
             random.shuffle(self.current_construct) # สุ่มใหม่

        # วาดปุ่มคลังคำที่เหลือ
        max_width = WIDTH - 100
        for i, word in enumerate(self.current_construct):
            # สร้าง Rect ชั่วคราวเพื่อวัดขนาด
            temp_surf = FONT.render(word, True, (0,0,0))
            btn_w = temp_surf.get_width() + 30 # เพิ่ม padding
            btn_h = 55
            
            if word_x + btn_w > max_width: # ถ้าล้นบรรทัด
                word_x = WIDTH//2 - 400
                word_y += btn_h + 10 # ขึ้นบรรทัดใหม่
                
            btn_rect = pygame.Rect(word_x, word_y, btn_w, btn_h)
            
            if not self.mode_review: # ถ้ายังไม่ตรวจ
                if draw_raised_button(word, btn_rect, mouse, clicked, text_color=(41, 68, 99),color=(241, 245, 249)):
                    # เล่นเสียงคำเดี่ยว (ถ้ามี) ก่อนย้ายคำไปกล่องคำตอบ
                    try:
                        if gTTS is not None:
                            self.speak_word(word, lang='en')
                    except Exception:
                        pass
                    # ย้ายคำจาก construct ไป answer
                    self.chosen_words.append(word)
                    self.current_construct.pop(i) # เอาคำที่ index i ออก
                    break # หยุด loop ทันทีที่คลิก (เพราะ list เปลี่ยนขนาด)
            else: # ถ้าตรวจแล้ว (โหมดรีวิว)
                # วาดปุ่มเฉยๆ แต่คลิกไม่ได้
                draw_raised_button(word, btn_rect, mouse, False, enabled=False, text_color=(41, 68, 99),color=(241, 245, 249))

            word_x += btn_w + 10 # เลื่อนไปทางขวา

        # 4. ปุ่ม "ส่งคำตอบ" / "ไปต่อ"
        submit_rect = pygame.Rect(WIDTH//2 - 120, 700, 240, 60)
        if not self.mode_review:
            can_submit = len(self.chosen_words) > 0
            if draw_raised_button("ส่งคำตอบ", submit_rect, mouse, clicked,
                                  enabled=can_submit, color=(70,200,90,), font=FONT):
                
                built_sentence = " ".join(self.chosen_words).strip().lower()
                correct_sentence = q["answer_sentence"].strip().lower()
                
                good = (built_sentence == correct_sentence)
                self.last_good = good
                (self.sounds["correct"] if good else self.sounds["wrong"]).play()
                self.engine.progress.correct() if good else self.engine.progress.wrong() # อัปเดตคะแนน
                self.mode_review = True
        else:
            if draw_raised_button("ไปต่อ", submit_rect, mouse, clicked,
                                  enabled=True, color=(60,150,255), font=FONT):
                self.engine.advance()
                self.mode_review = False
                self.chosen_words = []
                self.current_construct = []
    def run_sentence(self):
    # UI หลักของโหมดพิมพ์ประโยค: แสดงคำถาม รูป (ถ้ามี),
    # กล่องป้อนคำ และปุ่มส่ง/ไปต่อ พร้อมแถบแสดงผล
        screen.blit(self.bg, (0,0))
        draw_screen_frame(pad=50, color=(224, 234, 247), width=3, radius=28)
        self.draw_header()

        q = self.engine.current()
        if not q:
            self.state = RESULT
            return

    # เล่นเสียงประโยคครั้งเดียวถ้ามี
        if not hasattr(self, "sentence_sound_played") or not self.sentence_sound_played:
            snd = self.sounds.get("sentence")
            if snd:
                try:
                    snd.play()
                except Exception as e:
                    print("Could not play sentence sound:", e)
            self.sentence_sound_played = True

    # วาดข้อความคำถาม (ใช้ 'question_text' เป็นหลัก ถ้าไม่มีให้ใช้ 'prompt')
        prompt_text = q.get("question_text") or q.get("prompt", "")
    # ตัดบรรทัดเมื่อข้อความยาวเกินความกว้าง
        draw_wrapped_text(prompt_text, WIDTH//2, 100, max_width=WIDTH-200, font=BIG, line_spacing=6, align='center')

    # พื้นที่รูปภาพ (ยืมตรรกะจาก run_quiz เล็กน้อย)
        img_surface = None
        base_name = (q.get("image") or f"{q.get('answer_text','')}.png").strip()
        cand = [os.path.basename(base_name)]
        for filename in cand:
            for folder in ("assets/images", "assets/img", "assets/pics", "assets"):
                img_path = os.path.join(folder, filename)
                if os.path.exists(img_path):
                    try:
                        raw = pygame.image.load(img_path).convert_alpha()
                        pad = 12
                        max_w = 480
                        max_h = 200
                        iw, ih = raw.get_size()
                        scale = min(max_w/iw, max_h/ih, 1.0)
                        img_surface = pygame.transform.smoothscale(raw, (max(1, int(iw*scale)), max(1, int(ih*scale))))
                    except Exception as e:
                        print("Image load error:", e)
                    break
            if img_surface:
                break

        if img_surface:
            img_rect = img_surface.get_rect(center=(WIDTH//2, 260))
            screen.blit(img_surface, img_rect)

        # กล่องป้อนคำ
        input_rect = pygame.Rect(WIDTH//2 - 300, 420, 600, 60)
        # จัดการโฟกัส: คลิกภายในเพื่อโฟกัส คลิกนอกเพื่อยกเลิก
        if self.just_clicked:
            if input_rect.collidepoint(self.mouse_pos):
                self.sentence_focused = True
            else:
                self.sentence_focused = False
        border_color = (80,160,240) if self.sentence_focused else (200,200,200)
        pygame.draw.rect(screen, (255, 255, 255), input_rect, border_radius=12)
        pygame.draw.rect(screen, border_color, input_rect, width=2, border_radius=12)
        # เรนเดอร์ข้อความที่พิมพ์อยู่ (แสดง placeholder เมื่อว่าง)
        if self.text_buffer:
            surf = FONT.render(self.text_buffer, True, (41,68,99))
            rect = surf.get_rect()
            rect.midleft = (input_rect.x + 12, input_rect.centery)
            screen.blit(surf, rect)
        else:
            ph = "พิมพ์คำตอบภาษาอังกฤษที่นี่..."
            surf = FONT.render(ph, True, (140,140,140))
            rect = surf.get_rect()
            rect.midleft = (input_rect.x + 12, input_rect.centery)
            screen.blit(surf, rect)

        # เคอร์เซอร์กระพริบเมื่อกล่องข้อความมีโฟกัสและยังไม่อยู่ในโหมดรีวิว
        if getattr(self, 'sentence_focused', False) and not self.mode_review:
            now = pygame.time.get_ticks()
            if (now // self.cursor_blink_ms) % 2 == 0:
                # คำนวณตำแหน่งเคอร์เซอร์โดยใช้ความกว้างของข้อความที่เรนเดอร์จริง
                if self.text_buffer:
                    text_w = FONT.render(self.text_buffer, True, (41,68,99)).get_width()
                    cursor_x = input_rect.x + 12 + text_w + 2
                else:
                    cursor_x = input_rect.x + 12
                cursor_h = max(10, FONT.get_height() - 8)
                cursor_y = input_rect.centery - cursor_h // 2
                pygame.draw.rect(screen, (41,68,99), (cursor_x, cursor_y, 2, cursor_h))

    # ปุ่มส่งคำตอบ / ไปต่อ
        submit_rect = pygame.Rect(WIDTH//2 - 120, 500, 240, 60)
        if not self.mode_review:
            can_submit = bool(self.text_buffer.strip())
            if draw_raised_button("ส่งคำตอบ", submit_rect, self.mouse_pos, self.just_clicked,
                                  enabled=can_submit, color=(70,200,90,), font=FONT):
                good = self.engine.evaluate_text(self.text_buffer)
                self.last_good = good
                (self.sounds["correct"] if good else self.sounds["wrong"]).play()
                self.mode_review = True
        else:
            if draw_raised_button("ไปต่อ", submit_rect, self.mouse_pos, self.just_clicked,
                                  enabled=True, color=(60,150,255), font=FONT):
                self.engine.advance()
                self.text_buffer = ""
                self.mode_review = False
                self.sentence_sound_played = False

        if self.mode_review:
            self.draw_feedback_bar()

    def run_result(self):
        if not hasattr(self, "result_sound_played") or not self.result_sound_played:
            self.sounds["result"].play()
            self.result_sound_played = True
        screen.blit(self.bg, (0,0))            # พื้นหลังรูป
        draw_screen_frame(pad=50, color=(224, 234, 247), width=3, radius=28)  # ⬅️ กรอบล้อม
        p = self.engine.progress
        draw_text("จบบทเรียน!", WIDTH//2, 140, center=True, font=BIG)
        draw_text(f"คะแนนรวม: {p.total_score()}", WIDTH//2, 200, center=True)
        draw_text(f"สตรีคสูงสุด (รอบนี้): {p.highest_streak}", WIDTH//2, 240, center=True)
        if draw_raised_button("กลับหน้าเริ่มเกม", pygame.Rect(WIDTH//2-140, 300, 280, 60),
                            self.mouse_pos, self.just_clicked, color=(60,150,255), font=FONT):
            self.sounds["cilck"].play() 
            self.state = LOBBY
        if draw_raised_button("เริ่มบทเรียนใหม่", pygame.Rect(WIDTH//2-140, 380, 280, 60),
                            self.mouse_pos, self.just_clicked, color=(60,150,255), font=FONT):
            self.sounds["cilck"].play() 
            items = randomize_lesson(LESSON_choices, k=20, seed=random.randint(0,9999)) 
            self.engine = QuestionEngine(items)
            self.__init__()
            self.state = QUIZ
        if draw_raised_button("ออกจากเกม", pygame.Rect(WIDTH//2-140, 700, 280, 60),
                            self.mouse_pos, self.just_clicked, color=(200,70,70), font=FONT): 
            pygame.quit(); sys.exit()
    def handle_events(self):
        self.just_clicked = False
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            elif e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                self.just_clicked = True
                self.mouse_pos = e.pos
            elif e.type == pygame.MOUSEMOTION:
                self.mouse_pos = e.pos
            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_ESCAPE:
                    if self.state == LOBBY: pygame.quit(); sys.exit()
                    elif self.state == MENU: self.state = LOBBY
                    elif self.state == QUIZ: self.state = LOBBY
                    elif self.state == SENTENCE: self.state = MENU
                    elif self.state == CONSTRUCT: self.state = MENU
                    elif self.state == RESULT: self.state = LOBBY
                if self.state == RESULT and e.key == pygame.K_RETURN:
                    self.__init__()
                    self.state = QUIZ
                if self.state == QUIZ:
                    q = self.engine.current()
                    if q and q["type"] == "type":
                        if e.key == pygame.K_BACKSPACE and not self.mode_review:
                            self.text_buffer = self.text_buffer[:-1]
                        elif e.key == pygame.K_RETURN:
                            if not self.mode_review and self.text_buffer:
                                good = self.engine.evaluate_text(self.text_buffer)
                # การรับพิมพ์ในสถานะ SENTENCE
                if self.state == SENTENCE:
                    q = self.engine.current()
                    if q and q.get("type") == "sentence":
                        # รับการพิมพ์เฉพาะเมื่อกล่องป้อนคำมีโฟกัส
                        if not getattr(self, 'sentence_focused', False):
                            pass
                        else:
                            if e.key == pygame.K_BACKSPACE and not self.mode_review:
                                self.text_buffer = self.text_buffer[:-1]
                            elif e.key == pygame.K_RETURN:
                                if not self.mode_review and self.text_buffer:
                                    good = self.engine.evaluate_text(self.text_buffer)
                                    self.last_good = good
                                    (self.sounds["correct"] if good else self.sounds["wrong"]).play()
                                    self.mode_review = True
                            else:
                                # ต่ออักขระยูนิโค้ดที่พิมพ์ได้เมื่อยังไม่อยู่ในโหมดรีวิว
                                if not self.mode_review and hasattr(e, 'unicode') and e.unicode:
                                    self.text_buffer += e.unicode
    def run(self):
        while True:
            self.handle_events()
            if self.state == LOBBY:
                self.run_lobby()
            elif self.state == MENU:
                self.run_menu()
            elif self.state == QUIZ:
                if self.engine.done():
                    # ถ้าจบเพราะชีวิตหมด ให้ไปหน้า RESULT ทันที แม้จะอยู่ในโหมดรีวิว
                    if self.engine.progress.lives <= 0 or not self.mode_review:
                        self.state = RESULT
                    else:
                        # ยังคงแสดงหน้าทดสอบเพื่อให้ผู้ใช้เห็นผลและกด 'ไปต่อ'
                        self.run_quiz()
                else:
                    self.run_quiz()
            elif self.state == SENTENCE:
                if self.engine.done():
                    if self.engine.progress.lives <= 0 or not self.mode_review:
                        self.state = RESULT
                    else:
                        self.run_sentence()
                else:
                    self.run_sentence()
            elif self.state == CONSTRUCT:
                if self.engine.done():
                    if self.engine.progress.lives <= 0 or not self.mode_review:
                        self.state = RESULT
                    else:
                        self.run_construct()
                else:
                    self.run_construct()
            elif self.state == RESULT:
                self.run_result()

            pygame.display.flip()
            clock.tick(60)

if __name__ == "__main__":
    Game().run()
