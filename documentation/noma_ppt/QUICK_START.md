# Quick Start Guide - NOMA-GNN Presentation

## 📋 Before You Compile

### 1. Logo File
**IMPORTANT**: You need the IIIT Manipur logo file!

- **Filename**: `iiitm-logo.png`
- **Location**: Place it in the `noma_ppt` folder (same location as `main.tex`)
- **Format**: PNG with transparent background preferred
- **Size**: 500×500 pixels or larger

#### If you don't have the logo:
**Option A** - Remove logo from title page:
```latex
% Comment out these lines in main.tex (around line 140):
% \begin{tikzpicture}
%     \fill[white] (0,0) circle (1.5cm);
%     \node at (0,0) {\includegraphics[height=2.5cm]{iiitm-logo.png}};
% \end{tikzpicture}
```

**Option B** - Use a placeholder:
Create a simple placeholder image or download the official logo from IIIT Manipur website.

---

## 🚀 Compilation Steps

### Windows (Command Prompt):
```cmd
cd c:\Users\shail\Desktop\NOMA_FINAL\noma_ppt
pdflatex main.tex
pdflatex main.tex
```

### Why compile twice?
- First run: Generates TOC, page numbers, references
- Second run: Updates cross-references and finalizes layout

---

## 🎨 What You'll Get

### Title Slide Features:
✨ Navy blue background with orange & gold stripes
✨ Centered logo in white circle
✨ Professional typography
✨ Clean, modern design

### Content Slides:
📊 Navy blue frame titles (white text)
🎯 Orange bullets for emphasis
📈 Golden-highlighted result tables
💡 Color-coded blocks (blue=info, orange=alert, green=success)

---

## ⚠️ Troubleshooting

### Error: "File `iiitm-logo.png` not found"
**Solution**: 
1. Make sure `iiitm-logo.png` is in the `noma_ppt` folder
2. OR remove/comment the logo code (see above)

### Error: "Undefined control sequence"
**Solution**: Make sure you have all required packages installed:
```cmd
pdflatex --version
```
If missing packages, install MiKTeX or TeX Live.

### Colors look different from expected
**Solution**: 
- Use Adobe Acrobat Reader (best color accuracy)
- Some PDF viewers render colors differently
- Print preview may show different colors than screen

### Title page text overlapping
**Solution**: Already fixed! The new design properly layers text above background.

---

## 📝 Customization Quick Tips

### Change main color theme:
Edit lines 23-29 in `main.tex`:
```latex
\definecolor{primaryblue}{RGB}{0,51,102}        % Your main color
\definecolor{accentorange}{RGB}{255,103,0}      % Your accent color
```

### Adjust logo size:
Edit line 142:
```latex
\node at (0,0) {\includegraphics[height=2.5cm]{iiitm-logo.png}};
                                    ^^^^^^^^ Change this
```

### Modify table highlights:
Find `\rowcolor{accentgold!25}` and change:
- `!25` = 25% opacity (subtle)
- `!50` = 50% opacity (more visible)
- Replace `accentgold` with `successgreen` for green highlighting

---

## ✅ Final Checklist

Before presenting:
- [ ] Logo file in place (or logo code removed)
- [ ] Compiled successfully (no errors)
- [ ] Reviewed PDF output
- [ ] Tested on presentation computer/projector
- [ ] Verified all colors are visible
- [ ] Checked all content fits on slides
- [ ] Animation/transitions work (if any)

---

## 📧 Need Help?

Check the comprehensive guides:
- `COLOR_GUIDE.md` - Detailed color scheme documentation
- `SPEAKER_NOTES.md` - Presentation delivery tips (if exists)
- `README.md` - Overall project documentation

---

## 🎓 You're Ready!

Your presentation has:
✅ Professional conference-quality design
✅ Modern color scheme (navy, orange, gold, green)
✅ Custom title page with logo
✅ Enhanced readability
✅ Strategic visual hierarchy

**Compile and present with confidence!** 🚀
