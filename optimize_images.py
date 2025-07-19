#!/usr/bin/env python3
"""
Image optimization script for Radio Russell
Converts images to WebP format and optimizes PNG files
"""

import os

from PIL import Image


def optimize_png(input_path, output_path, quality=85):
    """Optimize PNG image by reducing file size while maintaining quality"""
    try:
        with Image.open(input_path) as img:
            # Convert RGBA to RGB if needed (for smaller file size)
            if img.mode in ("RGBA", "LA", "P"):
                # Create a white background
                background = Image.new("RGB", img.size, (255, 255, 255))
                if img.mode == "P":
                    img = img.convert("RGBA")
                background.paste(
                    img, mask=img.split()[-1] if img.mode == "RGBA" else None
                )
                img = background

            # Save optimized PNG
            img.save(output_path, "PNG", optimize=True, quality=quality)
            print(f"✅ Optimized PNG: {output_path}")
            return True
    except Exception as e:
        print(f"❌ Error optimizing PNG {input_path}: {e}")
        return False


def create_webp(input_path, output_path, quality=80):
    """Create WebP version of image"""
    try:
        with Image.open(input_path) as img:
            # Convert to RGB if necessary
            if img.mode in ("RGBA", "LA"):
                # For WebP, we can preserve transparency
                img.save(output_path, "WebP", quality=quality, method=6, lossless=False)
            else:
                if img.mode == "P":
                    img = img.convert("RGB")
                img.save(output_path, "WebP", quality=quality, method=6, lossless=False)

            print(f"✅ Created WebP: {output_path}")
            return True
    except Exception as e:
        print(f"❌ Error creating WebP {input_path}: {e}")
        return False


def get_file_size(path):
    """Get file size in KB"""
    return os.path.getsize(path) / 1024


def main():
    """Main optimization function"""
    print("🖼️  Radio Russell Image Optimizer")
    print("=" * 40)

    # Define images to optimize
    images_to_optimize = [
        {
            "input": "static/RadioCalicoLogoTM.png",
            "output_png": "static/RadioCalicoLogoTM_optimized.png",
            "output_webp": "static/RadioCalicoLogoTM.webp",
        }
    ]

    total_saved = 0

    for img_config in images_to_optimize:
        input_path = img_config["input"]

        if not os.path.exists(input_path):
            print(f"⚠️  Warning: {input_path} not found, skipping...")
            continue

        original_size = get_file_size(input_path)
        print(f"\n📁 Processing: {input_path}")
        print(f"   Original size: {original_size:.1f} KB")

        # Create optimized PNG
        if optimize_png(input_path, img_config["output_png"], quality=85):
            optimized_png_size = get_file_size(img_config["output_png"])
            png_savings = original_size - optimized_png_size
            print(
                f"   Optimized PNG size: {optimized_png_size:.1f} KB (saved {png_savings:.1f} KB)"
            )
            total_saved += png_savings

        # Create WebP version
        if create_webp(input_path, img_config["output_webp"], quality=80):
            webp_size = get_file_size(img_config["output_webp"])
            webp_savings = original_size - webp_size
            print(f"   WebP size: {webp_size:.1f} KB (saved {webp_savings:.1f} KB)")
            total_saved += webp_savings

    print("\n🎉 Optimization complete!")
    print(f"💾 Total space saved: {total_saved:.1f} KB")

    # Additional recommendations
    print("\n📋 Additional Recommendations:")
    print("1. Use the optimized images in your HTML")
    print("2. Implement responsive images with different sizes")
    print("3. Consider using a CDN for faster image delivery")
    print("4. Enable gzip/brotli compression on your server")


if __name__ == "__main__":
    main()
