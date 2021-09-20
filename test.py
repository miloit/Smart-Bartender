from PIL import Image, ImageDraw, ImageFont
import adafruit_ssd1306
import board
import busio
import digitalio
import time 

BORDER = 5

#spi = busio.SPI(board.SCK, MOSI=board.MOSI)
spi = board.SPI()
reset_pin = digitalio.DigitalInOut(board.D15) # any pin!
cs_pin = digitalio.DigitalInOut(board.D7)    # any pin!
dc_pin = digitalio.DigitalInOut(board.D16)    # any pin!

oled = adafruit_ssd1306.SSD1306_SPI(128, 64, spi, dc_pin, reset_pin, cs_pin)
# Clear display.
oled.fill(0)
oled.show()

oled.fill(0)
oled.show()

# Set a pixel in the origin 0,0 position.
oled.pixel(0, 0, 1)
# Set a pixel in the middle 64, 16 position.
oled.pixel(64, 16, 1)
# Set a pixel in the opposite 127, 31 position.
oled.pixel(127, 63, 1)
oled.show()


# Create blank image for drawing.
#image = Image.new("1", (oled.width, oled.height))
#draw = ImageDraw.Draw(image)

# Load a font in 2 different sizes.
#font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 16)
#font2 = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 24)
#font = ImageFont.load_default()
#font2 = ImageFont.load_default()


#offset = 0  # flips between 0 and 32 for double buffering

#while True:
    # write the current time to the display after each scroll
#    draw.rectangle((0, 0, oled.width, oled.height * 2), outline=0, fill=0)
#    text = time.strftime("%A")
#    draw.text((0, 0), text, font=font, fill=255)
#    text = time.strftime("%e %b %Y")
#    draw.text((0, 14), text, font=font, fill=255)
#    text = time.strftime("%X")
#



# Create blank image for drawing.
# Make sure to create image with mode '1' for 1-bit color.
image = Image.new('1', (oled.width, oled.height))

# Get drawing object to draw on image.
draw = ImageDraw.Draw(image)
# Draw a white background
draw.rectangle((0, 0, oled.width, oled.height), outline=255, fill=0)


# Draw a smaller inner rectangle
#draw.rectangle((BORDER, BORDER, oled.width - BORDER - 1, oled.height - BORDER - 1),
#               outline=0, fill=0)

# Display image

# Load default font.
#font = ImageFont.load_default()

# Draw Some Text
#text = "Hello World!"
#(font_width, font_height) = font.getsize(text)
#draw.text((oled.width//2 - 40//2, oled.height//2 - 40//2),
#          text, font=font, fill=255)

oled.image(image)
oled.show()
