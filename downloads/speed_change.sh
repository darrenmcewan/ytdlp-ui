#!/bin/bash

# Create output directory if it doesn't exist
mkdir -p output

# Loop through all files in the current directory
for file in *; do
    # Skip directories and the script itself
    if [ -f "$file" ] && [ "$file" != "$(basename "$0")" ]; then
        # Get the filename and extension
        filename=$(basename "$file")
        
        echo "Processing: $filename"
        
        # Run ffmpeg with atempo filter
        ffmpeg -i "$file" -filter:a "atempo=1.75" "output/$filename" -y
        
        if [ $? -eq 0 ]; then
            echo "Successfully processed: $filename"
        else
            echo "Error processing: $filename"
        fi
        
        echo "---"
    fi
done

echo "All files processed!"
