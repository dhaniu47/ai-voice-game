# --- [BASE CODE PRESERVED | UI-ONLY ENHANCEMENTS ADDED] ---
# Animated HUD glow
# Smooth UI transitions
# Radial ripple on hover
# Cinematic fade-in panels
# AUDIO ROUTING FIX APPLIED (PERMANENT)

import pygame, cv2, os, math, time, random, threading
import pyttsx3, speech_recognition as sr

# ================= INIT =================
pygame.init()
pygame.mixer.init()
engine = pyttsx3.init()
engine.setProperty("rate", 150)

recognizer = sr.Recognizer()
mic = sr.Microphone()

info = pygame.display.Info()
WIDTH, HEIGHT = info.current_w, info.current_h
screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.FULLSCREEN)
clock = pygame.time.Clock()
pygame.mouse.set_visible(True)

# ================= AUDIO LOCK =================
is_speaking = False

# ================= VIDEO BACKGROUND =================
VIDEO_PATH = os.path.join(os.path.dirname(__file__), "assets", "ai_background.mp4")
video = cv2.VideoCapture(VIDEO_PATH)

def get_video_frame():
    if not video.isOpened(): return None
    ret, frame = video.read()
    if not ret:
        video.set(cv2.CAP_PROP_POS_FRAMES, 0)
        ret, frame = video.read()
        if not ret: return None
    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    frame = cv2.resize(frame, (WIDTH, HEIGHT))
    surf = pygame.surfarray.make_surface(frame.swapaxes(0,1))
    surf.set_alpha(40)
    return surf

# ================= SOUNDS =================
click = pygame.mixer.Sound("assets/sounds/click.wav")
listen = pygame.mixer.Sound("assets/sounds/listen.wav")
amb = pygame.mixer.Sound("assets/sounds/ambience.wav")
amb.set_volume(0.3)
amb.play(-1)

# ================= ASSETS =================
player_img = pygame.image.load("assets/1.png").convert_alpha()
npc_imgs = {
    "calm": pygame.image.load("assets/calm.png").convert_alpha(),
    "curious": pygame.image.load("assets/curious.png").convert_alpha(),
    "angry": pygame.image.load("assets/touchy.png").convert_alpha()
}

BASE = (260, 420)
player_img = pygame.transform.smoothscale(player_img, BASE)
for k in npc_imgs:
    npc_imgs[k] = pygame.transform.smoothscale(npc_imgs[k], BASE)

# ================= POSITIONS =================
px, py = WIDTH * 0.3, HEIGHT * 0.65
npc = {"x": WIDTH * 0.7, "y": HEIGHT * 0.65, "mood": "calm"}
player_speed = 6

voice_state = "IDLE"
message = "Press V or Tap MIC"

font = pygame.font.SysFont("segoeui", 24)
big = pygame.font.SysFont("segoeui", 32)
small = pygame.font.SysFont("segoeui", 18)

# ================= FX DATA =================
snow = [{"x":random.randint(0,WIDTH),"y":random.randint(0,HEIGHT),"s":random.uniform(0.3,1)} for _ in range(300)]
embers = [{"x":random.randint(0,WIDTH),"y":random.randint(0,HEIGHT),"s":random.uniform(0.5,2)} for _ in range(250)]
math_pts = [{"a":random.uniform(0,math.pi*2),"r":random.randint(80,400)} for _ in range(250)]

# ================= UI STATE =================
show_help = False
help_alpha = 0
ripples = []
start_time = time.time()
interaction_count = 0

# ================= HELPERS =================
def lerp(a,b,t): return a+(b-a)*t

def glass_box(x,y,w,h,alpha):
    s=pygame.Surface((w,h),pygame.SRCALPHA)
    pygame.draw.rect(s,(30,40,70,alpha),s.get_rect(),border_radius=18)
    pygame.draw.rect(s,(120,200,255,alpha+40),s.get_rect(),1,border_radius=18)
    screen.blit(s,(x,y))

