# Restructured Project Report - NOMA GNN Thesis

## Overview

This folder contains the restructured version of the NOMA GNN thesis, reorganized from an 11-chapter structure to a 6-chapter structure based on supervisor feedback. The restructuring aims to create a more coherent narrative with better alignment for academic evaluation.

## Thesis Structure

### New 6-Chapter Organization

1. **Chapter 1: Introduction, Literature Review, and Problem Formulation** (`01_introduction_combined.tex`)
   - Combines original chapters 6, 7, and 8
   - Provides comprehensive background on NOMA, research motivation, literature review, and mathematical problem formulation
   - ~50 pages of paragraph-based narrative

2. **Chapter 2: System Model and Channel Modeling** (`02_system_channel_combined.tex`)
   - Combines original chapters 9 and 10
   - Details network architecture, PD-NOMA signal model, and 3GPP TR 38.901 UMa channel model
   - ~35 pages with detailed technical exposition

3. **Chapter 3: Traditional User Pairing Methods** (`03_traditional_combined.tex`)
   - Enhanced version of original chapter 11
   - Covers static pairing, balanced pairing, Blossom matching, and bipartite graph matching
   - ~30 pages with in-depth analysis of each method

4. **Chapter 4: Graph Neural Network Framework** (`04_gnn_combined.tex`)
   - Enhanced version of original chapter 12
   - Presents graph reformulation, GraphSAGE architecture, multi-task decoder, and training methodology
   - ~35 pages covering complete GNN framework

5. **Chapter 5: Implementation, Experimental Setup, and Results** (`05_results_combined.tex`)
   - Combines original chapters 13, 14, and 15
   - Covers software implementation, experimental configuration, performance evaluation
   - Comprehensive results analysis with 96.5% optimal throughput and 52.9× speedup
   - ~40 pages

6. **Chapter 6: Conclusion and Future Directions** (`06_conclusion.tex`)
   - Adapted from original chapter 16
   - Summarizes contributions, key findings, practical implications, limitations, and future work
   - ~25 pages

### Front Matter

- `00_titlepage.tex` - Title page with thesis details
- `01_certificate.tex` - Supervisor certificate
- `02_declaration.tex` - Student declaration
- `03_acknowledgment.tex` - Acknowledgments
- `04_abstract.tex` - Thesis abstract
- `05_abbreviations.tex` - List of abbreviations and acronyms

### Appendices

- `appendix_a_code.tex` - Code listings and repository information
- `appendix_b_dataset.tex` - Dataset specifications and generation details
- `appendix_c_hyperparams.tex` - Hyperparameter tables and configurations

## Key Changes from Original

### Structure
- **From 11 chapters to 6 chapters**: More aligned with standard thesis structure
- **Logical grouping**: Related topics combined for better flow
- **Progressive narrative**: Moves from motivation → theory → methods → results → conclusion

### Writing Style
- **More paragraph-based**: Reduced bullet points in favor of flowing paragraphs
- **Enhanced narrative**: Better connections between sections
- **Professional tone**: Suitable for graduate-level academic evaluation

### Content Enhancement
- Integrated insights from IEEE paper version
- Added more detailed explanations and justifications
- Improved transitions between topics
- Expanded discussion of methodology and results

## Compilation Instructions

### Prerequisites

Ensure you have a complete LaTeX distribution installed:
- **Windows**: MiKTeX or TeX Live
- **Linux/Mac**: TeX Live
- **Required packages**: geometry, graphicx, amsmath, algorithm, listings, hyperref, cite, booktabs, fancyhdr, setspace, titlesec, pgfplots

### Compilation Steps

#### Using Command Line

```bash
# Navigate to the restructured folder
cd c:\Users\shail\Desktop\NOMA_FINAL\PROJECT_REPORT_RESTRUCTURED

# First compilation (generates aux files)
pdflatex main.tex

# Generate bibliography
bibtex main

# Second compilation (resolves citations)
pdflatex main.tex

# Third compilation (resolves cross-references)
pdflatex main.tex
```

#### Using LaTeX Editor

1. Open `main.tex` in your LaTeX editor (TeXworks, TeXstudio, Overleaf, etc.)
2. Set the compiler to **pdfLaTeX**
3. Compile 3 times to resolve all references
4. Run BibTeX between compilations for bibliography

#### Quick Compilation Script (Windows)

```batch
pdflatex -interaction=nonstopmode main.tex
bibtex main
pdflatex -interaction=nonstopmode main.tex
pdflatex -interaction=nonstopmode main.tex
```

### Troubleshooting

**Missing packages**: If compilation fails due to missing packages:
- MiKTeX: Packages are usually installed automatically on first use
- TeX Live: Run `tlmgr install <package-name>`

**Bibliography not appearing**: Ensure you run:
1. pdflatex
2. bibtex
3. pdflatex (twice more)

**Cross-references showing ??**: Run pdflatex multiple times until all references resolve

## File Structure

```
PROJECT_REPORT_RESTRUCTURED/
├── main.tex                          # Main compilation file
├── references.bib                    # Bibliography database
├── README.md                         # This file
└── chapters/
    ├── 00_titlepage.tex             # Front matter
    ├── 01_certificate.tex
    ├── 02_declaration.tex
    ├── 03_acknowledgment.tex
    ├── 04_abstract.tex
    ├── 05_abbreviations.tex
    ├── 01_introduction_combined.tex  # Chapter 1
    ├── 02_system_channel_combined.tex # Chapter 2
    ├── 03_traditional_combined.tex   # Chapter 3
    ├── 04_gnn_combined.tex          # Chapter 4
    ├── 05_results_combined.tex      # Chapter 5
    ├── 06_conclusion.tex            # Chapter 6
    ├── appendix_a_code.tex          # Appendices
    ├── appendix_b_dataset.tex
    └── appendix_c_hyperparams.tex
```

## Key Results Summary

The restructured thesis presents a comprehensive study achieving:
- **96.5% of optimal throughput** (70.74 Gbps vs 73.30 Gbps)
- **52.9× speedup** over Blossom matching (846 ms vs 44.7 s)
- **O(N log N) complexity** vs O(N³) for optimal methods
- **15.72 bits/s/Hz spectral efficiency** (99.5% of optimal)
- **225 user pairs** formed (97% efficiency relative to optimal)

## Document Statistics

- **Total pages**: ~220-240 pages (estimated)
- **Main chapters**: ~215 pages
- **Front matter**: ~10 pages
- **Appendices**: ~15 pages
- **Figures**: Multiple performance plots and architecture diagrams
- **Tables**: Comprehensive results and hyperparameter tables
- **References**: ~50+ academic papers and standards documents

## Notes

1. **Compilation time**: First compilation may take 2-3 minutes depending on system
2. **PDF size**: Expected output ~3-5 MB
3. **Figures**: All referenced figures should be in appropriate directories
4. **Cross-references**: All chapter references updated to new numbering (Chapters 1-6)

## Contact

For questions about compilation or content:
- Review the original PROJECT_REPORT folder for reference
- Check that all required LaTeX packages are installed
- Ensure paths to any external figures are correct

## Version Information

- **Created**: October 2025
- **Based on**: Original 11-chapter thesis structure
- **Purpose**: Supervisor-requested restructuring for better academic alignment
- **Status**: Ready for compilation and review

---

**Ready to compile!** Simply run `pdflatex main.tex` three times with `bibtex main` after the first run to generate your complete restructured thesis.
