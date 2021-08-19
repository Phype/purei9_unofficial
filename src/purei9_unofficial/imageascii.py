import json
import base64
import io
import PIL.Image

def image_json_2_ascii(js):

    #with open("image.json") as fp:
    #    js = json.loads(fp.read())
    
    charger_pos = [js["ImageInfo"]["ChargerPoseImageCoordinates"]["X"], js["ImageInfo"]["ChargerPoseImageCoordinates"]["Y"]]
        
    imagebytes = io.BytesIO(base64.b64decode(js["PngImage"]))

    with PIL.Image.open(imagebytes) as img:
        
        buf = ""
        
        img = img.resize((64, 32), resample=PIL.Image.NEAREST)
        
        
        pixelMap = img.load()
        
        charger_pos[0] = int(charger_pos[0] * img.size[0])
        charger_pos[1] = int(charger_pos[1] * img.size[1])
        
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
        
        # img = img.resize((512, 512), resample=PIL.Image.NEAREST)
        
        # img.show()
        return buf + "\n"
    
