# Professional Color Scheme Guide

## 🎨 Color Palette

Your presentation now uses a **modern, professional color scheme** designed for maximum impact and readability.

### Primary Colors

| Color Name | RGB Values | Hex Code | Usage |
|------------|-----------|----------|-------|
| **Primary Blue** | (0, 51, 102) | #003366 | Main theme, titles, structure |
| **Accent Orange** | (255, 103, 0) | rgba(104, 24, 20, 1) | Highlights, bullets, emphasis |
| **Accent Gold** | (255, 193, 7) | #FFC107 | Special highlights, date |
| **Success Green** | (76, 175, 80) | #4CAF50 | Positive results, examples |
| **Sky Blue** | (3, 169, 244) | #03A9F4 | Light accents, decorative |

### Neutral Colors

| Color Name | RGB Values | Usage |
|------------|-----------|-------|
| **Soft Gray** | (250, 250, 250) | Block backgrounds |
| **Medium Gray** | (158, 158, 158) | Secondary text |
| **Dark Gray** | (66, 66, 66) | Body text |

---

## 🎯 Title Page Design

### Features:
- **Deep navy blue background** (full slide)
- **Orange accent stripe** at top (0.5cm)
- **Gold accent stripe** at bottom (0.5cm)
- **Logo in white circle** at center top
- **White text** for maximum contrast
- **Gold-colored date** for visual pop
- **Decorative background circles** (subtle, semi-transparent)

### Visual Hierarchy:
1. Logo (centered, white circle background)
2. Title (large, white, bold)
3. Authors & ID (white)
4. Supervisor (white, prominent)
5. Institute (white)
6. Date (gold, stands out)

---

## 📊 Content Slides

### Frame Titles
- **Background**: Primary Blue
- **Text**: White
- **Font**: Large, Bold

### Bullet Points
- **Level 1**: Accent Orange (eye-catching)
- **Level 2**: Primary Blue (cohesive)
- **Level 3**: Success Green (balanced)

### Block Types

#### Standard Block (Information)
- **Title**: Primary Blue background, White text
- **Body**: Soft Gray background, Dark Gray text
- **Use for**: Definitions, explanations, general info

#### Alert Block (Challenges/Problems)
- **Title**: Accent Orange background, White text
- **Body**: Soft Gray background, Dark Gray text
- **Use for**: Challenges, warnings, important notes

#### Example Block (Results/Success)
- **Title**: Success Green background, White text
- **Body**: Soft Gray background, Dark Gray text
- **Use for**: Results, examples, positive outcomes

---

## 📈 Tables

### Highlighted Rows
- **Color**: Accent Gold at 25% opacity (`accentgold!25`)
- **Use for**: NOMA-GNN results, key findings
- **Effect**: Subtle golden highlight that draws attention

### Example:
```latex
\rowcolor{accentgold!25}
\textbf{NOMA-GNN} & \textbf{96.5\%} & \textbf{846 ms}
```

---

## 🎨 Color Psychology

### Why These Colors?

1. **Navy Blue (Primary)**
   - Conveys: Trust, professionalism, stability
   - Perfect for: Academic/technical presentations
   - Impact: Authoritative and credible

2. **Accent Orange**
   - Conveys: Energy, innovation, enthusiasm
   - Perfect for: Highlighting key points
   - Impact: Draws attention without being aggressive

3. **Gold**
   - Conveys: Achievement, quality, excellence
   - Perfect for: Results, special emphasis
   - Impact: Premium, distinguished feel

4. **Success Green**
   - Conveys: Growth, positive results, solutions
   - Perfect for: Achievements, examples
   - Impact: Optimistic and encouraging

5. **Sky Blue**
   - Conveys: Clarity, communication, technology
   - Perfect for: Modern tech presentations
   - Impact: Fresh and contemporary

---

## 🖼️ Logo Requirements

### For Best Results:
- **Format**: PNG with transparent background
- **Filename**: `iiitm-logo.png`
- **Location**: Same folder as `main.tex`
- **Recommended size**: At least 500×500 pixels
- **Aspect ratio**: Square or circular preferred

### If You Don't Have a Logo:
The presentation will work fine without it. Simply comment out or remove the logo node:
```latex
% \node at (0,0) {\includegraphics[height=2.5cm]{iiitm-logo.png}};
```

---

## 💡 Customization Tips

### Change Title Page Colors:
```latex
% In the title slide TikZ code:
\fill[primaryblue] (current page.south west) rectangle (current page.north east);  % Main color
\fill[accentorange] (current page.north west) rectangle ([yshift=-0.5cm]current page.north east);  % Top stripe
\fill[accentgold] (current page.south west) rectangle ([yshift=0.5cm]current page.south east);  % Bottom stripe
```

### Adjust Table Highlighting:
```latex
\rowcolor{accentgold!25}  % 25% opacity - subtle
\rowcolor{accentgold!40}  % 40% opacity - more prominent
\rowcolor{successgreen!20}  % Alternative: use green for results
```

### Modify Block Colors:
Find these lines in the preamble (lines 40-50):
```latex
\setbeamercolor{block title}{bg=primaryblue,fg=white}
\setbeamercolor{block title alerted}{bg=accentorange,fg=white}
\setbeamercolor{block title example}{bg=successgreen,fg=white}
```

---

## ✅ Compilation

### Standard Process:
```cmd
cd c:\Users\shail\Desktop\NOMA_FINAL\noma_ppt
pdflatex main.tex
pdflatex main.tex
```

### Expected Output:
- Professional title slide with logo
- Consistent color scheme throughout
- High-contrast, readable text
- Eye-catching highlights
- Clean, modern appearance

---

## 🎯 Presentation Impact

### Visual Benefits:
✅ **Professional**: Corporate-quality color scheme
✅ **Readable**: High contrast (white on dark, dark on light)
✅ **Engaging**: Vibrant accents draw attention
✅ **Cohesive**: Consistent theme throughout
✅ **Memorable**: Distinctive title slide with logo
✅ **Modern**: Contemporary design aesthetic

### Audience Perception:
- **Credible**: Navy blue conveys expertise
- **Innovative**: Orange highlights suggest cutting-edge work
- **Successful**: Gold emphasizes achievements
- **Clear**: Excellent readability = better understanding

---

## 🚀 Ready to Present!

Your presentation now has:
- ✨ **Custom title page** with centered logo
- 🎨 **Professional color palette** (7 coordinated colors)
- 📊 **Enhanced tables** with golden highlights
- 🎯 **Strategic color coding** for different content types
- 💼 **Conference-quality** appearance

**Good luck with your presentation!** 🎓
