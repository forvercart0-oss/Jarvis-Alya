# JARVIS 2.0 Brand Assets

This directory contains the official branding assets for JARVIS 2.0.

## Files

- **logo.svg** - Primary logo for the application. Designed for light and dark backgrounds with cyan/blue glow effects.
- **favicon.svg** - Simplified icon for browser tabs and bookmarks.

## Design Guidelines

- **Primary Colors**: Cyan (#00f0ff) and Blue (#0077ff)
- **Style**: Geometric, futuristic, minimal
- **Background Compatibility**: Optimized for dark backgrounds
- **Icon Concept**: Hexagonal "J" with radiating lines and central core

## Usage

- Use `logo.svg` for headers, splash screens, and promotional materials.
- Use `favicon.svg` as the browser favicon (64x64 viewBox).
- For browsers that don't support SVG favicons, provide a PNG fallback generated from favicon.svg.

## Generation

To generate a PNG fallback from favicon.svg, you can use tools like:
- Inkscape: `inkscape --export-type=png --export-filename=favicon.png -w 32 -h 32 favicon.svg`
- ImageMagick: `convert -background none favicon.svg -resize 32x32 favicon.png`
