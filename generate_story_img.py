#!/usr/bin/env python3
import requests
from bs4 import BeautifulSoup
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime
import os


def get_base_image_name_and_color_from_aqi(aqi: int) -> str:
    if aqi < 50:
        return "good", "#2d3f5b"
    elif aqi < 100:
        return "ok", "#2d3f5b"
    elif aqi < 200:
        return "bad", "#28201d"
    else:
        return "dangerous", "#30130b"


def get_label_from_aqi(aqi: int) -> str:
    if aqi < 50:
        return "Breathe easy"
    elif aqi < 100:
        return "Mostly fine"
    elif aqi < 200:
        return "Unhealthy air"
    else:
        return "Stay inside!"


def fetch_sarajevo_aqi() -> int:
    url = "https://www.iqair.com/bosnia-herzegovina/federation-of-b-h/sarajevo"

    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }

    response = requests.get(url, headers=headers)
    response.raise_for_status()

    soup = BeautifulSoup(response.content, "html.parser")

    aqi_element = soup.find("p", class_="aqi-value__value")

    if not aqi_element:
        # Try alternative selector
        aqi_element = soup.find(string=lambda t: t and "US AQI" in str(t))
        if aqi_element:
            # Try to find the number near this text
            parent = aqi_element.parent
            for sibling in parent.find_all_previous():
                if sibling.string and sibling.string.strip().isdigit():
                    aqi_value = int(sibling.string.strip())
                    break
            else:
                raise ValueError("Could not parse AQI value from page")
        else:
            raise ValueError("Could not find AQI element on page")
    else:
        aqi_value = int(aqi_element.text.strip())

    return aqi_value


def generate_story_image(aqi: int) -> str:
    os.makedirs("stories", exist_ok=True)

    now = datetime.now()
    date_hour = now.strftime("%Y-%m-%d_%H")
    output_path = f"stories/{date_hour}.png"

    base_image, text_color = get_base_image_name_and_color_from_aqi(aqi)
    label = get_label_from_aqi(aqi)

    background_path = f"static/imgs/{base_image}.png"
    img = Image.open(background_path)

    draw = ImageDraw.Draw(img)

    now = datetime.now()
    formatted_date = now.strftime("%B %d at %H:00")

    normal_black = ImageFont.truetype("static/fonts/Noto_Sans/NotoSans-SemiBold.ttf", 110)
    normal = ImageFont.truetype("static/fonts/Noto_Sans/NotoSans-SemiBold.ttf", 65)
    large_black = ImageFont.truetype("static/fonts/Noto_Sans/NotoSans-Black.ttf", 110)

    img_width = img.width
    y_offset = 100

    text_line0 = "Sarajevo"
    bbox0 = draw.textbbox((0, 0), text_line0, font=normal_black)
    text_width0 = bbox0[2] - bbox0[0]
    x0 = (img_width - text_width0) // 2
    draw.text((x0, y_offset), text_line0, fill=text_color, font=normal_black)

    y_offset += 155
    text_line1 = formatted_date
    bbox1 = draw.textbbox((0, 0), text_line1, font=normal)
    text_width1 = bbox1[2] - bbox1[0]
    x1 = (img_width - text_width1) // 2
    draw.text((x1, y_offset), text_line1, fill=text_color, font=normal)

    y_offset += 90
    text_line2 = f"AQI: {aqi}"
    bbox2 = draw.textbbox((0, 0), text_line2, font=normal)
    text_width2 = bbox2[2] - bbox2[0]
    x2 = (img_width - text_width2) // 2
    draw.text((x2, y_offset), text_line2, fill=text_color, font=normal)

    y_offset += 90
    text_line3 = label
    bbox3 = draw.textbbox((0, 0), text_line3, font=large_black)
    text_width3 = bbox3[2] - bbox3[0]
    x3 = (img_width - text_width3) // 2
    draw.text((x3, y_offset), text_line3, fill=text_color, font=large_black)

    img.save(output_path)
    print(f"Story image generated: {output_path}")

    return output_path


def main():
    try:
        print("Fetching Sarajevo AQI...")
        aqi = fetch_sarajevo_aqi()
        print(f"AQI: {aqi}")

        output_path = generate_story_image(aqi)
        print(f"Image saved to: {output_path}")

    except Exception as e:
        print(f"Error: {e}")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
