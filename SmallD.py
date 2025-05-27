from RPLCD.i2c import CharLCD
import threading
import signal
import sys
import random
import RPi.GPIO as GPIO
import time
jumping = False
start_game_check = False
lcd = CharLCD("PCF8574",0x27)
Digit = [(),(),(),(),(),(),(),()]
lights = [18,23,24,25,8]
second_cnt = 0
time_set = 0.5
score_cnt = 0
flag = False
scene_list = []
#Run 1
Digit[0] = (
    0x0E,
    0x0E,
    0x14,
    0x1F,
    0x05,
    0x06,
    0x19,
    0x01
)
# Run 2
Digit[1] = (
    0x0E,
    0x0E,
    0x05,
    0x1F,
    0x14,
    0x06,
    0x19,
    0x01
)
# Jump
Digit[2] = (
    0x0E,
    0x0E,
    0x15,
    0x1F,
    0x04,
    0x0E,
    0x09,
    0x00
)
#仙人掌1
Digit[3] = (
    0x00,
    0x06,
    0x0F,
    0x06,
    0x0F,
    0x06,
    0x0F,
    0x06
)
#仙人掌2
Digit[4] = (
    0x10,
    0x14,
    0x14,
    0x15,
    0x1F,
    0x05,
    0x04,
    0x04
)
#子弹
Digit[5] = (
    0x00,
    0x00,
    0x00,
    0x0E,
    0x1E,
    0x0E,
    0x00,
    0x00
)
def signal_handler(sig,frame):
    GPIO.cleanup()
    sys.exit(0)

def button_press_callback(channel):
    global start_game_check
    if not start_game_check:
        start_game_check = True
        return
    print("Edge Detected")
    global jumping
    jumping = True
    GPIO.output(26,GPIO.HIGH)
    time.sleep(0.1)
    GPIO.output(26,GPIO.LOW)

def button_press_remake(channel):
    global start_game_check
    if not start_game_check:
        start_game_check = True
    print("Remake")
    global checkFlag
    lcd.clear()
    checkFlag = True
    init_game()

def init_game():
    global second_cnt,time_set,score_cnt,flag, scene_list
    second_cnt = 0
    time_set = 0.5
    score_cnt = 0
    flag = False
    scene_list = []
for i in range(0,6):
    lcd.create_char(i,Digit[i])
#x是列(0-15) y是行(0-1)
def print_on_canvas(x,y,i):
    lcd.cursor_pos = (x,y)
    if i == 0:
        lcd.write_string("\x00")
    elif i == 1:
        lcd.write_string("\x01")
    elif i == 2:
        lcd.write_string("\x02")
    elif i == 3:
        lcd.write_string("\x03")
    elif i == 4:
        lcd.write_string("\x04")
    elif i == 5:
        lcd.write_string("\x05")
    elif i == 6:
        lcd.write_string("\x06")

class Object:
    def __init__(self,y,x,type):
        self.y = y
        self.x = x
        self.type = type
    def print_Canvas(self):
        print_on_canvas(self.y,self.x,self.type)

class Player(Object):
    def __init__(self):
        self.y = 1
        self.x = 1
        self.type = 0
    
    def jump(self):
        self.y = 0
        self.type = 2
    
    def ground(self):
        self.y = 1
        if(self.type == 2):
            self.type = 0
        else:
            self.type = not self.type

class Scene(Object):
    def __init__(self, y, x, type):
        super().__init__(y, x, type)
    
    def move(self):
        self.x -= 1
def add_scene():
    global scene_list
    scene_type = random.randint(3,5)
    #子弹
    if scene_type == 5:
        new_type = Scene(0,15,scene_type)
    #仙人掌
    else:
        new_type = Scene(1,15,scene_type)
    scene_list.insert(0,new_type)
    
def timer_interruput():
    global second_cnt,flag
    flag = True
    timer = threading.Timer(time_set,timer_interruput)
    timer.start()
    second_cnt += 1
timer_interruput()
checkFlag = True
try:
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    GPIO.setup(20,GPIO.IN,pull_up_down = GPIO.PUD_UP)
    GPIO.setup(21,GPIO.IN,pull_up_down = GPIO.PUD_UP)
    GPIO.add_event_detect(20,GPIO.FALLING,callback = button_press_callback,bouncetime=200)
    GPIO.add_event_detect(21,GPIO.FALLING,callback = button_press_remake,bouncetime=200)
    GPIO.setup(26,GPIO.OUT)
    signal.signal(signal.SIGINT,signal_handler)
    GPIO.setup(lights,GPIO.OUT)
    P = Player()
    while True:
        if not start_game_check:
            lcd.cursor_pos = (0,2)
            lcd.write_string("SW1: Restart")
            lcd.cursor_pos = (1,3)
            lcd.write_string("SW2: JUMP")
        if flag and start_game_check:
            time_set = max(0.5-0.03*score_cnt,0.3)
            lcd.clear()
            flag = False
            if jumping:
                P.jump()
                jumping = False
                GPIO.output(lights,GPIO.HIGH)
            else:
                GPIO.output(lights,GPIO.LOW)
                P.ground()
            
            if len(scene_list) == 0:
                add_scene()
            elif (15 - scene_list[0].x)>=3:
                check_if_add = random.randint(0,1)
                if check_if_add == 0:
                    add_scene()
            for i in scene_list:
                i.move()
                i.print_Canvas()
            if scene_list[len(scene_list)-1].x == 1:
                if scene_list[len(scene_list)-1].y == P.y:
                    print("Game Over")
                    checkFlag = False
                    lcd.clear()
                    lcd.cursor_pos = (0,3)
                    lcd.write_string("GAME OVER")
                    lcd.cursor_pos = (1,(15-len("SCORE:"+str(score_cnt)))//2)
                    lcd.write_string("SCORE:"+str(score_cnt))
                    time_set = 0.2
                    while not checkFlag:
                        if second_cnt % 2 == 0:
                            GPIO.output(lights,GPIO.HIGH)
                        else:
                            GPIO.output(lights,GPIO.LOW)
                    else:
                        continue
                else:
                    score_cnt+=1
            if scene_list[len(scene_list)-1].x == 0:
                scene_list.pop()
            P.print_Canvas()
            lcd.cursor_pos = (0,16-len(str(score_cnt)))
            lcd.write_string(str(score_cnt))
except Exception as e:
    print(e)
    lcd.clear()
    lcd.cursor_pos = (1,3)
    lcd.write_string(" THE END ")
