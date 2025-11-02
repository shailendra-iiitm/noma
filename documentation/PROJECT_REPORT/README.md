# NOMA User Pairing using Graph Neural Networks
## College Project Report (50-60 Pages)

### Project Overview
This LaTeX document presents a comprehensive academic project report on **Graph Neural Network-based User Pairing for Power-Domain Non-Orthogonal Multiple Access (PD-NOMA)** systems in 5G/6G wireless networks.

### Report Structure

#### Front Matter
- **Title Page**: University details, project title, student and supervisor information
- **Certificate**: Supervisor and HOD certification
- **Declaration**: Student declaration of originality
- **Acknowledgments**: Recognition of guidance and support
- **Abstract**: 500-word summary with keywords
- **Abbreviations**: List of 40+ technical acronyms

#### Main Chapters (16 Chapters)

1. **Introduction** (~3000 words)
   - Background on 5G/6G and NOMA
   - Motivation for user pairing problem
   - Deep learning approach overview
   - Problem statement and objectives
   - Scope and contributions

2. **Literature Review** (~3500 words)
   - Evolution of multiple access techniques
   - User pairing strategies (heuristic, optimization, graph-theoretic)
   - Deep learning for wireless communications
   - Graph neural networks
   - Research gaps

3. **Problem Formulation** (~2500 words)
   - System overview
   - Channel model
   - NOMA signal model and SIC constraints
   - Optimization formulation
   - Complexity analysis
   - Graph reformulation

4. **System Model** (~500 words)
   - Network architecture
   - Base station configuration
   - NOMA protocol
   - Performance metrics

5. **Channel Modeling** (~2500 words)
   - 3GPP TR 38.901 standard
   - UMa scenario specifications
   - LOS probability calculation
   - Path loss models (LOS/NLOS)
   - Shadow fading and Rayleigh fading
   - Dataset generation pipeline

6. **Traditional Methods** (~3500 words)
   - Static pairing algorithm
   - Balanced pairing algorithm
   - Blossom maximum-weight matching
   - Bipartite graph matching
   - Power allocation via bisection
   - Comparative analysis

7. **GNN Framework** (~5000 words)
   - Graph learning formulation
   - GraphSAGE encoder architecture
   - Multi-task decoder heads
   - Training procedure with hard negative sampling
   - Inference pipeline with greedy matching
   - Model interpretability

8. **Implementation Details** (~1500 words)
   - Software architecture
   - Directory structure
   - Technology stack (PyTorch, PyTorch Geometric)
   - Key modules (dataset, model, training, inference)
   - Configuration management
   - Development workflow

9. **Experimental Setup** (~2000 words)
   - Dataset specifications (50,000 scenarios)
   - Hardware and software environment
   - Hyperparameters (architecture, training, optimization)
   - Evaluation metrics (classification, regression, system)
   - Baseline methods
   - Experimental procedure

