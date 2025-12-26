#!/usr/bin/env python3
"""
Generate placeholder icons for UDAC Portal.
Run this script to create basic icons if you don't have custom ones.
"""

import os

# Simple SVG brain icon
BRAIN_SVG = '''<?xml version="1.0" encoding="UTF-8"?>
<svg width="1024" height="1024" viewBox="0 0 1024 1024" xmlns="http://www.w3.org/2000/svg">
  <rect width="1024" height="1024" fill="#0f0c29"/>
  <circle cx="512" cy="512" r="400" fill="#667eea" opacity="0.3"/>
  <text x="512" y="580" font-family="Arial" font-size="400" fill="#667eea" text-anchor="middle">🧠</text>
</svg>
'''

def create_icons():
    """Create placeholder icons."""
    resources_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Write SVG
    svg_path = os.path.join(resources_dir, "udac_portal.svg")
    with open(svg_path, 'w') as f:
        f.write(BRAIN_SVG)
    
    print(f"Created: {svg_path}")
    print("\nTo create proper PNG icons, use an SVG converter or image editor.")
    print("Required sizes for Android: 48x48, 72x72, 96x96, 144x144, 192x192")

if __name__ == "__main__":
    create_icons()
