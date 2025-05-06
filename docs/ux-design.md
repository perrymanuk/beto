# RadBot UI Design Principles

This document outlines the key design principles for RadBot's terminal-inspired interface.

## Space Efficiency Principles

RadBot's UI follows a tiling window manager philosophy, emphasizing maximum space utilization while maintaining clarity:

1. **Minimal Vertical Spacing**
   - Reduced line heights (1.1-1.15)
   - Tight paragraph margins (0.2rem between elements)
   - Compact message containers with minimal padding
   - Decreased gaps between UI elements (0.1-0.4rem)

2. **Compact Components**
   - Optimized header height (40px)
   - Reduced input container height (50px)
   - Smart textarea resizing (minimal height when empty, limited growth as typing)
   - Condensed control buttons with minimal padding

3. **Text and Information Density**
   - Smaller font sizes for UI elements (0.7-0.85rem)
   - Reduced command prompt size
   - Condensed system messages with multi-part information in single lines
   - Combined information with separators (|) rather than line breaks

4. **Visual Distinction without Space Waste**
   - Color-coding instead of spacing to show hierarchy
   - Subtle separators with minimal height
   - Element borders for visual separation without padding
   - Unique colors for different user roles (system, user, assistant)

5. **Content Optimization**
   - Smart handling of blank lines (compressing multiple line breaks)
   - User-friendly content formatting with minimal empty space
   - Lower height for voice wave animation
   - Consolidated welcome messages

6. **Responsive Design Considerations**
   - Auto-adjusting elements based on content
   - Minimal padding that maintains context
   - Border highlighting instead of spacing for hover states
   - Efficient use of horizontal space

## Implementation Guidelines

When implementing UI changes:

1. Prefer color, borders, and typography over whitespace for visual hierarchy
2. Use line heights between 1.1-1.3 for readability without wasting space
3. Keep container padding minimal (0.1-0.5rem)
4. Set margins between elements at 0.1-0.4rem
5. Utilize CSS grid/flex layouts with minimal gaps
6. Consolidate information when possible (merging related data)
7. Test with various content densities to ensure readability
8. Consider reducing UI elements to their functional minimum

## Color Palette Strategy

- Use accent colors (blue, amber, red) to indicate different function areas
- Apply subtle backgrounds for content separation
- Employ border highlights for interactive elements
- Select high-contrast text colors for readability
- Create visual depth with subtle separators rather than spacing

This approach ensures RadBot maintains its tiling-window manager aesthetic while providing an efficient, information-dense interface that maximizes screen real estate.