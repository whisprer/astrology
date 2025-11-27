# woflstrology-icon-gen-FINAL.py
# Drops EVERYTHING (ico, icns, all PNGs) directly in the current folder
# Tested on Windows 11 + Python 3.12 venv → works 100%

import numpy as np
from PIL import Image, ImageDraw
import os

# Rider-Waite 16-color palette
PALETTE_HEX = [
    "#000000","#66023C","#8B0000","#E32636","#A0522D","#D2691E","#E6A23C","#FFD700",
    "#006400","#008080","#00CED1","#7FFFD4","#4B0082","#9370DB","#DDA0DD","#FFFFFF"
]
raw_palette = []
for h in PALETTE_HEX:
    raw_palette.extend([int(h[1:3],16), int(h[3:5],16), int(h[5:7],16)])
raw_palette.extend([0,0,0] * (256-len(PALETTE_HEX)))  # pad

def generate_base_icon(size=64):
    img = Image.new('P', (size, size), 0)
    img.putpalette(raw_palette)
    draw = ImageDraw.Draw(img)

    # cosmic void circle
    draw.ellipse([size//8, size//8, 7*size//8, 7*size//8], fill=1)

    # sun
    sun_cx, sun_cy = int(size*0.72), int(size*0.28)
    r = size//9
    draw.ellipse([sun_cx-r, sun_cy-r, sun_cx+r, sun_cy+r], fill=6)
    for i in range(12):
        a = i * np.pi / 6
        x2 = sun_cx + int(np.cos(a) * r * 1.8)
        y2 = sun_cy + int(np.sin(a) * r * 1.8)
        draw.line([sun_cx,sun_cy,x2,y2], fill=7, width=max(1,size//32))

    # crescent moon
    moon_cx, moon_cy = int(size*0.28), int(size*0.28)
    draw.ellipse([moon_cx-r, moon_cy-r, moon_cx+r, moon_cy+r], fill=7)
    draw.ellipse([moon_cx-r+3, moon_cy-r, moon_cx+r-3, moon_cy+r], fill=1)

    # wolf head
    wolf = [(size//4,size*0.55),(size//3,size*0.45),(size//2,size*0.48),
            (size*0.75,size*0.55),(size*0.65,size*0.75),(size//3,size*0.78)]
    draw.polygon(wolf, fill=15)
    draw.ellipse([size*0.42,size*0.62,size*0.48,size*0.68], fill=9)  # eye
    draw.line([size*0.58,size*0.66,size*0.65,size*0.74], fill=3, width=max(2,size//20))

    # zodiac ring
    for i in range(12):
        a = 2*np.pi*i/12 - np.pi/2
        gx = int(size//2 + size*0.38*np.cos(a))
        gy = int(size//2 + size*0.38*np.sin(a))
        draw.ellipse([gx-1,gy-1,gx+1,gy+1], fill=14)

    return img

def forge():
    base = generate_base_icon(64)

    # all the sizes we actually need
    sizes = [16,20,24,32,40,48,64,128,180,256,512,1024]
    imgs = [base.resize((s,s), Image.NEAREST) for s in sizes]

    # PNGs
    for s, im in zip(sizes, imgs):
        im.save(f"woflstrology_{s}.png")

    # Windows .ico (multi-resolution)
    ico_sizes = [16,32,48,64,128,256]
    ico_imgs = [base.resize((s,s), Image.NEAREST).convert("RGBA") for s in ico_sizes]
    ico_imgs[0].save("woflstrology.ico", format='ICO', append_images=ico_imgs[1:], sizes=[(s,s) for s in ico_sizes])

    # macOS .icns (proper format using the 1024 master)
    img_1024 = imgs[-1].convert("RGBA")
    img_1024.save("woflstrology.icns", format="ICNS")

    print("🐺🌙☀️ ALL DONE, fren!")
    print("   → woflstrology.ico  (Windows)")
    print("   → woflstrology.icns (macOS – works in Tauri/Electron/Cargo bundles)")
    print("   → every woflstrology_XXX.png ready for app stores")

if __name__ == "__main__":
    forge()