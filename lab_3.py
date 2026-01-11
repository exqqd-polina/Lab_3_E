import math
import xml.etree.ElementTree as ET
from PIL import Image, ImageDraw
import re


def parse_svg(filename):
    try:
        tree = ET.parse(filename)
        root = tree.getroot()
        for desc in root.iter('{http://www.w3.org/2000/svg}desc'):
            desc_text = desc.text
            if desc_text:
                match = re.search(r'радиус[а\s:]*(\d+)', desc_text, re.IGNORECASE)
                if match:
                    return int(match.group(1))
        return None
    except Exception as e:
        print(f"Ошибка при чтении SVG файла: {e}")
        return None


def create_star_segments(radius, center_x=300, center_y=200):
    n = 8
    m = 3
    vertices = []
    for i in range(n):
        angle = 2 * math.pi * i / n - math.pi / 2
        x = center_x + radius * math.cos(angle)
        y = center_y + radius * math.sin(angle)
        vertices.append((int(round(x)), int(round(y))))
    segments = []
    connected = set()

    for i in range(n):
        j = (i + m) % n
        edge_id = tuple(sorted((i, j)))
        if edge_id not in connected:
            connected.add(edge_id)
            x1, y1 = vertices[i]
            x2, y2 = vertices[j]
            segments.append((x1, y1, x2, y2))
    return segments, vertices


def draw_pixel_color(image_rgb, x, y, color):
    if 0 <= y < len(image_rgb) and 0 <= x < len(image_rgb[0]):
        image_rgb[y][x] = color


def draw_line_dda_color(image_rgb, x1, y1, x2, y2, color):
    dx = x2 - x1
    dy = y2 - y1
    steps = max(abs(dx), abs(dy))
    if steps == 0:
        draw_pixel_color(image_rgb, x1, y1, color)
        return
    x_inc, y_inc = dx / steps, dy / steps
    x, y = float(x1), float(y1)
    for _ in range(steps + 1):
        draw_pixel_color(image_rgb, round(x), round(y), color)
        x += x_inc
        y += y_inc


def draw_line_bresenham_float_color(image_rgb, x1, y1, x2, y2, color):
    dx, dy = x2 - x1, y2 - y1
    steep = abs(dy) > abs(dx)
    if steep: x1, y1, x2, y2 = y1, x1, y2, x2
    if x1 > x2: x1, x2, y1, y2 = x2, x1, y2, y1
    dx, dy = x2 - x1, abs(y2 - y1)
    error, y, ystep = 0.0, y1, 1 if y1 < y2 else -1
    for x in range(x1, x2 + 1):
        if steep:
            draw_pixel_color(image_rgb, y, x, color)
        else:
            draw_pixel_color(image_rgb, x, y, color)
        error += dy / dx if dx != 0 else 0
        if error >= 0.5:
            y += ystep
            error -= 1.0


def draw_line_bresenham_int_color(image_rgb, x1, y1, x2, y2, color):
    dx, dy = abs(x2 - x1), abs(y2 - y1)
    sx, sy = 1 if x1 < x2 else -1, 1 if y1 < y2 else -1
    err = dx - dy
    while True:
        draw_pixel_color(image_rgb, x1, y1, color)
        if x1 == x2 and y1 == y2: break
        e2 = 2 * err
        if e2 > -dy:
            err -= dy
            x1 += sx
        if e2 < dx:
            err += dx
            y1 += sy


def draw_line_library_color(image_rgb, x1, y1, x2, y2, width, height, color):
    temp_img = Image.new('RGB', (width, height), (0, 0, 0))
    draw = ImageDraw.Draw(temp_img)
    draw.line([(x1, y1), (x2, y2)], fill=color, width=1)
    for y in range(height):
        for x in range(width):
            pixel_color = temp_img.getpixel((x, y))
            if pixel_color != (0, 0, 0):
                draw_pixel_color(image_rgb, x, y, pixel_color)


def write_ppm_p3_color(filename, image_rgb, width, height):
    with open(filename, 'w') as f:
        f.write(f"P3\n")
        f.write(f"{width} {height}\n")
        f.write(f"255\n")
        for y in range(height):
            row = []
            for x in range(width):
                r, g, b = image_rgb[y][x]
                row.extend([r, g, b])
            f.write(" ".join(map(str, row)) + "\n")
    print(f"  PPM файл сохранен: {filename}")


def save_as_png_color(image_rgb, width, height, filename="star_octagon_colors.png"):
    pil_image = Image.new('RGB', (width, height), color='black')
    pixels = pil_image.load()
    for y in range(height):
        for x in range(width):
            pixels[x, y] = image_rgb[y][x]
    pil_image.save(filename)
    print(f"  PNG файл сохранен: {filename}")


def draw_vertices(image_rgb, vertices, color=(255, 255, 255)):
    for x, y in vertices:
        for dx in range(-2, 3):
            for dy in range(-2, 3):
                if dx * dx + dy * dy <= 4:
                    draw_pixel_color(image_rgb, x + dx, y + dy, color)


