# File Overwrite Dialog - UI Mockup

## Before Enhancement
```
┌─────────────────────────────────────────┐
│ File Already Exists                     │
├─────────────────────────────────────────┤
│                                         │
│ A file named "document.pdf" already     │
│ exists. Do you want to overwrite it?    │
│                                         │
├─────────────────────────────────────────┤
│         [Overwrite] [Skip] [Cancel]     │
└─────────────────────────────────────────┘
```

## Single File Upload (Details Loaded)
```
┌─────────────────────────────────────────┐
│ File Already Exists                     │
├─────────────────────────────────────────┤
│                                         │
│ A file named "document.pdf" already     │
│ exists.                                 │
│                                         │
│ 📄 File size: 2.45 MB                   │
│ 🔄 Last modified: 2025-12-20 14:30:22   │
│ 🕐 Created: 2025-12-15 09:15:10         │
│                                         │
│ Do you want to overwrite it?            │
│                                         │
├─────────────────────────────────────────┤
│         [Overwrite] [Skip] [Cancel]     │
└─────────────────────────────────────────┘
```

## Batch Upload (Multiple Files - Details Loaded)
```
┌──────────────────────────────────────────────────┐
│ File Already Exists                              │
├──────────────────────────────────────────────────┤
│                                                  │
│ A file named "document.pdf" already exists.      │
│                                                  │
│ 📄 File size: 2.45 MB                            │
│ 🔄 Last modified: 2025-12-20 14:30:22            │
│ 🕐 Created: 2025-12-15 09:15:10                  │
│                                                  │
│ Do you want to overwrite it?                     │
│                                                  │
├──────────────────────────────────────────────────┤
│ [Overwrite] [Always Overwrite] [Skip]           │
│             [Always Skip] [Cancel]               │
└──────────────────────────────────────────────────┘
```

## After Enhancement (Loading State)
```
┌─────────────────────────────────────────┐
│ File Already Exists                     │
├─────────────────────────────────────────┤
│                                         │
│ A file named "document.pdf" already     │
│ exists.                                 │
│                                         │
│ ⭘ Loading file details...              │
│                                         │
│                                         │
│ Do you want to overwrite it?            │
│                                         │
├─────────────────────────────────────────┤
│         [Overwrite] [Skip] [Cancel]     │
└─────────────────────────────────────────┘
```

## After Enhancement (Details Loaded)
```
┌─────────────────────────────────────────┐
│ File Already Exists                     │
├─────────────────────────────────────────┤
│                                         │
│ A file named "document.pdf" already     │
│ exists.                                 │
│                                         │
│ 📄 File size: 2.45 MB                   │
│ 🔄 Last modified: 2025-12-20 14:30:22   │
│ 🕐 Created: 2025-12-15 09:15:10         │
│                                         │
│ Do you want to overwrite it?            │
│                                         │
├─────────────────────────────────────────┤
│         [Overwrite] [Skip] [Cancel]     │
└─────────────────────────────────────────┘
```

## After Enhancement (Error State)
```
┌─────────────────────────────────────────┐
│ File Already Exists                     │
├─────────────────────────────────────────┤
│                                         │
│ A file named "document.pdf" already     │
│ exists.                                 │
│                                         │
│ ⚠️ Could not load file details          │
│                                         │
│                                         │
│ Do you want to overwrite it?            │
│                                         │
├─────────────────────────────────────────┤
│         [Overwrite] [Skip] [Cancel]     │
└─────────────────────────────────────────┘
```

## Animation Sequence

1. **T=0ms**: Dialog opens with loading indicator
2. **T=0-500ms**: API request sent to server
3. **T=500ms**: Details received, loading indicator hidden
4. **T=500-800ms**: Details container fades in (300ms ease-in-out)
5. **T=800ms+**: User can interact with fully loaded dialog

## Visual Elements

### Icons & Colors
- **Document Icon** (Blue #4A90E2): 📄 File size information
- **Update Icon** (Orange #F5A623): 🔄 Last modified timestamp
- **Clock Icon** (Green #7ED321): 🕐 Created timestamp
- **Error Icon** (Red #D0021B): ⚠️ Error state indicator

### Typography
- **Filename**: Bold weight for emphasis
- **Question**: Normal weight
- **Details**: Size 14, with spacing
- **Loading/Error**: Italic style

### Spacing
- 10px gap between major sections
- 8px spacing within detail rows
- Consistent 400px width for content

### Animation
- **Type**: Opacity fade-in
- **Duration**: 300ms
- **Curve**: Ease-in-out
- **Property**: Container opacity (0 → 1)
