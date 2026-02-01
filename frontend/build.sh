#!/bin/bash
# Build Tailwind CSS for MinutesIQ

echo "Building Tailwind CSS..."
npx tailwindcss -i ./src/input.css -o ../src/minutes_iq/static/css/tailwind.css --minify

if [ $? -eq 0 ]; then
    echo "✓ Tailwind CSS built successfully!"
    ls -lh ../src/minutes_iq/static/css/tailwind.css
else
    echo "✗ Build failed"
    exit 1
fi
