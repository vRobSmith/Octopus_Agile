import requests
import time
import pytz
from inky.auto import auto
from datetime import datetime, timezone
from inky import InkyPHAT
from PIL import Image, ImageDraw, ImageFont
from font_fredoka_one import FredokaOne
from dateutil.parser import parse

font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
colour = "black"

def fetch_pricing_data():
    url = "https://api.octopus.energy/v1/products/AGILE-18-02-21/electricity-tariffs/E-1R-AGILE-18-02-21-L/standard-unit-rates/"

    headers = {
        "Content-Type": "application/json",
    }

    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        print(f"Error fetching pricing data: {response.status_code} - {response.text}")
        return []

    data = response.json()

    if 'results' not in data:
        print("Error: 'results' key not found in response")
        return []

    tz = pytz.timezone('Europe/London')
    now = datetime.now(tz=tz)

    # Sort the entire data by 'valid_from' (ascending)
    data['results'].sort(key=lambda x: parse(x['valid_from']))

    # Find the index of the ongoing time slot
    current_slot_index = None
    for i, rate in enumerate(data['results']):
        if parse(rate['valid_from']).astimezone(tz) > now:
            current_slot_index = i - 1
            break

    # Get the ongoing time slot and the next three time slots
    pricing_data = data['results'][current_slot_index:current_slot_index + 4]

    # Convert 'valid_from' to a formatted string
    for rate in pricing_data:
        try:
            valid_from = datetime.fromisoformat(rate['valid_from']).astimezone(tz).strftime('%H:%M')
        except ValueError:
            valid_from = datetime.strptime(rate['valid_from'], '%Y-%m-%dT%H:%M:%S%z').astimezone(tz).strftime('%H:%M')

        rate['valid_from'] = valid_from

    return pricing_data




def display_pricing_data(pricing_data):
    inky_display = auto(ask_user=True, verbose=True)
    inky_display.set_border(inky_display.WHITE)

    img = Image.new("P", (inky_display.WIDTH, inky_display.HEIGHT))
    draw = ImageDraw.Draw(img)

    # Display title
    title_font = ImageFont.truetype(FredokaOne, 18)
    title_text = "Agile Pricing"
    title_size = title_font.getsize(title_text)
    title_x = (inky_display.WIDTH - title_size[0]) // 2
    title_y = 5
    draw.text((title_x, title_y), title_text, inky_display.BLACK, title_font)

    # Draw a horizontal line
    draw.line((0, 30, inky_display.WIDTH, 30), fill=inky_display.BLACK)

    # Display current time
    current_time = time.strftime("%H:%M")
    time_font = ImageFont.truetype(FredokaOne, 14)
    time_size = time_font.getsize(current_time)
    time_x = (inky_display.WIDTH - time_size[0]) // 2
    time_y = 32
    draw.text((time_x, time_y), current_time, inky_display.BLACK, time_font)

    # Draw another horizontal line
    draw.line((0, 50, inky_display.WIDTH, 50), fill=inky_display.BLACK)

    # Display pricing data
    rate_font = ImageFont.truetype(FredokaOne, 12)
    icon_font = ImageFont.truetype("DejaVuSans.ttf", 14)
    large_icon_font = ImageFont.truetype("DejaVuSans.ttf", 56)  # Larger font for the big face
    y = 55
    max_price = 35
    max_bar_width = 70

    # Define the red price threshold (in p/kWh)
    red_price_threshold = 25

    # Determine if the current price is less than 25p
    current_price = pricing_data[0]["value_inc_vat"]
    below_red_price = current_price < red_price_threshold

    for rate in pricing_data:
        valid_from = rate["valid_from"]
        price = rate["value_inc_vat"]
        color = inky_display.RED if price > red_price_threshold else inky_display.BLACK

        # Calculate proportional bar width
        bar_width = int((price / max_price) * max_bar_width)

        draw.text((5, y), valid_from, inky_display.BLACK, rate_font)
        draw.rectangle((45, y-1, 45+bar_width, y+11), fill=color)
        draw.text((45+max_bar_width+5, y), f"{price:.2f}p/kWh", inky_display.BLACK, rate_font)

        # Adjust the y coordinate to fit the text within the display
        y += 16
        if y >= inky_display.HEIGHT:
            break

    # Set the border color based on the current price
    border_color = inky_display.RED if not below_red_price else inky_display.WHITE
    inky_display.set_border(border_color)

    # Display a large smiley or frowning face based on the current price
    if below_red_price:
        draw.text((195, 65), "☺", inky_display.BLACK, large_icon_font)
    else:
        draw.text((195, 65), "☹", inky_display.RED, large_icon_font)  # Use red color for the frowning face

    inky_display.set_image(img)
    inky_display.show()

def main():
    pricing_data = fetch_pricing_data()
    print(pricing_data)  # Add this line to check the content of pricing_data
    display_pricing_data(pricing_data)

if __name__ == "__main__":
    main()
