# IEEE Paper - Quick Compilation Guide

## ✅ Your Paper is Now IEEE-Standardized!

All essential modifications for IEEE conference submission standards have been applied to your NOMA-GNN paper.

---

## 🚀 Compile Your Paper

### Windows (Your Current System)

```cmd
cd c:\Users\shail\Developer\MAJOR_PROJECT\NOMA_IEEE
pdflatex main.tex
bibtex main
pdflatex main.tex
pdflatex main.tex
```

**Expected Output:** `main.pdf` (6-8 pages in IEEE 2-column format)

---

## 📋 What Was Changed

### 1. **IEEE Standard Packages**
- Added `\IEEEoverridecommandlockouts`
- Proper package ordering
- Added `booktabs` for professional tables

### 2. **Title & Authors**
- IEEE multi-author format (individual blocks)
- Ordinal numbering (1st, 2nd, 3rd)
- Proper affiliation formatting

### 3. **Abstract**
- Results-focused (95.8% throughput, 92.5% AUC upfront)
- Quantitative baseline comparisons
- 3GPP standard reference for credibility

### 4. **Keywords**
- Lowercase, expanded abbreviations
- IEEE Xplore indexable terms
- Broader coverage (5G networks, resource management)

### 5. **Tables**
- `\toprule`, `\midrule`, `\bottomrule` (professional lines)
- `[!t]` float placement
- Enhanced captions with context

### 6. **Bibliography**
- Removed `\nocite{*}` (only cite what you use)
- Added optional acknowledgment template

---

## ✅ Pre-Submission Checklist

Before submitting to conference:

- [ ] **Compile successfully** - No LaTeX errors
- [ ] **Check references** - All `\cite{}` have BibTeX entries
- [ ] **Verify figures** - All referenced figures exist in `figures/` folder
- [ ] **Page count** - Typically 6-8 pages for IEEE conference
- [ ] **Proofread** - Grammar, spelling, technical accuracy
- [ ] **Acronyms** - First use expanded (e.g., "NOMA (Non-Orthogonal...)")
- [ ] **Equations** - All important ones numbered and referenced
- [ ] **Table/Figure captions** - Descriptive and standalone
- [ ] **Author info** - Complete emails and affiliations

---

## 📊 Current Paper Structure

```
NOMA_IEEE/
├── main.tex                     ✅ IEEE-standardized
├── introduction.tex             ✅ Updated (from previous session)
├── literature_review.tex        
├── problem_formulation.tex      
├── system_model.tex             
├── graph_matching.tex           
├── clustering_methodology.tex   
├── gnn_methodology.tex          ✅ GNN framework
├── simulation_setup.tex         
├── result_discussion.tex        ✅ Tables IEEE-formatted
├── conclusion.tex               ✅ Updated (from previous session)
├── references.bib               ✅ 30+ IEEE references
└── figures/                     (add your plots here)
```

---

## 🎯 Key Improvements Made

| Item | Improvement | Impact |
|------|-------------|--------|
| **Packages** | IEEE standard order with `booktabs` | Professional formatting |
| **Author Block** | Individual author blocks | Proper IEEE indexing |
| **Abstract** | Results-first, quantitative | Stronger first impression |
| **Keywords** | Expanded, lowercase terms | Better discoverability |
| **Tables** | `\toprule/\midrule/\bottomrule` | Publication-quality |
| **Citations** | Removed `\nocite{*}` | Only relevant references |

---

## 📈 Expected Results

After compiling, your PDF should:
- ✅ Be in IEEE 2-column format
- ✅ Have professional-looking tables
- ✅ Show all 3 authors properly formatted
- ✅ Include quantitative results in abstract
- ✅ Have 6-8 pages of content
- ✅ Include ~30 references (only cited ones)

---

## 🔍 Verify Your PDF

1. **Title Page**
   - Title: "Graph Neural Network-Based User Pairing..."
   - Authors: 3 individual blocks with ordinals
   - Affiliations: IIIT Manipur

2. **Abstract**
   - Opens with "Power-Domain Non-Orthogonal Multiple Access..."
   - Contains "95.8% of optimal throughput"
   - Contains "92.5% AUC"
   - Contains "20× speedup"

3. **Keywords**
   - All lowercase
   - "Non-orthogonal multiple access" (not "NOMA")
   - "successive interference cancellation" (not "SIC")

4. **Tables** (Section IX - Results)
   - Table I: Classification Performance (with `\toprule`)
   - Table II: Regression Performance (with `\midrule`)
   - Table III: Complexity Comparison (with `\bottomrule`)

5. **References**
   - Only cited references appear (not all 380+ from .bib)
   - IEEE format with DOIs

---

## 🚨 Common Issues & Fixes

### Issue: "Undefined control sequence \toprule"
**Fix:** Ensure `\usepackage{booktabs}` is in preamble (already added)

### Issue: Bibliography not showing
**Fix:** Run the full sequence:
```cmd
pdflatex main.tex
bibtex main
pdflatex main.tex
pdflatex main.tex
```

### Issue: Too many references
**Fix:** Good! We removed `\nocite{*}`, so only cited refs appear

### Issue: Figure not found
**Fix:** Add your plots to `figures/` folder:
- `throughput_comparison.png`
- Any other figures referenced in text

---

## 📝 Optional Enhancements

### Add Acknowledgment (if applicable)
Edit `main.tex` and uncomment:
```latex
\section*{Acknowledgment}
This work was supported by [Your Funding Source].
The authors would like to thank...
```

### Add Figures
Place in `figures/` folder:
- System architecture diagram
- GNN model architecture
- Throughput comparison plot
- AUC-ROC curve
- Complexity scaling graph

Reference in text:
```latex
Fig.~\ref{fig:throughput} shows...

\begin{figure}[!t]
\centering
\includegraphics[width=\columnwidth]{throughput_comparison.png}
\caption{System throughput comparison across methods.}
\label{fig:throughput}
\end{figure}
```

---

## 🎓 Submission Tips

1. **Conference Deadlines**
   - Check submission deadline carefully
   - Allow 2-3 days for final proofreading
   - Submit 1 day early (avoid last-minute server issues)

2. **PDF Requirements**
   - IEEE conferences typically require PDF/A format
   - Use `pdflatex` (not `latex + dvips`)
   - Embed all fonts (automatic with modern TeX distributions)

3. **Copyright Form**
   - Will be required after acceptance
   - Keep your LaTeX source for camera-ready version

4. **Supplementary Materials**
   - Some conferences allow code/data submissions
   - Consider preparing GitHub repository link

---

## ✅ Your Paper is Ready!

All IEEE standardization changes have been applied. Your paper now:
- ✅ Follows IEEE conference template exactly
- ✅ Has professional table formatting
- ✅ Uses proper author block format
- ✅ Contains quantitative abstract
- ✅ Uses IEEE-indexable keywords
- ✅ Ready for submission after proofreading

**Next Step:** Compile and verify the PDF!

```cmd
cd c:\Users\shail\Developer\MAJOR_PROJECT\NOMA_IEEE
pdflatex main.tex
bibtex main
pdflatex main.tex
pdflatex main.tex
start main.pdf
```

Good luck with your submission! 🎉
