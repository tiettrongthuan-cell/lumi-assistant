"""
make_logo.py — Gargantua black hole logo (Interstellar style)
8 layers: stars, nebula, disk, lensing, photon ring, event horizon, bloom, halo
"""
import os
import numpy as np
from PIL import Image, ImageFilter

SIZE = 1024


def render_gargantua(size=SIZE):
    # ==============================================================
    #  Coordinate grid [-1, 1]
    # ==============================================================
    ys, xs = np.mgrid[0:size, 0:size].astype(np.float32)
    cx = cy = (size - 1) / 2.0
    X = (xs - cx) / (size / 2.0)
    Y = (ys - cy) / (size / 2.0)
    R = np.sqrt(X * X + Y * Y)
    R_safe = np.maximum(R, 1e-6)

    # ==============================================================
    #  1. Deep space background
    # ==============================================================
    canvas = np.zeros((size, size, 3), dtype=np.float32)
    radial = np.clip(1.0 - R / 1.6, 0.0, 1.0) ** 1.6
    canvas[..., 0] = 0.008 + 0.030 * radial
    canvas[..., 1] = 0.012 + 0.045 * radial
    canvas[..., 2] = 0.030 + 0.090 * radial

    # ==============================================================
    #  2. Starfield — 3200 stars, 3 color tints
    # ==============================================================
    rng = np.random.default_rng(2024)
    n_stars = 3200
    sx = rng.integers(0, size, n_stars)
    sy = rng.integers(0, size, n_stars)
    sb = rng.uniform(0.20, 1.00, n_stars).astype(np.float32)
    tint = rng.random(n_stars)

    star_rgb = np.zeros((n_stars, 3), dtype=np.float32)
    star_rgb[:, 0] = np.where(tint < 0.70, 1.00,
                     np.where(tint < 0.85, 0.70, 1.00))
    star_rgb[:, 1] = np.where(tint < 0.70, 1.00,
                     np.where(tint < 0.85, 0.85, 0.85))
    star_rgb[:, 2] = np.where(tint < 0.70, 1.00,
                     np.where(tint < 0.85, 1.00, 0.60))

    star_buf = np.zeros((size, size), dtype=np.float32)
    star_buf[sy, sx] = sb
    col_buf = np.zeros((size, size, 3), dtype=np.float32)
    col_buf[sy, sx] = star_rgb

    # Soft glow
    star_buf = np.array(
        Image.fromarray((star_buf * 255).astype(np.uint8))
        .filter(ImageFilter.GaussianBlur(0.6))
    ).astype(np.float32) / 255.0
    col_buf = np.array(
        Image.fromarray((col_buf * 255).astype(np.uint8))
        .filter(ImageFilter.GaussianBlur(0.6))
    ).astype(np.float32) / 255.0

    sa = star_buf[..., None]
    canvas = canvas * (1.0 - sa) + col_buf * sa

    # ==============================================================
    #  3. Nebula glow — 3 clouds
    # ==============================================================
    for nx, ny, r, g, b, sig, amp in [
        (-0.35, -0.25, 0.10, 0.25, 0.55, 0.55, 0.16),
        ( 0.40,  0.30, 0.35, 0.15, 0.55, 0.50, 0.12),
        ( 0.00,  0.45, 0.10, 0.35, 0.55, 0.40, 0.09),
    ]:
        dx, dy = X - nx, Y - ny
        gg = np.exp(-(dx * dx + dy * dy) / (2 * sig * sig)).astype(np.float32) * amp
        canvas[..., 0] += r * gg
        canvas[..., 1] += g * gg
        canvas[..., 2] += b * gg
    canvas = np.clip(canvas, 0.0, 1.0)

    # ==============================================================
    #  4. Accretion disk (flat, granular, doppler-beamed)
    # ==============================================================
    R_HORIZON   = 0.20
    R_PHOTON    = 0.255
    R_DISK_IN   = 0.27
    R_DISK_OUT  = 0.62
    DISK_SQUASH = 0.20

    RD = np.sqrt(X * X + (Y / DISK_SQUASH) ** 2)
    t = np.clip((RD - R_DISK_IN) / (R_DISK_OUT - R_DISK_IN), 0.0, 1.0)
    disk_mask = ((RD >= R_DISK_IN) & (RD <= R_DISK_OUT)).astype(np.float32)

    falloff_in = np.clip((RD - R_DISK_IN) / 0.04, 0.0, 1.0)
    falloff_out = np.clip((R_DISK_OUT - RD) / 0.18, 0.0, 1.0)
    falloff = falloff_in * falloff_out

    # Texture: smooth noise + swirl
    noise = rng.random((size, size)).astype(np.float32)
    noise = np.array(
        Image.fromarray((noise * 255).astype(np.uint8))
        .filter(ImageFilter.GaussianBlur(1.5))
    ).astype(np.float32) / 255.0
    theta = np.arctan2(Y / DISK_SQUASH, X)
    swirl = 0.5 + 0.5 * np.sin(12.0 * theta + 6.0 * RD)
    texture = np.clip(0.45 + 0.35 * noise + 0.20 * swirl, 0.0, 1.0)

    inten = disk_mask * falloff * texture
    doppler = 0.65 + 0.60 * np.clip(-X / R_safe, -1.0, 1.0)
    inten = inten * doppler

    # Color: white-hot → orange → deep red
    hot = np.array([1.00, 0.98, 0.92], dtype=np.float32)
    mid = np.array([1.00, 0.72, 0.35], dtype=np.float32)
    cool = np.array([0.65, 0.25, 0.10], dtype=np.float32)
    k1 = np.clip(t * 2.0, 0.0, 1.0)[..., None]
    k2 = np.clip((t - 0.5) * 2.0, 0.0, 1.0)[..., None]
    disk_color = hot * (1 - k1) + mid * k1
    disk_color = disk_color * (1 - k2 * 0.85) + cool * (k2 * 0.85)

    disk_a = np.clip(inten, 0.0, 1.0)[..., None]
    canvas = canvas * (1 - disk_a) + disk_color * disk_a

    # ==============================================================
    #  5. Lensing arcs — light from behind the black hole
    # ==============================================================
    arc_r = (R_HORIZON + R_PHOTON) / 2.0
    arc_w = 0.030
    arc_mask = np.clip(1.0 - np.abs(R - arc_r) / arc_w, 0.0, 1.0)
    vert = np.abs(Y / R_safe) ** 1.2
    arc_mask = arc_mask * (0.35 + 0.65 * vert) * doppler * 1.15
    arc_color = np.array([1.00, 0.90, 0.80], dtype=np.float32)
    arc_a = np.clip(arc_mask, 0.0, 1.0)[..., None]
    canvas = canvas * (1 - arc_a) + arc_color * arc_a

    # Second fine arc
    arc2_r = R_HORIZON + 0.085
    arc2_mask = np.clip(1.0 - np.abs(R - arc2_r) / 0.012, 0.0, 1.0)
    arc2_mask = arc2_mask * (np.abs(Y / R_safe) ** 1.6) * doppler * 0.7
    arc2_a = np.clip(arc2_mask, 0.0, 1.0)[..., None]
    canvas = canvas * (1 - arc2_a) + np.array([1.0, 0.85, 0.70]) * arc2_a

    # ==============================================================
    #  6. Photon ring + outer halo
    # ==============================================================
    photon_mask = np.clip(1.0 - np.abs(R - R_PHOTON) / 0.010, 0.0, 1.0)
    photon_mask = photon_mask * (0.55 + 0.80 * np.clip(-X / R_safe, 0.0, 1.0))
    photon_a = np.clip(photon_mask, 0.0, 1.0)[..., None]
    canvas = canvas * (1 - photon_a) + np.array([1.00, 0.98, 0.92]) * photon_a

    halo = np.exp(-((R - R_PHOTON) / 0.09) ** 2).astype(np.float32)
    halo *= np.clip(1.0 - (R - R_PHOTON) / 0.30, 0.0, 1.0) * 0.55
    halo_a = halo[..., None]
    canvas = canvas * (1 - halo_a) + np.array([1.0, 0.85, 0.70]) * halo_a

    # ==============================================================
    #  7. Event horizon — pure black
    # ==============================================================
    eh = np.clip((R_HORIZON - R) / 0.006, 0.0, 1.0).astype(np.float32)
    eh = np.maximum(eh, (R < R_HORIZON).astype(np.float32))
    eh_a = eh[..., None]
    canvas = canvas * (1 - eh_a)

    # ==============================================================
    #  8. Outer bloom
    # ==============================================================
    bloom = np.exp(-((R - 0.30) / 0.25) ** 2).astype(np.float32) * 0.35
    bloom += np.exp(-((R - 0.55) / 0.20) ** 2).astype(np.float32) * 0.15
    bloom_a = bloom[..., None]
    canvas = canvas + bloom_a * np.array([0.90, 0.70, 0.50])

    return np.clip(canvas, 0.0, 1.0)


