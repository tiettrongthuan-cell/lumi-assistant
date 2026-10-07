"""
make_logo.py — Vẽ logo ngôi sao cho Lumi Assistant.
Nền TRONG SUỐT (PNG alpha).
Chạy: python make_logo.py
Xuất:
  - logo.png           (512x512, nền trong suốt)
  - logo_256.png       (256x256)
  - logo_preview_dark.png   (xem trên nền tối)
  - logo_preview_light.png  (xem trên nền sáng)
"""
import os
import math
from PIL import Image, ImageDraw, ImageFilter

# ─── Cấu hình ────────────────────────────────────────────────
SIZE = 1024                       # Vẽ to rồi downscale cho mượt
STAR_POINTS = 4                   # 4 cánh (kiểu ✨). Đổi 5 = sao thường, 6 = bông tuyết
SPIKY = 0.28                      # Tỉ lệ cánh ngắn/dài (0.2 = nhọn, 0.5 = đều)
ROTATION = -90                    # Quay sao (độ). -90 = cánh nhọn lên trên
GLOW = True                       # Có hào quang phát sáng không

# Màu (Ocean × Galaxy)
CORE_COLOR   = (255, 255, 255)    # lõi trắng
INNER_COLOR  = (155, 231, 255)    # #9BE7FF cyan sáng
OUTER_COLOR  = (124, 77, 255)     # #7C4DFF tím vũ trụ
GLOW_COLOR   = (120, 220, 255)    # hào quang cyan


# ═══════════════════════════════════════════════════════════════
#  VẼ NGÔI SAO
# ═══════════════════════════════════════════════════════════════
def star_points(cx, cy, outer_r, inner_r, points, rotation_deg=-90):
    """Trả list điểm của ngôi sao."""
    pts = []
    rot = math.radians(rotation_deg)
    total = points * 2
    for i in range(total):
        ang = rot + (math.pi * 2 * i) / total
        r = outer_r if i % 2 == 0 else inner_r
        x = cx + r * math.cos(ang)
        y = cy + r * math.sin(ang)
        pts.append((x, y))
    return pts


def radial_gradient_square(size, c_center, c_edge):
    """Gradient tròn từ tâm ra rìa (dùng mask)."""
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    px = img.load()
    cx = cy = size / 2
    max_d = math.hypot(cx, cy)
    for y in range(size):
        for x in range(size):
            d = math.hypot(x - cx, y - cy) / max_d
            d = min(1.0, d)
            r = int(c_center[0] + (c_edge[0] - c_center[0]) * d)
            g = int(c_center[1] + (c_edge[1] - c_center[1]) * d)
            b = int(c_center[2] + (c_edge[2] - c_center[2]) * d)
            px[x, y] = (r, g, b, 255)
    return img


def make_star_mask(size, points, spiky, rotation):
    """Mask đen trắng của ngôi sao."""
    mask = Image.new("L", (size, size), 0)
    d = ImageDraw.Draw(mask)
    cx = cy = size / 2
    outer_r = size * 0.44
    inner_r = outer_r * spiky
    pts = star_points(cx, cy, outer_r, inner_r, points, rotation)
    d.polygon(pts, fill=255)
    return mask


def make_glow(size, points, spiky, rotation, color, blur_amount):
    """Hào quang: sao mờ phóng to + blur."""
    glow = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(glow)
    cx = cy = size / 2
    outer_r = size * 0.44
    inner_r = outer_r * spiky
    pts = star_points(cx, cy, outer_r * 1.3, inner_r * 1.3, points, rotation)
    d.polygon(pts, fill=(*color, 160))
    glow = glow.filter(ImageFilter.GaussianBlur(radius=blur_amount))
    return glow


def make_star(size):
    canvas = Image.new("RGBA", (size, size), (0, 0, 0, 0))

    # 1. Hào quang phía sau (nếu bật)
    if GLOW:
        glow1 = make_glow(size, STAR_POINTS, SPIKY, ROTATION, GLOW_COLOR, size * 0.08)
        glow2 = make_glow(size, STAR_POINTS, SPIKY, ROTATION, OUTER_COLOR, size * 0.15)
        canvas.alpha_composite(glow2)
        canvas.alpha_composite(glow1)

    # 2. Gradient màu bên trong ngôi sao (tím rìa → cyan giữa)
    grad = radial_gradient_square(size, INNER_COLOR, OUTER_COLOR)

    # 3. Mask của ngôi sao
    mask = make_star_mask(size, STAR_POINTS, SPIKY, ROTATION)

    # 4. Ghép gradient + mask
    star_layer = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    star_layer.paste(grad, (0, 0), mask)

    # 5. Lõi trắng phát sáng ở giữa
    core = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(core)
    cx = cy = size / 2
    core_r = size * 0.07
    d.ellipse([cx - core_r, cy - core_r, cx + core_r, cy + core_r],
              fill=(*CORE_COLOR, 255))
    core = core.filter(ImageFilter.GaussianBlur(radius=size * 0.02))

    star_layer.alpha_composite(core)
    canvas.alpha_composite(star_layer)

    # 6. Vài đốm sáng nhỏ (sparkle) xung quanh
    spark = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    ds = ImageDraw.Draw(spark)
    for angle_deg, dist, rad in [(45, 0.42, 0.012), (135, 0.40, 0.009),
                                  (225, 0.44, 0.011), (315, 0.40, 0.008)]:
        ang = math.radians(angle_deg)
        sx = cx + math.cos(ang) * size * dist
        sy = cy + math.sin(ang) * size * dist
        sr = size * rad
        ds.ellipse([sx - sr, sy - sr, sx + sr, sy + sr],
                   fill=(*INNER_COLOR, 200))
    spark = spark.filter(ImageFilter.GaussianBlur(radius=size * 0.004))
    canvas.alpha_composite(spark)

    return canvas


# ═══════════════════════════════════════════════════════════════
#  PREVIEW
# ═══════════════════════════════════════════════════════════════
def make_preview(logo, bg_color, path):
    """Ghép logo lên nền để xem trước."""
    prev = Image.new("RGBA", logo.size, (*bg_color, 255))
    prev.alpha_composite(logo)
    prev.convert("RGB").save(path, "PNG")


# ═══════════════════════════════════════════════════════════════
#  MAIN
# ═══════════════════════════════════════════════════════════════
def main():
    print("[LOGO] Đang vẽ...")
    master = make_star(SIZE)

    # Logo chính — nền trong suốt
    master.resize((512, 512), Image.LANCZOS).save("logo.png", "PNG")
    print("[LOGO] ✅ logo.png (512, no background)")

    # Bản 256 để dùng cho UI nhỏ
    master.resize((256, 256), Image.LANCZOS).save("logo_256.png", "PNG")
    print("[LOGO] ✅ logo_256.png (256)")

    # Preview trên nền tối
    make_preview(master, (10, 15, 30), "logo_preview_dark.png")
    print("[LOGO] ✅ logo_preview_dark.png")

    # Preview trên nền sáng
    make_preview(master, (245, 249, 253), "logo_preview_light.png")
    print("[LOGO] ✅ logo_preview_light.png")

    print("\n→ Mở logo_preview_dark.png hoặc logo_preview_light.png để xem thử.")


if __name__ == "__main__":
    main()