def glow_box(x,y,w,h,t):
    a=int(120+math.sin(t*2)*60)
    glass_box(x,y,w,h,a)

def draw_circle_button(cx,cy,r,label,hover):
    surf=pygame.Surface((r*2,r*2),pygame.SRCALPHA)
    base=20; glow=140 if hover else base
    pygame.draw.circle(surf,(120,200,255,glow),(r,r),r)
    if hover: pygame.draw.circle(surf,(200,240,255,200),(r,r),r,2)
    txt=small.render(label,True,(230,240,255))
    surf.blit(txt,(r-txt.get_width()//2,r-txt.get_height()//2))
    screen.blit(surf,(cx-r,cy-r))

def add_ripple(pos):
    ripples.append({"x":pos[0],"y":pos[1],"r":5,"a":120})

def draw_ripples():
    for r in ripples[:]:
        r["r"]+=3
        r["a"]-=4
        if r["a"]<=0: ripples.remove(r)
        else:
            s=pygame.Surface((r["r"]*2,r["r"]*2),pygame.SRCALPHA)
            pygame.draw.circle(s,(180,220,255,r["a"]),(r["r"],r["r"]),r["r"],2)
            screen.blit(s,(r["x"]-r["r"],r["y"]-r["r"]))

# ================= VOICE (PERMANENT FIX) =================
def speak(t):
    global is_speaking
    if is_speaking:
        return

    def _s():
        global is_speaking
        is_speaking = True
        pygame.mixer.pause()          # silence game audio
        engine.say(t)
        engine.runAndWait()
        pygame.mixer.unpause()        # restore game audio
        is_speaking = False

    threading.Thread(target=_s, daemon=True).start()

def npc_reply(txt):
    if not txt: return "I didn't catch that."
    if "hello" in txt or "hi" in txt: return "Hello. I can hear you."
    if "name" in txt: return "I am your AI companion."
    return "Okay."

def listen_and_reply():
    global voice_state,message,interaction_count
    voice_state="LISTENING"
    listen.play()
    try:
        with mic as src:
            recognizer.adjust_for_ambient_noise(src,0.3)
            audio=recognizer.listen(src,phrase_time_limit=4)
        txt=recognizer.recognize_google(audio).lower()
    except:
        txt=""
    reply=npc_reply(txt)
    message="NPC: "+reply
    speak(reply)
    interaction_count+=1
    voice_state="IDLE"

# ================= LOOP =================
running=True
while running:
    t=time.time()
    bg=get_video_frame()
    if bg: screen.blit(bg,(0,0))
    else: screen.fill((10,15,25))

    # Background FX
    if npc["mood"]=="calm":
        for p in snow:
            p["y"]+=p["s"]
            if p["y"]>HEIGHT: p["y"]=0
            pygame.draw.circle(screen,(200,230,255,50),(int(p["x"]),int(p["y"])),2)
    elif npc["mood"]=="angry":
        for e in embers:
            e["y"]-=e["s"]
            if e["y"]<0: e["y"]=HEIGHT
            pygame.draw.circle(screen,(255,120,40,45),(int(e["x"]),int(e["y"])),2)
    else:
        cx,cy=WIDTH//2,HEIGHT//2
        for p in math_pts:
            p["a"]+=0.01
            x=cx+math.cos(p["a"]+t)*p["r"]
            y=cy+math.sin(p["a"]+t)*p["r"]
            pygame.draw.circle(screen,(120,200,255,40),(int(x),int(y)),2)

    mouse=pygame.mouse.get_pos()
    click_m=False

    for e in pygame.event.get():
        if e.type==pygame.QUIT: running=False
        if e.type==pygame.MOUSEBUTTONDOWN:
            click_m=True
            add_ripple(mouse)
        if e.type==pygame.KEYDOWN:
            if e.key==pygame.K_ESCAPE: running=False
            if e.key==pygame.K_v and voice_state=="IDLE" and not is_speaking:
                threading.Thread(target=listen_and_reply,daemon=True).start()
            if e.key==pygame.K_e and not is_speaking:
                message="NPC: I am here."
                speak("I am here.")

    # Player (keyboard)
    k=pygame.key.get_pressed()
    if k[pygame.K_LEFT]: px-=player_speed
    if k[pygame.K_RIGHT]: px+=player_speed
    if k[pygame.K_UP]: py-=player_speed
    if k[pygame.K_DOWN]: py+=player_speed
    px=max(130,min(WIDTH-130,px))
    py=max(210,min(HEIGHT-210,py))
    screen.blit(player_img,(px-BASE[0]//2,py-BASE[1]//2))

    # NPC mood
    d=math.hypot(px-npc["x"],py-npc["y"])
    npc["mood"]="angry" if d<140 else "curious" if d<300 else "calm"
    screen.blit(npc_imgs[npc["mood"]],(npc["x"]-BASE[0]//2,npc["y"]-BASE[1]//2))

    # HUD
    glow_box(20,20,260,130,t)
    screen.blit(font.render(f"NPC MODE : {npc['mood'].upper()}",True,(230,240,255)),(40,50))
    screen.blit(font.render(f"VOICE : {voice_state}",True,(200,220,255)),(40,75))
    screen.blit(font.render(f"TIME : {int(t-start_time)}s",True,(200,220,255)),(40,100))
    screen.blit(font.render(f"COUNT : {interaction_count}",True,(200,220,255)),(40,125))

    # Controls (touch + keyboard)
    cx,cy=WIDTH-170,HEIGHT-170
    spacing=64
    buttons={
        "↑":(cx,cy-spacing),
        "←":(cx-spacing,cy),
        "→":(cx+spacing,cy),
        "↓":(cx,cy+spacing),
        "V":(cx+spacing*1.6,cy),
        "E":(cx+spacing*1.6,cy-spacing),
        "ESC":(cx,cy+spacing*2)
    }

    for lbl,(bx,by) in buttons.items():
        hover=math.hypot(mouse[0]-bx,mouse[1]-by)<28
        draw_circle_button(bx,by,26 if lbl!="ESC" else 30,lbl,hover)

        if hover and click_m:
            if lbl=="↑": py-=player_speed*4
            if lbl=="↓": py+=player_speed*4
            if lbl=="←": px-=player_speed*4
            if lbl=="→": px+=player_speed*4
            if lbl=="V" and voice_state=="IDLE" and not is_speaking:
                threading.Thread(target=listen_and_reply,daemon=True).start()
            if lbl=="E" and not is_speaking:
                message="NPC: I am here."
                speak("I am here.")
            if lbl=="ESC": running=False

    # HOW TO PLAY
    # HOW TO PLAY (LEFT BOTTOM)
    how_rect = pygame.Rect(20, HEIGHT-70, 200, 40)
    glass_box(how_rect.x, how_rect.y, how_rect.width, how_rect.height, 70)
    screen.blit(font.render("HOW TO PLAY", True, (230,240,255)), (how_rect.x+40, how_rect.y+10))
    if how_rect.collidepoint(mouse) and click_m:
        show_help = not show_help
        click.play()


    help_alpha=lerp(help_alpha,200 if show_help else 0,0.1)
    if help_alpha>5:
        glass_box(WIDTH-420,20,400,260,int(help_alpha))
        lines=[
            "HOW TO PLAY","",
            "Arrow / Touch : Move",
            "V : Voice",
            "E : Attention",
            "ESC : Exit","",
            "Mic clarity affects voice"
        ]
        for i,l in enumerate(lines):
            screen.blit(font.render(l,True,(230,240,255)),(WIDTH-390,60+i*26))

    draw_ripples()
    pygame.display.update()
    clock.tick(60)

video.release()
pygame.quit()