# ==================================================================
#  POST-PROCESSING
# ==================================================================
def to_pil_rgba(arr, alpha_mode="full"):
    """arr: HxWx3 float [0,1] → PIL RGBA"""
    rgb = (arr * 255).astype(np.uint8)
    if alpha_mode == "full":
        a = np.full(rgb.shape[:2], 255, dtype=np.uint8)
    else:  # transparent by luminance
        lum = arr.mean(axis=2)
        a = np.clip((lum - 0.015) / 0.85, 0.0, 1.0) ** 0.85
        a = (a * 255).astype(np.uint8)
    return Image.fromarray(np.dstack([rgb, a]), "RGBA")


def add_bloom(pil_img, strength=0.9, radius_factor=0.012):
    """Soft bloom pass for extra glow."""
    arr = np.array(pil_img).astype(np.float32)
    lum = arr[..., :3].mean(axis=2)
    ba = arr.copy()
    ba[..., 3] = np.clip(lum * 1.6, 0, 255).astype(np.uint8)
    bloom = Image.fromarray(ba.astype(np.uint8), "RGBA")
    bloom = bloom.filter(ImageFilter.GaussianBlur(SIZE * radius_factor))
    ba2 = np.array(bloom).astype(np.float32)
    ba2[..., :3] *= strength
    bloom = Image.fromarray(np.clip(ba2, 0, 255).astype(np.uint8), "RGBA")
    return Image.alpha_composite(bloom, pil_img)


