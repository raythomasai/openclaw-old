#!/usr/bin/env python3
"""
Visual helper for Jarvis - creates nice images for lists and reminders
Usage: python3 /Users/raythomas/.openclaw/workspace/scripts/visual_helper.py --title "Title" --items "Item 1,Item 2,Item 3" --output /tmp/output.png
"""

from PIL import Image, ImageDraw, ImageFont
import sys
import argparse

def create_list_image(
    title: str,
    items: list,
    output_path: str = "/tmp/image.png",
    accent_color: tuple = (100, 149, 237),  # Cornflower blue
    bg_color: tuple = (30, 30, 30),
    text_color: tuple = (255, 255, 255),
    width: int = 600
):
    """Create a nice image with a title and bullet list."""
    
    # Calculate height based on content
    item_height = 35
    title_height = 80
    padding = 40
    extra_padding = 60
    height = title_height + len(items) * item_height + padding + extra_padding
    
    # Create image
    img = Image.new('RGB', (width, height), bg_color)
    draw = ImageDraw.Draw(img)
    
    # Try fonts, fall back gracefully
    try:
        title_font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 28)
        item_font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 18)
        bullet_font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 14)
    except:
        title_font = ImageFont.load_default()
        item_font = ImageFont.load_default()
        bullet_font = ImageFont.load_default()
    
    # Draw title
    y = 35
    draw.text((30, y), title, font=title_font, fill=accent_color)
    y += 60
    
    # Draw items
    for i, item in enumerate(items):
        # Bullet point
        draw.text((30, y), "●", font=bullet_font, fill=accent_color)
        # Item text
        draw.text((50, y), item, font=item_font, fill=text_color)
        y += item_height
    
    # Save
    img.save(output_path)
    return output_path


def create_reminder_image(
    reminder_text: str,
    output_path: str = "/tmp/reminder.png",
    accent_color: tuple = (255, 107, 107)  # Coral red
):
    """Create a reminder-style image."""
    
    create_list_image(
        title="🔔 Reminder",
        items=[reminder_text],
        output_path=output_path,
        accent_color=accent_color
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Create visual images")
    parser.add_argument("--title", required=True, help="Image title")
    parser.add_argument("--items", required=True, help="Comma-separated items")
    parser.add_argument("--output", default="/tmp/image.png", help="Output path")
    parser.add_argument("--color", default="blue", help="Accent color: blue, red, green, orange")
    
    args = parser.parse_args()
    
    color_map = {
        "blue": (100, 149, 237),
        "red": (255, 107, 107),
        "green": (107, 255, 107),
        "orange": (255, 180, 100),
    }
    accent = color_map.get(args.color, color_map["blue"])
    
    items = [item.strip() for item in args.items.split(",")]
    
    create_list_image(
        title=args.title,
        items=items,
        output_path=args.output,
        accent_color=accent
    )
    
    print(f"Created: {args.output}")
