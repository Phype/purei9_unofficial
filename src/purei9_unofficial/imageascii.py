import json
import base64
import io
import PIL.Image
import math

BLOCKS = [
    " ",
    "▘",
    "▝",
    "▀",
    "▖",
    "▌",
    "▞",
    "▛",
    "▗",
    "▚",
    "▐",
    "▜",
    "▄",
    "▙",
    "▟",
    "█"
]

def pixelfunc(x):
    return x[3] >= 200

def pixelfunc2(x):

    # Cleaned
    # Purei9
    if 195 <= x[1]: #  and x[1] <= 196:
        r= 2

    # Cleaned
    # Purei9.2 seems to use differen colors ?!
    elif 148 <= x[0] and x[0] <= 149:
        r=2
    
    # Uncleaned
    elif 127 <= x[1] and x[1] <= 128:
        r=1
    
    else:
        r=0

    return r

def pic2block(pic, w, h, charger=None, twoshade=False, border = False, halfblock = True):
    global BLOCKS
    
    buf = ""

    #h = pic.size[1] # len(pic)
    #w = pic.size[0] # len(pic[0])
    
    rows = [False] * h
    cols = [False] * w
    
    crop_x_start = 0
    crop_x_end   = w
    
    crop_y_start = 0
    crop_y_end   = h

    for y in range(0, h):
        row_empty = True
        
        for x in range(0, w):
            if pixelfunc(pic[x, y]) > 0:
                row_empty = False
                
        rows[y] = row_empty
    
    for x in range(0, w):
        col_empty = True
        
        for y in range(0, h):
            if pixelfunc(pic[x, y]) > 0:
                col_empty = False
                
        cols[x] = col_empty
        
    for col in range(0, w):
        if cols[col]:
            crop_x_start = col + 1
        else:
            break
        
    for col in range(w - 1, -1, -1):
        if cols[col]:
            crop_x_end = col - 1
        else:
            break
        
    for row in range(0, h):
        if rows[row]:
            crop_y_start = row + 1
        else:
            break
        
    for row in range(h - 1, -1, -1):
        if rows[row]:
            crop_y_end = row - 1
        else:
            break
        
    if border:
        buf += "+-" + ("-" * int(math.ceil((crop_x_end - crop_x_start)/2))) + "-+\n"

    if charger:
        charger[0] = int(charger[0] * w)
        charger[1] = int(charger[1] * h)


    if halfblock:
        for y in range(crop_y_start, crop_y_end, 2):
            
            if border:
                buf += "| "
            
            for x in range(crop_x_start, crop_x_end, 2):
                
                if charger and (charger[0] == x or charger[0] == x+1) and (charger[1] == y or charger[1] == y+1):
                    buf += "C"
                else:
                
                    a = pixelfunc(pic[x, y])
                    b = pixelfunc(pic[x + 1, y])
                    c = pixelfunc(pic[x, y + 1])
                    d = pixelfunc(pic[x + 1, y + 1])
                    
                    if twoshade:
                        shades = [pixelfunc2(pic[x, y]) , pixelfunc2(pic[x+1, y]) , pixelfunc2(pic[x, y+1]) , pixelfunc2(pic[x+1, y+1])]
                        shade = max(shades)
                    else:
                        shade = 2
                    
                    code = a + 2*b + 4*c + 8*d
                    
                    if code != 0:
                        if shade == 2:
                            buf += BLOCKS[code]
                        elif shade == 1:
                            buf += "▒"
                        else:
                            buf += " "
                    else:
                        buf += " "
            
            if border:
                buf += " |"
            buf += "\n"
    else:
        for y in range(crop_y_start, crop_y_end):
            
            if border:
                buf += "| "
            
            for x in range(crop_x_start, crop_x_end):
                
                if charger and (charger[0] == x or charger[0] == x+1) and (charger[1] == y or charger[1] == y+1):
                    buf += "▒"
                else:
                    a = pixelfunc(pic[x, y])
                    
                    shade = pixelfunc2(pic[x, y])
                    
                    if a:
                        if shade == 2:
                            buf += "█"
                        elif shade == 1:
                            buf += "▒"
                        elif shade == 0:
                            buf += " "
                    else:
                        buf += " "
            
            if border:
                buf += " |"
            buf += "\n"
        
    if border:
        buf += "+-" + ("-" * int(math.ceil((crop_x_end - crop_x_start)/2))) + "-+\n"

    return buf 

def image_json_2_ascii(js):

    #with open("image.json") as fp:
    #    js = json.loads(fp.read())
    
    charger_pos = [js["ImageInfo"]["ChargerPoseImageCoordinates"]["X"], js["ImageInfo"]["ChargerPoseImageCoordinates"]["Y"]]
        
    imagebytes = io.BytesIO(base64.b64decode(js["PngImage"]))

    with PIL.Image.open(imagebytes) as img:
        
        # resize, adjust for character width/heigh in terminal
        img = img.resize((68, 32), resample=PIL.Image.NEAREST)
        
        
        pixelMap = img.load()
        
        #charger_pos[0] = int(charger_pos[0] * img.size[0])
        #charger_pos[1] = int(charger_pos[1] * img.size[1])
        
        """
        
        buf = ""
        for y in range(img.size[1]):
            for x in range(img.size[0]):
                
                r,g,b,a = pixelMap[x,y]
                
                if x == charger_pos[0] and y == charger_pos[1]:
                    r,g,b,a = (0,0,255, 255)
                    c = "\033[38;31;47;41m \033[0m"
                else:
                    
                    if a == 255:
                        r,g,b,a = (255,255,255, 255)
                        c = "\033[38;30;47;47m \033[0m"
                    else:
                        r,g,b,a = (0,0,0,0)
                        c = " "
                
                pixelMap[x,y] = (r, g, b, a)
                
                buf += c
            buf += "\n"
        
        """
        
        buf = pic2block(pixelMap, img.size[0], img.size[1], charger=charger_pos)
        
        return buf
    

import requests

def draw2shade(url, show=False):
    
    r = requests.get(url)
    imagebytes = io.BytesIO(r.content)
    
    with PIL.Image.open(imagebytes) as img:
    
        # resize, adjust for character width/heigh in terminal
        img = img.resize((68, 32), resample=PIL.Image.NEAREST)
        # img = img.resize((36, 16), resample=PIL.Image.NEAREST)
        
        pixelMap = img.load()
        
        buf = pic2block(pixelMap, img.size[0], img.size[1], charger=None, twoshade=True)
        
        if show:
            img = img.resize((68*10, 32*10), resample=PIL.Image.NEAREST)
            img.show()
        
    return buf

if __name__ == "__main__":
    import sys
    print(draw2shade(sys.argv[1], show=False))

