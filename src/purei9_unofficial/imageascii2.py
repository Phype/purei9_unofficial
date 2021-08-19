


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

def pic2block(pic):
    global BLOCKS

    buf = ""

    h = len(pic)
    w = len(pic[0])

    for y in range(0, h, 2):
        for x in range(0, w, 2):
            
            a = pic[y][x]
            b = pic[y][x + 1]
            c = pic[y + 1][x]
            d = pic[y + 1][x + 1]
            
            code = a + 2*b + 4*c + 8*d
            
            buf += BLOCKS[code]
            
        buf += "\n"
            

    return buf

print(pic2block(PIC))
    
        
        
        
