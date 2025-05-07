#!/bin/bash

# Script to add version tags to documentation files

# Version information
VERSION="0.4.0"
DATE=$(date +'%Y-%m-%d')

# Function to add version tag to a file if it doesn't already have one
add_version_tag() {
    local file=$1
    
    # Check if file already has a version tag
    if grep -q "Version: " "$file"; then
        echo "✅ $file already has a version tag"
    else
        # Create temporary file
        local temp_file=$(mktemp)
        
        # Add version tag at the top of the file (after the first line which is usually the title)
        head -n 1 "$file" > "$temp_file"
        echo "" >> "$temp_file"
        echo "<!-- Version: $VERSION | Last Updated: $DATE -->" >> "$temp_file"
        echo "" >> "$temp_file"
        tail -n +2 "$file" >> "$temp_file"
        
        # Replace the original file
        mv "$temp_file" "$file"
        echo "✅ Added version tag to $file"
    fi
}

# Process all markdown files in the implementation directory and subdirectories
find_and_tag() {
    local dir=$1
    for file in $(find "$dir" -name "*.md"); do
        add_version_tag "$file"
    done
}

# Main execution
echo "Adding version tags to documentation files..."
find_and_tag "/Users/perry.manuk/git/perrymanuk/radbot/docs/implementation"

echo "Version tagging complete!"