def draw_center(image_rgb, center_x, center_y, color=(0, 255, 255)):
    for dx in range(-3, 4):
        for dy in range(-3, 4):
            if abs(dx) + abs(dy) <= 4:
                draw_pixel_color(image_rgb, center_x + dx, center_y + dy, color)


def main():
    SVG_FILE = "star_octagon.svg"
    WIDTH, HEIGHT = 600, 400
    CENTER_X, CENTER_Y = 300, 200

    print(f"\n1. Чтение радиуса из '{SVG_FILE}'...")
    radius = parse_svg(SVG_FILE)

    if radius is None:
        print("Ошибка: не удалось найти радиус в SVG файле.")
        return

    print(f"   Радиус описанной окружности: {radius}")
    print(f"   Центр звезды: ({CENTER_X}, {CENTER_Y})")

    print("\n2. Создание отрезков звезды...")
    segments, vertices = create_star_segments(radius, CENTER_X, CENTER_Y)

    print(f"   Создано {len(segments)} отрезков")
    print(f"   Вершины звезды:")
    for i, (x, y) in enumerate(vertices):
        angle = i * 45
        print(f"     V{i + 1} ({angle}°): ({x}, {y})")

    print("\n3. Создание цветного холста...")
    image_rgb = [[(0, 0, 0) for _ in range(WIDTH)] for _ in range(HEIGHT)]

    algorithms_config = [
        {
            "name": "Целочисленный Брезенхем",
            "color": (255, 0, 0),
            "function": draw_line_bresenham_int_color,
            "segments_indices": [0, 4]
        },
        {
            "name": "ЦДА",
            "color": (0, 255, 0),
            "function": draw_line_dda_color,
            "segments_indices": [1, 5]
        },
        {
            "name": "Вещественный Брезенхем",
            "color": (0, 0, 255),
            "function": draw_line_bresenham_float_color,
            "segments_indices": [2, 6]
        },
        {
            "name": "Pillow",
            "color": (255, 255, 0),
            "function": lambda img, x1, y1, x2, y2, col: draw_line_library_color(img, x1, y1, x2, y2, WIDTH, HEIGHT,
                                                                                 col),
            "segments_indices": [3, 7]
        }
    ]

    print("\n4. Отрисовка отрезков звезды...")

    for algo_config in algorithms_config:
        algo_name = algo_config["name"]
        color = algo_config["color"]
        algo_func = algo_config["function"]
        indices = algo_config["segments_indices"]

        print(f"   {algo_name}: RGB{color}")

        for idx in indices:
            if idx < len(segments):
                x1, y1, x2, y2 = segments[idx]
                print(f"     Отрезок {idx + 1}: ({x1},{y1}) - ({x2},{y2})")
                if "Pillow" in algo_name:
                    algo_func(image_rgb, x1, y1, x2, y2, color)
                else:
                    algo_func(image_rgb, x1, y1, x2, y2, color)

    print("\n5. Рисование вершин звезды...")
    draw_vertices(image_rgb, vertices, (255, 255, 255))
    print("   Вершины нарисованы (белый цвет)")

    print("\n6. Рисование центра...")
    draw_center(image_rgb, CENTER_X, CENTER_Y, (0, 255, 255))
    print("   Центр нарисован (голубой цвет)")

    print("\n7. Сохранение в форматы PPM P3 и PNG...")

    ppm_filename = f"star.ppm"
    write_ppm_p3_color(ppm_filename, image_rgb, WIDTH, HEIGHT)

    png_filename = f"star.png"
    save_as_png_color(image_rgb, WIDTH, HEIGHT, png_filename)

    print("\n8. Информация о звездчатом восьмиугольнике:")
    print(f"   - Радиус описанной окружности: {radius}")
    print(f"   - Центр: ({CENTER_X}, {CENTER_Y})")
    print(f"   - Количество вершин: 8")
    print(f"   - Количество отрезков: {len(segments)}")
    print(f"   - Тип звезды: связный восьмиугольник (шаг 3)")

    if segments:
        x1, y1, x2, y2 = segments[0]
        length = math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)
        print(f"   - Длина отрезка: {length:.1f} пикселей")
        print(f"   - Угол между вершинами: {360 / 8}°")

        print(f"\n   Координаты вершин (относительно центра):")
        for i, (x, y) in enumerate(vertices):
            rel_x = x - CENTER_X
            rel_y = y - CENTER_Y
            angle_deg = i * 45
            print(f"     V{i + 1} ({angle_deg}°): ({rel_x:+4d}, {rel_y:+4d})")


    print("\n" + "=" * 80)
    print("ГОТОВО! Созданы файлы:")
    print(f"  - {ppm_filename} (цветной PPM P3, ASCII)")
    print(f"  - {png_filename} (цветной PNG)")
    print("=" * 80)


if __name__ == "__main__":
    main()