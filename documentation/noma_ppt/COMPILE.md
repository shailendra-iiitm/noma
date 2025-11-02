# Quick Compilation Guide

## Fastest Way to Get Your PDF

### Option 1: Overleaf (Recommended - No Installation Needed)
1. Go to https://www.overleaf.com
2. Create free account
3. New Project → Upload Project
4. Upload `main.tex`
5. Click "Recompile"
6. Download PDF

### Option 2: Windows Command Line (If LaTeX Installed)
```cmd
cd c:\Users\shail\Desktop\NOMA_FINAL\noma_ppt
pdflatex main.tex
pdflatex main.tex
```

### Option 3: TeXstudio (If Installed)
1. Open TeXstudio
2. File → Open → Select `main.tex`
3. Press F5 (or Tools → Build & View)
4. PDF opens automatically

### Option 4: VS Code with LaTeX Workshop
1. Install "LaTeX Workshop" extension
2. Open `main.tex`
3. Press Ctrl+Alt+B (or click green play button)
4. PDF preview appears

## Output
- File: `main.pdf`
- Pages: ~18-20 slides
- Format: 16:9 widescreen
- Size: ~200-300 KB

## Presentation Tips
- Use full-screen mode (F5 in most PDF readers)
- Practice timing: ~1 minute per slide
- Keep backup slides (30-31) ready for questions

## Customization Before Compiling
1. Add your institute logo (optional):
   - Uncomment line 36 in `main.tex`
   - Add logo file to `figures/` folder

2. Change colors (optional):
   - Line 28: `\usetheme{Madrid}` → Try: Berlin, Warsaw
   - Line 29: `\usecolortheme{default}` → Try: beaver, crane

3. Add figures (if you have):
   - Create `figures/` folder
   - Add .png/.jpg files
   - Reference in slides

## Common Issues

**Issue**: "beamer.cls not found"
**Solution**: Install MiKTeX or TeX Live

**Issue**: Tables too wide
**Solution**: Already optimized, but can use `\tiny` if needed

**Issue**: Math symbols not rendering
**Solution**: Compile twice (pdflatex main.tex twice)

## Need Help?
Check README.md for detailed instructions.
