# Pre-Submission Checklist

## ✅ Before Compiling

### 1. Verify LaTeX Installation
- [ ] TeX distribution installed (MiKTeX/TeX Live)
- [ ] All required packages available
- [ ] pdflatex command accessible
- [ ] bibtex command accessible

### 2. Check File Integrity
- [ ] All 20 chapter files present in `chapters/` folder
- [ ] `main.tex` in root directory
- [ ] `references.bib` in root directory
- [ ] `figures/` directory exists (even if empty)

## 📝 Customization Tasks

### 3. Update Title Page (`chapters/00_titlepage.tex`)
- [ ] Replace "[Your Name]" with your actual name
- [ ] Update "[Your Roll Number]"
- [ ] Update "[Supervisor Name]" 
- [ ] Update "[Department Name]"
- [ ] Update "[University Name]"
- [ ] Update "[City]"
- [ ] Update "[Month Year]"

### 4. Update Certificate (`chapters/01_certificate.tex`)
- [ ] Replace "[Student Name]" (appears twice)
- [ ] Update "[Supervisor Name]"
- [ ] Update "[HOD Name]"
- [ ] Update "[Department]" (appears multiple times)
- [ ] Update date

### 5. Update Declaration (`chapters/02_declaration.tex`)
- [ ] Replace "[Your Name]"
- [ ] Update "[University Name]"
- [ ] Update date
- [ ] Update "[Your City]"

### 6. Review Abstract (`chapters/04_abstract.tex`)
- [ ] Verify all numbers match your actual results
- [ ] Check AUC, MAE, throughput values
- [ ] Ensure no placeholder text remains

## 🖼️ Optional: Add Figures

### 7. Prepare Figures (Optional but Recommended)
- [ ] System architecture diagram
- [ ] GNN model architecture visualization
- [ ] 3GPP UMa channel model illustration
- [ ] Throughput comparison bar chart
- [ ] AUC-ROC curve plot
- [ ] Fairness comparison chart
- [ ] Scalability graph (runtime vs N)

**If adding figures:**
1. Save images in `figures/` directory
2. Supported formats: PNG, JPG, PDF
3. Use descriptive filenames (e.g., `system_architecture.png`)
4. Add to chapters using:
```latex
\begin{figure}[H]
\centering
\includegraphics[width=0.8\textwidth]{figures/filename.png}
\caption{Your caption here}
\label{fig:yourlabel}
\end{figure}
```

## 🔢 Verify Technical Details

### 8. Cross-Check Results (Chapters 14-15)
Compare with your actual implementation:
- [ ] AUC value (currently: 92.5%)
- [ ] MAE sum-rate (currently: 0.031 bps/Hz)
- [ ] MAE power (currently: 0.009 W)
- [ ] Throughput ratio (currently: 95.8%)
- [ ] Speedup (currently: 20×)
- [ ] Runtime (currently: 1.1 ms)
- [ ] Jain's fairness (currently: 0.903)

### 9. Verify Hyperparameters (Appendix C)
- [ ] Hidden dimension (currently: 128)
- [ ] Number of layers (currently: 3)
- [ ] Learning rate (currently: 1e-3)
- [ ] Batch size (currently: 32)
- [ ] Max epochs (currently: 200)
- [ ] Dropout (currently: 0.3)

### 10. Dataset Statistics (Appendix B)
- [ ] Total scenarios (currently: 50,000)
- [ ] User counts (currently: 4-12)
- [ ] Train/val/test split (currently: 70/15/15)

## 🔨 Compilation

### 11. First Compilation
```cmd
cd c:\Users\shail\Developer\MAJOR_PROJECT\PROJECT_REPORT
pdflatex main.tex
```
- [ ] No errors in compilation
- [ ] Check main.log for warnings
- [ ] Verify PDF created (may have missing references - normal)

### 12. Bibliography
```cmd
bibtex main
```
- [ ] No errors
- [ ] Check main.blg for issues

### 13. Final Compilation (Two Passes)
```cmd
pdflatex main.tex
pdflatex main.tex
```
- [ ] All references resolved
- [ ] Table of contents complete
- [ ] Page numbers correct
- [ ] All citations showing

## 📄 PDF Review

### 14. Check PDF Quality
- [ ] Title page formatted correctly
- [ ] All names spelled correctly
- [ ] Table of contents complete with page numbers
- [ ] List of figures appears (if you added figures)
- [ ] List of tables appears
- [ ] List of algorithms appears
- [ ] Abbreviations page formatted properly
- [ ] Chapter numbers sequential (1-11)
- [ ] Appendix letters correct (A-C)

### 15. Review Content
- [ ] No placeholder text (e.g., [Your Name])
- [ ] All equations render properly
- [ ] All tables formatted cleanly
- [ ] Code listings readable
- [ ] No overfull hbox warnings (text overflow)
- [ ] Page breaks sensible (no orphan lines)

### 16. Verify References
- [ ] Bibliography appears at end
- [ ] All citations in text have entries in bibliography
- [ ] No "?" for citations (means missing reference)
- [ ] IEEE citation style correct

## 📏 Format Check

### 17. Page Layout
- [ ] Page size: A4
- [ ] Margins: 1 inch all sides
- [ ] Font: Times New Roman 12pt
- [ ] Line spacing: 1.5
- [ ] Page numbers: bottom center
- [ ] Headers show chapter names

### 18. Length Verification
- [ ] Total pages: 50-65 pages (target achieved)
- [ ] Not too short (< 45 pages)
- [ ] Not too long (> 70 pages)

## 🎯 Final Steps

### 19. Proofreading
- [ ] Spell check complete document
- [ ] Grammar check key sections
- [ ] Technical terms consistent
- [ ] Acronyms defined on first use
- [ ] Consistent tense throughout

### 20. Submission Preparation
- [ ] Save final PDF with descriptive name:
      `[YourName]_NOMA_GNN_Project_Report.pdf`
- [ ] Create backup copy
- [ ] Print copy if required (double-sided recommended)
- [ ] Upload to submission portal if electronic

## 🚨 Common Issues

### If compilation fails:
1. **Missing package**: Install via MiKTeX Console or tlmgr
2. **File not found**: Check all chapter files are in `chapters/`
3. **Bibliography errors**: Ensure bibtex step completed
4. **Overfull hbox**: Usually safe to ignore minor ones (<1pt)

### If references show as "?":
1. Run bibtex again
2. Compile pdflatex twice more
3. Check .bib file for syntax errors

### If TOC missing:
- Compile at least twice (LaTeX needs two passes)

## ✅ Final Checklist

Before final submission:
- [ ] All customizations complete
- [ ] PDF compiles without errors
- [ ] All sections present and complete
- [ ] Page count: 50-60 pages ✓
- [ ] Professional appearance ✓
- [ ] Ready for submission ✓

---

## Quick Compilation Command Sequence

```cmd
cd c:\Users\shail\Developer\MAJOR_PROJECT\PROJECT_REPORT
pdflatex main.tex
bibtex main
pdflatex main.tex
pdflatex main.tex
```

## Expected Output

- **File**: `main.pdf`
- **Pages**: ~55-60 pages
- **Size**: ~2-3 MB
- **Quality**: Print-ready

---

**🎉 Good luck with your project submission!**

*This checklist ensures your report is complete, accurate, and professionally formatted.*
