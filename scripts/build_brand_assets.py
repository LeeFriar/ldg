from pathlib import Path
from PIL import Image, ImageChops

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "public" / "brand"
OUT.mkdir(parents=True, exist_ok=True)

ICON_SRC = Path(r"C:\Users\MrPC\.codex\generated_images\01a02010-7a15-7b71-8353-1d963cfad082\exec-136c88c2-2e1b-4898-91d2-b891dca622a8.png")
LOCKUP_SRC = Path(r"C:\Users\MrPC\.codex\generated_images\01a02010-7a15-7b71-8353-1d963cfad082\exec-df209dd7-1a7d-495b-90dd-dd22b5c022de.png")


def contain(image: Image.Image, size: tuple[int, int], padding: int = 0) -> Image.Image:
    canvas = Image.new("RGBA", size, (0, 0, 0, 0))
    available = (size[0] - padding * 2, size[1] - padding * 2)
    copy = image.copy()
    copy.thumbnail(available, Image.Resampling.LANCZOS)
    x = (size[0] - copy.width) // 2
    y = (size[1] - copy.height) // 2
    canvas.alpha_composite(copy, (x, y))
    return canvas


def remove_light_checkerboard(image: Image.Image, margin: int = 24) -> Image.Image:
    """Convert the generator's neutral light preview grid to real transparency."""
    image = image.convert("RGBA")
    pixels = image.load()
    for y in range(image.height):
        for x in range(image.width):
            r, g, b, _ = pixels[x, y]
            spread = max(r, g, b) - min(r, g, b)
            # Grid cells are near-neutral and bright; brand navy and gold are not.
            alpha = 0 if min(r, g, b) >= 218 and spread <= 18 else 255
            pixels[x, y] = (r, g, b, alpha)
    bbox = image.getchannel("A").getbbox()
    if not bbox:
        raise ValueError("No foreground pixels found")
    left = max(0, bbox[0] - margin)
    top = max(0, bbox[1] - margin)
    right = min(image.width, bbox[2] + margin)
    bottom = min(image.height, bbox[3] + margin)
    return image.crop((left, top, right, bottom))


icon = remove_light_checkerboard(Image.open(ICON_SRC))
lockup = remove_light_checkerboard(Image.open(LOCKUP_SRC))

# Preserve the high-resolution editable web masters.
icon.save(OUT / "ldg-mark.png", optimize=True)
lockup.save(OUT / "ldg-logo-horizontal.png", optimize=True)

sizes = {
    "favicon-16x16.png": (16, 16),
    "favicon-32x32.png": (32, 32),
    "favicon-48x48.png": (48, 48),
    "apple-touch-icon.png": (180, 180),
    "android-chrome-192x192.png": (192, 192),
    "android-chrome-512x512.png": (512, 512),
}
for filename, size in sizes.items():
    contain(icon, size, max(1, size[0] // 16)).save(OUT / filename, optimize=True)

favicon_frames = [contain(icon, (n, n), max(1, n // 16)) for n in (16, 32, 48)]
favicon_frames[0].save(
    OUT / "favicon.ico",
    format="ICO",
    append_images=favicon_frames[1:],
    sizes=[(16, 16), (32, 32), (48, 48)],
)

# A navbar-friendly derivative capped at 640 px wide.
header = lockup.copy()
header.thumbnail((640, 240), Image.Resampling.LANCZOS)
header.save(OUT / "ldg-logo-header.png", optimize=True)

for path in sorted(OUT.iterdir()):
    with Image.open(path) as image:
        print(f"{path.name}: {image.size[0]}x{image.size[1]} {image.mode}")