10. **Results and Discussion** (~4500 words)
    - Classification performance (AUC 92.5%)
    - Regression performance (MAE 0.031 bps/Hz, 0.009 W)
    - System throughput comparison (95.8% optimal, 20× speedup)
    - Ablation studies (multi-task, features, depth, negatives)
    - Generalization tests (unseen densities, channels, geometries)
    - Fairness analysis (Jain's index 0.903)

11. **Conclusion and Future Work** (~3000 words)
    - Summary of contributions
    - Key findings (performance, efficiency, generalization)
    - Practical implications for 5G/6G
    - Limitations (perfect CSI, single cell, scalability)
    - 10 future research directions

#### Appendices

- **Appendix A: Code Listings** (~3000 words)
  - 3GPP UMa channel generation (Python)
  - Multi-task GraphSAGE model
  - Training loop with multi-task loss
  - Inference with greedy matching and SIC verification
  - Dataset generation script
  - Complete evaluation script

- **Appendix B: Dataset Specifications** (~2000 words)
  - CSV file format
  - Data statistics (400,000 users, 1.6M edges)
  - Feature ranges and distributions
  - Normalization schemes
  - Data splits (70/15/15)
  - Sample scenarios
  - Validation results

- **Appendix C: Hyperparameter Configurations** (~2000 words)
  - Complete model configuration
  - GNN architecture parameters
  - Decoder head specifications
  - Training hyperparameters (optimizer, scheduler, loss weights)
  - Data loading and negative sampling
  - Inference parameters
  - Hardware/software environment
  - Hyperparameter tuning results

#### References
- 30+ academic references from IEEE journals, conferences, and 3GPP standards

### Compilation Instructions

#### Prerequisites
```bash
# LaTeX distribution (TeX Live, MiKTeX, or MacTeX)
# Required packages: specified in main.tex preamble
```

#### Compile the Report
```bash
# Method 1: Using pdflatex (recommended)
cd PROJECT_REPORT
pdflatex main.tex
bibtex main
pdflatex main.tex
pdflatex main.tex

# Method 2: Using latexmk (automated)
latexmk -pdf main.tex

# Method 3: Using VS Code with LaTeX Workshop extension
# Open main.tex and use "Build LaTeX project" command
```

#### Clean Auxiliary Files
```bash
latexmk -c  # Remove auxiliary files
latexmk -C  # Remove all generated files including PDF
```

### File Structure

```
PROJECT_REPORT/
├── main.tex                          # Master document
├── references.bib                    # Bibliography
├── README.md                         # This file
├── chapters/
│   ├── 00_titlepage.tex             # Title page
│   ├── 01_certificate.tex           # Certificate
│   ├── 02_declaration.tex           # Declaration
│   ├── 03_acknowledgment.tex        # Acknowledgments
│   ├── 04_abstract.tex              # Abstract
│   ├── 05_abbreviations.tex         # Abbreviations
│   ├── 06_introduction.tex          # Chapter 1
│   ├── 07_literature_review.tex     # Chapter 2
│   ├── 08_problem_formulation.tex   # Chapter 3
│   ├── 09_system_model.tex          # Chapter 4
│   ├── 10_channel_modeling.tex      # Chapter 5
│   ├── 11_traditional_methods.tex   # Chapter 6
│   ├── 12_gnn_framework.tex         # Chapter 7
│   ├── 13_implementation.tex        # Chapter 8
│   ├── 14_experimental_setup.tex    # Chapter 9
│   ├── 15_results.tex               # Chapter 10
│   ├── 16_conclusion.tex            # Chapter 11
│   ├── appendix_a_code.tex          # Appendix A
│   ├── appendix_b_dataset.tex       # Appendix B
│   └── appendix_c_hyperparams.tex   # Appendix C
└── figures/                          # Directory for images (empty)
```

### Key Features

#### LaTeX Packages Used
- **Document Class**: `report` (12pt, A4 paper, one-sided)
- **Page Layout**: `geometry` (1-inch margins)
- **Fonts**: `times`, `helvet`, `courier`
- **Mathematics**: `amsmath`, `amssymb`, `mathtools`
- **Graphics**: `graphicx`, `float`
- **Tables**: `booktabs`, `tabularx`, `multirow`
- **Algorithms**: `algorithm`, `algorithmic`
- **Code Listings**: `listings` (Python syntax highlighting)
- **References**: `cite`, `hyperref`
- **Formatting**: `titlesec`, `fancyhdr`

#### Typography
- **Line Spacing**: 1.5
- **Font**: Times New Roman (12pt)
- **Page Numbers**: Bottom center
- **Headers**: Chapter name in header
- **TOC Depth**: 3 levels
- **Equations**: Numbered by chapter

#### Content Statistics
- **Total Word Count**: ~35,000 words
- **Estimated Pages**: 55-60 pages (excluding figures)
- **Chapters**: 16 main chapters + 3 appendices
- **Tables**: 50+ tables
- **Equations**: 100+ mathematical expressions
- **Algorithms**: 5 algorithm pseudocodes
- **Code Listings**: 6 Python implementations
- **References**: 30+ citations

### Key Results Highlighted

1. **Classification**: AUC 92.5% on pairing prediction
2. **Regression**: MAE 0.031 bps/Hz (sum-rate), 0.009 W (power)
3. **Throughput**: 95.8% of optimal Blossom with 20× speedup
4. **Fairness**: Jain's index 0.903 (near-optimal)
5. **Generalization**: >92% on unseen densities, channels, geometries
6. **Scalability**: O(N log N) complexity vs O(N³) for Blossom
7. **Real-time**: 1.1 ms latency enables TTI-level scheduling

### Academic Context
- **Level**: Undergraduate/Graduate Project
- **Department**: Electronics and Communication Engineering / Computer Science
- **Domain**: Wireless Communications, Deep Learning, Graph Neural Networks
- **Applications**: 5G/6G NOMA systems, Resource Allocation, Network Optimization

### Contact and Acknowledgments

This report documents the complete NOMA-GNN project including:
- Traditional baseline implementations
- 3GPP-compliant channel modeling
- GraphSAGE-based multi-task learning framework
- Comprehensive experimental validation
- Practical deployment considerations

### License
Academic use only. For research and educational purposes.

### Citation
If using this work, please cite:
```
[Student Name], "Graph Neural Network-based User Pairing for 
Power-Domain NOMA in 5G/6G Networks," [University Name], 
[Department], [Year].
```

---

**Report Status**: Complete ✓  
**Last Updated**: 2024  
**Total Pages**: ~55-60 pages  
**Compilation**: Tested with TeXLive 2023  