# ==================================================================
#  MAIN
# ==================================================================
def main():
    print(f"[LOGO] Rendering Gargantua {SIZE}x{SIZE}... (10-20s)")
    arr = render_gargantua(SIZE)
    print("[LOGO] Composite bloom...")

    # Full background version (đẹp nhất, giữ nguyên nền đen)
    full = to_pil_rgba(arr, alpha_mode="full")
    full = add_bloom(full, strength=0.85)
    full.resize((1024, 1024), Image.LANCZOS).save("logo_dark.png", "PNG")
    print("[LOGO] ✅ logo_dark.png (nền đen đầy đủ)")

    # Transparent version
    trans = to_pil_rgba(arr, alpha_mode="luminance")
    trans = add_bloom(trans, strength=0.7)
    trans.resize((1024, 1024), Image.LANCZOS).save("logo.png", "PNG")
    trans.resize((256, 256), Image.LANCZOS).save("logo_256.png", "PNG")
    print("[LOGO] ✅ logo.png + logo_256.png (trong suốt)")

    # ICO cho Windows
    trans.resize((256, 256), Image.LANCZOS).save(
        "icon.ico", format="ICO",
        sizes=[(16,16),(24,24),(32,32),(48,48),(64,64),(128,128),(256,256)]
    )
    trans.resize((256, 256), Image.LANCZOS).save("icon.png", "PNG")
    print("[LOGO] ✅ icon.ico + icon.png")

    print("\n→ Mở logo_dark.png xem bản đầy đủ, logo.png xem bản trong suốt.")


if __name__ == "__main__":
    main()