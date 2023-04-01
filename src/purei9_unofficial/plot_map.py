
import numpy as np
import gzip
import json
import io

import PIL
import PIL.ImageDraw

def transform(points, xya):
    translate = xya[0:2]
    angle = -1 * xya[2]
    R = np.array([[np.cos(angle), -np.sin(angle)],[np.sin(angle),np.cos(angle)]])
    
    #return np.matmul(points-translate, R)
    return np.matmul(R, (points - translate).T).T

def plot_map(map_data_gzip: bytes):
    map_data = json.loads(gzip.decompress(map_data_gzip))
    
    transform_ids = np.array([crumb["t"] for crumb in map_data['crumbs']])
    points = np.array([np.array(crumb['xy']) for crumb in map_data['crumbs']])
    
    transforms = {}
    for transform_data in map_data['transforms']:
        transforms[transform_data['t']] = np.array(transform_data['xya'])
    
    unique_transform_ids = np.unique(transform_ids)
    transformed_points = np.zeros(points.shape)
    for transform_id in unique_transform_ids:
        transformed_points[transform_ids==transform_id] = transform(points[transform_ids==transform_id], transforms[transform_id])
    
    ###

    min_x, min_y = np.amin(transformed_points, axis=0)
    max_x, max_y = np.amax(transformed_points, axis=0)

    width  = max_x - min_x
    height = max_y - min_y

    ###

    point_radius = 1# 1.4#5
    scale        = 11# 10#35
    upscale      = 10# 10#35

    width  = int(round(width * scale + 2 * point_radius)) + 4
    height = int(round(height * scale + 2 * point_radius)) + 4

    image = PIL.Image.new("RGB", (width, height))
    draw = PIL.ImageDraw.Draw(image)

    for p in transformed_points:
        x = 2 + (p[0] - min_x) * scale
        y = -3 + height - ((p[1] - min_y) * scale)

        draw.ellipse((x - point_radius, y - point_radius, x + point_radius, y + point_radius), fill = 'white', outline ='white')

    image = image.resize((upscale*width, upscale*height), PIL.Image.BILINEAR )
    image = image.convert('L')

    image = image.point( lambda p: 180 if p > 127 else 255 )

    image = image.convert('RGB')

    charger_pose = map_data["chargerPose"]
    charger_pose_transform = transforms[charger_pose['t']]
    charger_pos = np.array(charger_pose['xya'][0:2])
    charger_angle = charger_pose['xya'][2]
    charger_pos_transformed = transform(charger_pos, charger_pose_transform)
    charger_angle_transformed = charger_angle - charger_pose_transform[2]
    
    # plt.scatter(charger_pos_transformed[0],charger_pos_transformed[1],marker=(3,0,90+charger_angle_transformed*180/np.pi),s=200, linewidths=30)
    
    x = (  2 + (charger_pos_transformed[0] - min_x) * scale) * upscale
    y = ( -3 + height - ((charger_pos_transformed[1] - min_y) * scale)) * upscale
    base_radius = 4 * upscale

    draw = PIL.ImageDraw.Draw(image)
    draw.ellipse((x - base_radius, y - base_radius, x + base_radius, y + base_radius), fill = 'blue', outline ='blue')

    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()

if __name__ == "__main__":
    import sys

    with open(sys.argv[1], "rb") as fp:
        with open(sys.argv[2], "wb") as fpout:
            fpout.write(plot_map(fp.read()))
