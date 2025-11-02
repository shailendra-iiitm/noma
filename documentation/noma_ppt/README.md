# NOMA-GNN Presentation

This folder contains a comprehensive 18-slide Beamer presentation covering the entire NOMA-GNN project.

## Files

- `main.tex` - Main presentation file (complete 18+ slides)

## Compilation

### Using Command Line (Windows)

```cmd
cd c:\Users\shail\Desktop\NOMA_FINAL\noma_ppt
pdflatex main.tex
pdflatex main.tex
```

Run `pdflatex` twice to ensure proper cross-references and table of contents.

### Using TeXstudio/Overleaf

1. Open `main.tex` in your LaTeX editor
2. Click "Build & View" (F5 in TeXstudio)
3. PDF will be generated automatically

## Presentation Structure (18 Slides)

### Section 1: Introduction (Slides 1-4)
1. Title slide
2. Outline
3. The 5G/6G Challenge
4. What is NOMA?
5. The User Pairing Challenge

### Section 2: Problem Formulation (Slides 5-6)
6. System Model
7. Optimization Problem

### Section 3: Traditional Methods (Slides 7-8)
8. Classical Approaches
9. Performance vs Complexity

### Section 4: Proposed GNN Framework (Slides 9-12)
10. Why Graph Neural Networks?
11. NOMA-GNN Architecture
12. Training Pipeline
13. Inference Pipeline

### Section 5: Experimental Setup (Slides 13-15)
14. Channel Model: 3GPP TR 38.901 UMa
15. Dataset Statistics
16. Implementation Details

### Section 6: Results (Slides 16-19)
17. Throughput Performance
18. Detailed Performance Metrics
19. Model Performance Analysis
20. Computational Complexity Comparison

### Section 7: Contributions (Slides 20-21)
21. Major Contributions
22. Technical Innovations
23. Key Insights

### Section 8: Future Work (Slides 22-23)
24. Current Limitations
25. Future Research Directions

### Section 9: Conclusion (Slides 24-26)
26. Summary
27. Impact and Significance
28. Publications and Deliverables

### Section 10: Q&A (Slides 27-29)
29. Thank You / Questions
30. Backup: Technical Details
31. Backup: Complexity Derivation

## Key Highlights

### Performance Results Shown
- ✓ NOMA-GNN: 96.5% of optimal throughput
- ✓ 52.9× speedup (846 ms vs 44.7 s)
- ✓ 166K parameters, 650 KB model
- ✓ Real-time inference for 500 users

### Visual Elements
- Comprehensive tables comparing all methods
- Color-coded performance metrics
- Clear mathematical formulations
- Algorithm descriptions
- System architecture diagrams

### Technical Content
- Complete problem formulation
- Detailed GNN architecture
- Training and inference pipelines
- 3GPP channel model specifications
- Complexity analysis
- Future research directions

## Customization

### Adding Figures
If you have figures (graphs, diagrams, etc.), create a `figures/` folder and add:

```latex
\begin{figure}
    \centering
    \includegraphics[width=0.8\textwidth]{figures/your_image.png}
    \caption{Your caption}
\end{figure}
```

### Adding Your Logo
Uncomment the logo line in the preamble:
```latex
\logo{\includegraphics[height=0.8cm]{figures/iiit_logo.png}}
```

### Changing Theme/Colors
Modify these lines in the preamble:
```latex
\usetheme{Madrid}           % Try: Berlin, Warsaw, Copenhagen
\usecolortheme{default}     % Try: beaver, crane, dolphin
```

### Adjusting Content
- Each frame is a slide
- Remove/add frames as needed
- Modify content within `\begin{frame}...\end{frame}`
- Adjust font sizes: `\small`, `\footnotesize`, `\tiny`

## Tips for Presentation

### Time Management (15-20 minutes)
- Introduction: 3-4 minutes (Slides 1-5)
- Problem & Methods: 3-4 minutes (Slides 6-9)
- GNN Framework: 4-5 minutes (Slides 10-13)
- Results: 3-4 minutes (Slides 14-20)
- Conclusion: 2-3 minutes (Slides 21-27)
- Q&A: 5 minutes

### Key Points to Emphasize
1. **Problem Importance**: NOMA is critical for 5G/6G
2. **Main Challenge**: Computational complexity vs performance
3. **Our Solution**: GNN learns from optimal solutions
4. **Key Result**: 96.5% throughput with 52.9× speedup
5. **Impact**: Enables real-time deployment

### Backup Slides
Slides 30-31 are backup slides with detailed technical information for questions.

## Panel Presentation Strategy

### For Non-Technical Panel Members
- Focus on slides: 1, 3, 4, 8, 17, 21, 26
- Emphasize practical impact and real-world applications
- Use analogies for complex concepts

### For Technical Panel Members
- Include all slides
- Be ready to discuss architecture details (Slide 11)
- Prepare to explain complexity analysis (Slide 20, 31)
- Reference mathematical formulations (Slides 6, 7, 11)

### Common Questions to Prepare
1. Why GNN over traditional optimization?
2. How does SIC constraint work?
3. What is the training data requirement?
4. Can it scale to 1000+ users?
5. What about multi-cell scenarios?
6. How to handle imperfect CSI?

## Presentation Mode

### Presenter View (Recommended)
- Use PDF reader with presenter view
- Shows current + next slide
- Notes and timer

### Handout Generation
To create a handout with multiple slides per page:
```latex
\documentclass[aspectratio=169,handout]{beamer}
```

## Troubleshooting

### Missing Packages
If compilation fails, install missing packages:
```cmd
tlmgr install beamer
tlmgr install algorithm
tlmgr install algorithmicx
```

### Table Too Wide
Reduce font size within table:
```latex
\begin{table}
    \small  % or \footnotesize or \tiny
    ...
\end{table}
```

### Text Overflow
- Split into multiple frames
- Use `\allowframebreaks`
- Reduce content

## Additional Resources

- Beamer User Guide: https://ctan.org/pkg/beamer
- Theme Gallery: https://deic.uab.cat/~iblanes/beamer_gallery/
- Color Themes: https://hartwork.org/beamer-theme-matrix/

## Contact

For questions about the presentation content, refer to:
- Project Report: `../PROJECT_REPORT/`
- IEEE Paper: `../NOMA_IEEE/`
- Implementation: `../noma_gnn_backup/`

Good luck with your presentation! 🎯
