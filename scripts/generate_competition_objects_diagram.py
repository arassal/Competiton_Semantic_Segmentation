from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'docs' / 'competition_objects_pipeline.png'


def font(size, bold=False):
    name = 'DejaVuSans-Bold.ttf' if bold else 'DejaVuSans.ttf'
    path = Path('/usr/share/fonts/truetype/dejavu') / name
    if path.exists():
        return ImageFont.truetype(str(path), size)
    return ImageFont.load_default()


def box(draw, xy, title, lines, fill, accent):
    x0, y0, x1, y1 = xy
    draw.rounded_rectangle(xy, radius=8, fill=fill, outline=accent, width=2)
    draw.rectangle((x0, y0, x0 + 10, y1), fill=accent)
    draw.text((x0 + 24, y0 + 18), title, font=font(28, True), fill=(24, 30, 38))
    y = y0 + 62
    for line in lines:
        draw.text((x0 + 24, y), line, font=font(19), fill=(50, 62, 72))
        y += 29


def arrow(draw, start, end):
    draw.line((start, end), fill=(52, 65, 78), width=4)
    ex, ey = end
    sx, sy = start
    if abs(ex - sx) > abs(ey - sy):
        d = 1 if ex > sx else -1
        pts = [(ex, ey), (ex - 14 * d, ey - 8), (ex - 14 * d, ey + 8)]
    else:
        d = 1 if ey > sy else -1
        pts = [(ex, ey), (ex - 8, ey - 14 * d), (ex + 8, ey - 14 * d)]
    draw.polygon(pts, fill=(52, 65, 78))


def main():
    img = Image.new('RGB', (1800, 980), (248, 250, 252))
    draw = ImageDraw.Draw(img)
    draw.text((70, 46), 'Competition Object Detection Pipeline',
              font=font(44, True), fill=(24, 30, 38))
    draw.text((72, 103), 'Traffic cones, people, signs, lights, and vehicles through a ROS 2 Jazzy bridge',
              font=font(24), fill=(78, 90, 102))

    box(draw, (70, 190, 450, 410), 'Input Frames',
        ['demo image folder today', 'RealSense RGB next', 'camera_color_optical_frame'],
        (236, 246, 255), (50, 133, 201))
    box(draw, (550, 190, 930, 410), 'YOLOv8 Model',
        ['Roboflow Logistics', 'included 6 MB checkpoint', 'native traffic cone class'],
        (238, 249, 240), (43, 150, 87))
    box(draw, (1030, 190, 1410, 410), 'ROS 2 Node',
        ['competition_objects_node', 'rclpy + cv_bridge', 'JSON detections'],
        (255, 244, 232), (219, 123, 43))
    box(draw, (70, 560, 450, 780), 'Published Topics',
        ['/seg_ros/.../input_image', '/seg_ros/.../annotated_image', '/seg_ros/.../detections'],
        (248, 242, 255), (132, 80, 177))
    box(draw, (550, 560, 930, 780), 'Proof Results',
        ['72 road frames: 0 false cones', '12 cone road scenes: 59 cones', 'cone eval F1: 0.8299'],
        (236, 249, 249), (36, 147, 158))
    box(draw, (1030, 560, 1410, 780), 'Navigation Use',
        ['cones as obstacles/cues', 'people as safety obstacles', 'keep depth/geometric safety'],
        (248, 248, 238), (155, 148, 50))

    arrow(draw, (450, 300), (550, 300))
    arrow(draw, (930, 300), (1030, 300))
    arrow(draw, (1220, 410), (1220, 560))
    arrow(draw, (1030, 670), (930, 670))
    arrow(draw, (550, 670), (450, 670))
    arrow(draw, (260, 560), (260, 410))

    OUT.parent.mkdir(parents=True, exist_ok=True)
    img.save(OUT)
    print(OUT)


if __name__ == '__main__':
    main()
