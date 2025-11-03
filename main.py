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
    # เงานุ่ม ๆ รอบกรอบ (optional)
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
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, list):
        raise ValueError("lessons file must be a JSON list")
    return data
LESSON_choices = load_lessons_json("assets/lessons/choices.json")

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
    
    def done(self):
        return self.progress.current_index >= len(self.items) or self.progress.lives <= 0
    
LOBBY, MENU, QUIZ, RESULT = 'LOBBY','MENU','QUIZ','RESULT'

class Game:
    def __init__(self):
        self.state = LOBBY
        self.engine = QuestionEngine(LESSON_choices)
        self.feedback_timer = 0
        self.feedback_color = (0,0,0)
        self.text_buffer = ""
        self.just_clicked = False
        self.mouse_pos = (0, 0)
        self.heart_img = pygame.transform.smoothscale(
                    pygame.image.load("assets/ui/heart.png").convert_alpha(), (18,18))
        pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=4096)
        pygame.mixer.music.set_volume(1.0)
        self.voice_dir = "assets/voice"
        os.makedirs(self.voice_dir, exist_ok=True)
        self.selected_index = None
        os.makedirs(self.voice_dir, exist_ok=True)
        self.mode_review = False   # True = เพิ่งตรวจเสร็จ กำลังรอให้กด "ไปต่อ"
        self.last_good = None
        self.sounds = {
                        "correct": pygame.mixer.Sound("assets/sounds/correct.mp3"),
                        "wrong": pygame.mixer.Sound("assets/sounds/wrong.mp3"),
                        "ui": pygame.mixer.Sound("assets/sounds/ui_sound.mp3"),
                        "cilck": pygame.mixer.Sound("assets/sounds/game_start.mp3"),
                        "lobby": pygame.mixer.Sound("assets/sounds/lobby.mp3"),
                        "result": pygame.mixer.Sound("assets/sounds/result.mp3"),
                    }
        self.bg_lobby = pygame.image.load("assets/background/bg_lobby.png").convert_alpha()
        self.bg_lobby = pygame.transform.smoothscale(self.bg_lobby, (WIDTH, HEIGHT))
        self.bg = pygame.image.load("assets/background/bg1.png").convert_alpha()
        self.bg = pygame.transform.smoothscale(self.bg, (WIDTH, HEIGHT))
        self.bg2 = pygame.image.load("assets/background/bg2.png").convert_alpha()
        self.bg2 = pygame.transform.smoothscale(self.bg2, (WIDTH, HEIGHT))

    # ---------- สร้างเสียงเก็บไว้ใน voices และเรียกอ่านเสียง  ----------
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

    def run_lobby(self):
        screen.blit(self.bg_lobby, (0, 0))
        draw_screen_frame(pad=280, color=(224, 234, 247), width=3, radius=28)
        mouse = self.mouse_pos
        clicked = self.just_clicked
        btn = pygame.Rect(WIDTH//2-120, 370, 240, 60)
        if draw_raised_button("START", btn, mouse, clicked, font=FONT,):
            self.sounds["cilck"].play()
            self.state = MENU
        draw_text("Press ESC to exit.", WIDTH//2, 480, center=True,color=(255,255,255))

    def run_menu(self):
    screen.blit(self.bg, (0,0))
    draw_screen_frame(pad=50, color=(224, 234, 247), width=3, radius=28)
    draw_text("เลือกรูปแบบแบบทดสอบ", WIDTH//2, 120, center=True, font=BIG)
    mouse = self.mouse_pos
    clicked = self.just_clicked

    # --- Word translation ---
    if draw_raised_button("แปลคำศัพท์", pygame.Rect(WIDTH//2-120, 370, 240, 60), mouse, clicked):
        self.sounds["cilck"].play()
        items = randomize_lesson(LESSON_choices, k=20, seed=random.randint(0,9999))
        self.engine = QuestionEngine(items)
        self.feedback_timer = 0
        self.text_buffer = ""
        self.state = QUIZ

    # --- Sentence translation ---
    if draw_raised_button("แปลประโยค", pygame.Rect(WIDTH//2-120, 500, 240, 60), mouse, clicked):
        self.sounds["cilck"].play()
        items = randomize_lesson(LESSON_sentences, k=10, seed=random.randint(0,9999))
        self.engine = QuestionEngine(items)
        self.feedback_timer = 0
        self.text_buffer = ""
        self.state = QUIZ
        
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
                
        elif q["type"] == "sentence": #ยังทำไม่เสร็จ (แบบแปลประโยค)
            box = pygame.Rect(WIDTH//2-220, 220, 440, 60)
            pygame.draw.rect(screen, (40,40,40), box, border_radius=8)
            pygame.draw.rect(screen, (120,120,120), box, 2, border_radius=8)
            draw_text(self.text_buffer or "พิมพ์คำตอบที่นี่...", box.x+12, box.y+16, color=(200,200,200))
            mouse = pygame.mouse.get_pos()
            clicked = pygame.mouse.get_pressed()[0]
            submit = pygame.Rect(WIDTH//2-80, 310, 160, 50)
            #if draw_button("ส่งคำตอบ", submit, mouse, clicked, enabled=len(self.text_buffer)>0):
                ##self.feedback_color = (10,80,40) if good else (90,20,20)
                ##self.text_buffer = ""

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
                                self.last_good = good
                                self.feedback_color = (10,80,40) if good else (90,20,20)
                                self.feedback_timer = 10
                                self.text_buffer = ""
                                self.mode_review = True
                            elif self.mode_review:
                                self.engine.advance()
                                self.mode_review = False
                                self.feedback_timer = 0
                        else:
                            ch = e.unicode
                            if ch.isprintable() and not self.mode_review:
                                self.text_buffer += ch


    def run(self):
        while True:
            self.handle_events()
            if self.state == LOBBY:
                self.run_lobby()
            elif self.state == MENU:
                self.run_menu()
            elif self.state == QUIZ:
                if self.engine.done() and not self.mode_review:
                    self.state = RESULT
                else:
                    self.run_quiz()
            elif self.state == RESULT:
                self.run_result()
            pygame.display.flip()
            clock.tick(60)

if __name__ == "__main__":
    Game().run()

