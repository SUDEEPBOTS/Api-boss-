import logging
import os
import re
import aiofiles
import aiohttp
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont
from youtubesearchpython.__future__ import VideosSearch
import textwrap
import traceback

from config import YOUTUBE_IMG_URL
from RessoMusic import app

logging.basicConfig(level=logging.INFO)

# =================================================
# 🛠️ HELPER FUNCTIONS (Inki ab zaroorat nahi hai, par 
# error na aaye isliye code mein chhod raha hu)
# =================================================

def changeImageSize(maxWidth, maxHeight, image):
    widthRatio = maxWidth / image.size[0]
    heightRatio = maxHeight / image.size[1]
    newWidth = int(widthRatio * image.size[0])
    newHeight = int(heightRatio * image.size[1])
    return image.resize((newWidth, newHeight))

def truncate(text):
    list = text.split(" ")
    text1 = ""
    text2 = ""    
    for i in list:
        if len(text1) + len(i) < 30:        
            text1 += " " + i
        elif len(text2) + len(i) < 30:       
            text2 += " " + i
    return [text1.strip(), text2.strip()]

def random_color():
    return (255, 255, 255)

def generate_gradient(width, height, start_color, end_color):
    return Image.new('RGBA', (width, height), start_color)

def add_border(image, border_width, border_color):
    return image

def crop_center_circle(img, output_size, border, border_color, crop_scale=1.5):
    return img

def draw_text_with_shadow(background, draw, position, text, font, fill, shadow_offset=(3, 3), shadow_blur=5):
    pass

# =================================================
# 🚀 MAIN THUMBNAIL LOGIC (NOW INSTANT)
# =================================================

async def gen_thumb(videoid: str):
    """
    Ye function ab koi processing nahi karega.
    Seedha Static Thumbnail ka link return karega.
    Speed: 0.001s ⚡
    """
    return "https://files.catbox.moe/vk7gj0.jpg"

