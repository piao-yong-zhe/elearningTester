from PIL import Image, ImageDraw
import os

w, h = 256, 256
img = Image.new('RGBA', (w, h), (0, 0, 0, 0))
d = ImageDraw.Draw(img)

# skull outline
bbox = [(40, 35), (216, 221)]
d.ellipse(bbox, outline=(255, 255, 255, 255), width=6)

# jaw
jaw = [(70, 165), (186, 215)]
d.rectangle(jaw, outline=(255, 255, 255, 255), width=6)

# eyes
for x, y in [(90, 95), (166, 95)]:
    d.ellipse((x - 16, y - 16, x + 16, y + 16), outline=(255, 255, 255, 255), width=4)

# nose
for x, y in [(128, 112)]:
    d.line((x, y, x, y + 24), fill=(255, 255, 255, 255), width=4)

# teeth
for x in range(90, 170, 20):
    d.rectangle((x, 175, x + 10, 190), fill=(255, 255, 255, 255))

# crossbones
for x, y in [(42, 28), (214, 28)]:
    d.line((x, y, x + 18, y + 18), fill=(255, 255, 255, 255), width=4)
    d.line((x + 18, y, x, y + 18), fill=(255, 255, 255, 255), width=4)

img.save('skull.ico')
print('created', os.path.abspath('skull.ico'))
