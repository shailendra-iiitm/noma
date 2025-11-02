# Quick Compilation Guide

## Windows (Your Current System)

### Option 1: Command Prompt
```cmd
cd c:\Users\shail\Developer\MAJOR_PROJECT\PROJECT_REPORT
pdflatex main.tex
bibtex main
pdflatex main.tex
pdflatex main.tex
```

### Option 2: Using latexmk (if installed)
```cmd
cd c:\Users\shail\Developer\MAJOR_PROJECT\PROJECT_REPORT
latexmk -pdf main.tex
```

### Option 3: VS Code LaTeX Workshop
1. Open `main.tex` in VS Code
2. Press `Ctrl+Alt+B` to build
3. Or click "Build LaTeX project" in the LaTeX Workshop menu
4. View PDF with `Ctrl+Alt+V`

## What Gets Generated

After successful compilation:
- `main.pdf` - Your final report (55-60 pages)
- `main.aux`, `main.log`, `main.toc`, etc. - Auxiliary files
- `main.bbl`, `main.blg` - Bibliography files

## Common Issues and Fixes

### Issue: Missing packages
**Solution**: Install missing packages via your LaTeX distribution manager
- MiKTeX: Packages auto-install on first use
- TeX Live: Use `tlmgr install <package-name>`

### Issue: Bibliography not showing
**Solution**: Run the full sequence:
```cmd
pdflatex main.tex
bibtex main
pdflatex main.tex
pdflatex main.tex
```

### Issue: Table of Contents not updating
**Solution**: Compile twice (LaTeX needs two passes)

### Issue: Figures not found
**Solution**: Ensure all referenced figures are in `figures/` directory

## Cleaning Up

### Remove auxiliary files only:
```cmd
del main.aux main.log main.toc main.lof main.lot main.bbl main.blg main.out
```

### Remove everything including PDF:
```cmd
latexmk -C
```

## Report Statistics

- **Front Matter**: 6 sections
- **Main Chapters**: 11 chapters (Introduction through Conclusion)
- **Appendices**: 3 appendices (Code, Dataset, Hyperparameters)
- **References**: 30+ citations
- **Total Sections**: 20+ sections
- **Estimated Pages**: 55-60 pages
- **Word Count**: ~35,000 words

## Customization

### Update Student Details
Edit `chapters/00_titlepage.tex`:
- Your name
- Roll number
- Supervisor name
- Department
- University
- Year

### Update Abstract
Edit `chapters/04_abstract.tex` if needed

### Add Figures
1. Place image files in `figures/` directory
2. Reference in chapters using:
```latex
\begin{figure}[H]
\centering
\includegraphics[width=0.8\textwidth]{figures/your_image.png}
\caption{Your caption}
\label{fig:your_label}
\end{figure}
```

### Modify Hyperparameters
If your actual results differ, update:
- `chapters/14_experimental_setup.tex`
- `chapters/15_results.tex`
- `chapters/appendix_c_hyperparams.tex`

## Compilation Time

Expected compilation time:
- First run: 30-60 seconds
- Subsequent runs: 10-20 seconds
- Full build (4 passes): 2-3 minutes

## Output Quality

- **Page Size**: A4
- **Font Size**: 12pt
- **Line Spacing**: 1.5
- **Margins**: 1 inch all sides
- **Font**: Times New Roman (main text), Courier (code)

## Next Steps After Compilation

1. Review the PDF carefully
2. Check all equations render correctly
3. Verify table formatting
4. Ensure code listings are readable
5. Validate references are cited
6. Proofread for typos
7. Add any missing figures
8. Print or submit electronically

## Technical Support

If compilation fails:
1. Check the `.log` file for specific errors
2. Ensure all `.tex` files are in `chapters/` folder
3. Verify `references.bib` exists in root directory
4. Make sure LaTeX distribution is up to date
5. Try compiling in a clean directory

---

**Ready to Compile!** Just run `pdflatex main.tex` in the PROJECT_REPORT directory.
