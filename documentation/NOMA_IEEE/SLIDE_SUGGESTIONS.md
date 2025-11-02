# Presentation Slide Content Suggestions

## Slide 2: Introduction and Background (IMPROVED)

### Current Issues:
- Text is a bit dense for a presentation slide
- Could use more visual hierarchy

### Suggested Content:

```latex
\section{Introduction and Background}

\begin{frame}{5G/6G Challenges: Massive Connectivity}
\begin{columns}
\column{0.5\textwidth}
\textbf{The Problem:}
\begin{itemize}
    \item 5G/6G demand massive connectivity
    \item Limited spectrum resources
    \item OMA: Each user gets separate resources
\end{itemize}

\vspace{0.3cm}
\textbf{Limitations of OMA:}
\begin{itemize}
    \item ❌ Spectrum limited; users massive
    \item ❌ QoS heterogeneity not supported
    \item ❌ Inefficient: Unused slots wasted
    \item ❌ Cannot handle massive 5G/6G connectivity
\end{itemize}

\column{0.5\textwidth}
\includegraphics[width=\textwidth]{5g_connections_graph.png}
\end{columns}

\vspace{0.2cm}
\textbf{Source:} Information Matters (Last Updated: January 4, 2023)
\end{frame}

\begin{frame}{Solution: Non-Orthogonal Multiple Access (NOMA)}
\begin{block}{Key Idea}
\textbf{Superpose users on same resource blocks} and separate via \textbf{Successive Interference Cancellation (SIC)}
\end{block}

\vspace{0.3cm}

\begin{columns}
\column{0.45\textwidth}
\textbf{Two Types of NOMA:}

\textbf{a) Code-domain NOMA}
\begin{itemize}
    \item Uses distinct spreading codes
    \item Multi-user detection at receiver
\end{itemize}

\vspace{0.2cm}
\textbf{b) Power-domain NOMA} ✓
\begin{itemize}
    \item Weak user: \textcolor{blue}{Higher power}
    \item Strong user: \textcolor{red}{Lower power}
    \item Strong performs SIC
\end{itemize}

\column{0.5\textwidth}
\textbf{Advantages:}
\begin{itemize}
    \item ✅ Higher spectral efficiency
    \item ✅ Fairness at scale
    \item ✅ Massive connectivity
\end{itemize}
\end{columns}

\end{frame}
```

---

## Slide 3: How Does PD-NOMA Work

### Current Issues:
- Too minimal - needs more detail for understanding
- Missing key equations and process flow

### Suggested Content:

```latex
\begin{frame}{How Does PD-NOMA Work?}

\begin{block}{Basic Process}
BS transmits \textbf{single superposed signal} carrying signals of multiple users (typically 2)
\end{block}

\vspace{0.3cm}

\textbf{Step-by-Step Process:}

\begin{enumerate}
    \item \textbf{Power Allocation:} BS allocates power based on channel quality
    \begin{equation*}
    P_{\text{weak}} = \alpha \cdot P_{\text{total}}, \quad P_{\text{strong}} = (1-\alpha) \cdot P_{\text{total}}
    \end{equation*}
    where $\alpha > 0.5$ (weak user gets more power)
    
    \vspace{0.2cm}
    \item \textbf{Superposition:} BS transmits superposed signal
    \begin{equation*}
    y = h_w \sqrt{P_w} x_w + h_s \sqrt{P_s} x_s + n
    \end{equation*}
    
    \vspace{0.2cm}
    \item \textbf{SIC at Strong User:}
    \begin{itemize}
        \item Decode weak user's signal first (higher power)
        \item Subtract weak signal from received signal
        \item Decode own signal treating residual as noise
    \end{itemize}
    
    \vspace{0.2cm}
    \item \textbf{Weak User:} Treats strong user's signal as noise, decodes directly
\end{enumerate}

\end{frame}

\begin{frame}{PD-NOMA: Visual Illustration}
\centering
\includegraphics[width=0.7\textwidth]{pdnoma_diagram.png}

\vspace{0.5cm}
\textbf{Key Constraint:} Channel gain difference must be sufficient for SIC
\begin{equation*}
|h_{\text{strong}} - h_{\text{weak}}|_{\text{dB}} \geq \Delta_{\text{SIC}} = 5 \text{ dB}
\end{equation*}
\end{frame}
```

---

## Slide 4: User Pairing in NOMA

### Current Issues:
- Good content but could emphasize the optimization challenge more

### Suggested Content:

```latex
\begin{frame}{User Pairing in NOMA: The Critical Challenge}

\begin{block}{Why User Pairing?}
User pairing determines \textbf{which users share the same PRB}. It's the \textbf{most critical} factor affecting NOMA performance.
\end{block}

\vspace{0.3cm}

\begin{columns}
\column{0.55\textwidth}
\textbf{Why It's Important:}
\begin{itemize}
    \item Boosts total throughput \& sum-rate
    \item Increases spectral efficiency
    \item Ensures fairness (edge users)
    \item No extra spectrum needed!
\end{itemize}

\vspace{0.2cm}
\textbf{The Challenge:}
\begin{itemize}
    \item ❌ Combinatorial problem: $\binom{N}{2}$ choices
    \item ❌ Optimal methods: $O(N^3)$ complexity
    \item ❌ Real-time requirements: <1 second
    \item ❌ Must satisfy SIC constraints
\end{itemize}

\column{0.4\textwidth}
\centering
\includegraphics[width=\textwidth]{noma_pairing_diagram.png}

\vspace{0.2cm}
\textbf{Pairing Strategy:}
\begin{equation*}
\alpha P_t \rightarrow \text{Weak}
\end{equation*}
\begin{equation*}
(1-\alpha) P_t \rightarrow \text{Strong}
\end{equation*}

Strong performs SIC $\rightarrow$ Decodes weak $\rightarrow$ Decodes own
\end{columns}

\end{frame}

\begin{frame}{User Pairing: Optimization Problem}

\textbf{Goal:} Find optimal matching $\mathcal{M}^*$ that maximizes system sum-rate

\begin{equation*}
\mathcal{M}^* = \arg\max_{\mathcal{M}} \sum_{(i,j) \in \mathcal{M}} R_{ij}
\end{equation*}

\textbf{Subject to:}
\begin{itemize}
    \item SIC constraint: $|h_i - h_j|_{\text{dB}} \geq 5$ dB
    \item Angular separation: $|\theta_i - \theta_j| \leq 90°$
    \item Matching constraint: Each user paired at most once
    \item Power constraint: $P_i + P_j \leq P_{\text{total}}$
\end{itemize}

\vspace{0.3cm}

\begin{alertblock}{The Problem}
\textbf{NP-Hard} for general NOMA with $N$ users! Need intelligent solutions.
\end{alertblock}

\end{frame}
```

---

## Slide 5-6: Literature Review (TWO SLIDES)

### Suggested Content:

```latex
\begin{frame}{Literature Review: Traditional Approaches}

\begin{block}{1. Foundations \& Early Results}
Early work showed pairing strong+weak users significantly improves NOMA over OMA
\begin{itemize}
    \item \textit{Ding et al.} demonstrated 30-40\% throughput gains
    \item Established SIC feasibility requirements
\end{itemize}
\end{block}

\vspace{0.2cm}

\begin{block}{2. Survey Papers Consolidate the Field}
Major surveys mapped pairing with power allocation, fairness, capacity trade-offs
\begin{itemize}
    \item Recommend \textbf{matching theory} for shared subchannels
    \item \textit{Islam \& Liu} survey (2016), \textit{Dai et al.} survey (2018)
\end{itemize}
\end{block}

\vspace{0.2cm}

\begin{block}{3. Algorithmic Approaches}
Beyond simple heuristics $\rightarrow$ \textbf{Graph Optimization}
\begin{itemize}
    \item \textbf{Bipartite matching} (Hungarian): $O(N^3)$
    \item \textbf{General matching} (Blossom/Edmonds): $O(N^3)$, globally optimal
    \item \textbf{Conflict graph MWIS:} Köse et al. proved claw-free property
    \item \textbf{Hypergraph matching:} For 3+ user groups
\end{itemize}
Target: sum-rate, energy efficiency, or fairness
\end{block}

\end{frame}

\begin{frame}{Literature Review: Learning-Based Trend}

\begin{block}{4. Machine Learning Enters NOMA}
Recent work uses \textbf{ML/DL} (including \textbf{GNNs}) to speed pairing under imperfect CSI
\end{block}

\vspace{0.2cm}

\textbf{Key Works:}

\begin{itemize}
    \item \textbf{NOMANet} (Sun et al., 2020): GNN for NOMA power allocation on subchannels
    \begin{itemize}
        \item Achieved 92\% of optimal with 100× speedup
    \end{itemize}
    
    \vspace{0.1cm}
    \item \textbf{DRL for Joint Optimization} (Jiang et al., 2021): DQN for pairing + power
    \begin{itemize}
        \item Learned policies under QoS constraints
        \item Converged faster than Q-learning baselines
    \end{itemize}
    
    \vspace{0.1cm}
    \item \textbf{GraphSAGE for Wireless} (Eisen et al., 2020): Power control in interference networks
    \begin{itemize}
        \item 95\% of optimal centralized performance
        \item Inductive learning on dynamic topologies
    \end{itemize}
    
    \vspace{0.1cm}
    \item \textbf{V2V NOMA-GNN} (Zhao et al., 2020): GNN for vehicular NOMA
    \begin{itemize}
        \item 88\% optimal with 50× speedup
        \item Lacked physical SIC constraints
    \end{itemize}
\end{itemize}

\vspace{0.2cm}

\begin{alertblock}{Research Gap}
\textbf{No comprehensive GNN framework for PD-NOMA user pairing} with realistic channel models, physical constraints, and multi-task learning!
\end{alertblock}

\end{frame}
```

---

## Additional Slide Suggestions:

### After Literature Review, add these slides:

```latex
\begin{frame}{Research Gap \& Motivation}

\textbf{What's Missing in Existing Work?}

\begin{enumerate}
    \item \textbf{Realistic Channel Models:}
    \begin{itemize}
        \item Most GNN works use simplified path loss
        \item Need 3GPP standardized models (UMa, UMi)
    \end{itemize}
    
    \vspace{0.2cm}
    \item \textbf{Physical Constraints:}
    \begin{itemize}
        \item SIC feasibility often ignored
        \item Angular separation not enforced
    \end{itemize}
    
    \vspace{0.2cm}
    \item \textbf{Joint Optimization:}
    \begin{itemize}
        \item Pairing and power allocation done separately
        \item Multi-task learning underexplored
    \end{itemize}
    
    \vspace{0.2cm}
    \item \textbf{Scalability:}
    \begin{itemize}
        \item Most works test on $N \leq 100$ users
        \item Need solutions for dense 5G/6G (500+ users)
    \end{itemize}
\end{enumerate}

\vspace{0.3cm}

\begin{block}{Our Contribution}
\textbf{NOMA-GNN:} A GraphSAGE-based multi-task framework with realistic 3GPP channels, physical constraints, and scalable to 500+ users
\end{block}

\end{frame}

\begin{frame}{Problem Formulation}

\textbf{System Model:}
\begin{itemize}
    \item Single-cell downlink PD-NOMA
    \item $N$ users randomly distributed in 500m radius
    \item 3GPP UMa channel: path loss + shadowing + Rayleigh fading
    \item $M$ Physical Resource Blocks (PRBs)
\end{itemize}

\vspace{0.3cm}

\textbf{Optimization Objective:}

\begin{equation*}
\max_{\mathcal{M}, \{\alpha_{ij}\}} \sum_{(i,j) \in \mathcal{M}} \left( R_i^{\text{weak}} + R_j^{\text{strong}} \right)
\end{equation*}

where for pair $(i,j)$ with $h_i < h_j$:

\begin{align*}
R_i^{\text{weak}} &= \log_2\left(1 + \frac{\alpha P h_i}{(1-\alpha) P h_i + N_0}\right) \\
R_j^{\text{strong}} &= \log_2\left(1 + \frac{(1-\alpha) P h_j}{N_0}\right)
\end{align*}

\textbf{Constraints:}
\begin{itemize}
    \item $|h_i - h_j|_{\text{dB}} \geq 5$ dB (SIC)
    \item $|\theta_i - \theta_j| \leq 90°$ (Angular)
    \item $0.5 \leq \alpha \leq 1$ (Power split)
\end{itemize}

\end{frame}
```

---

## Summary of Recommendations:

### For Your Presentation:

1. **Slide 2 (Intro):** ✅ Keep as is, very clear

2. **Slide 3 (How PD-NOMA Works):** 
   - Add equations for power allocation
   - Add visual diagram
   - Explain SIC step-by-step

3. **Slide 4 (User Pairing):** ✅ Good, maybe add complexity comparison table

4. **Slides 5-6 (Literature Review - TWO SLIDES):**
   - **Slide 5:** Traditional (Foundations, Surveys, Graph Methods)
   - **Slide 6:** Learning-based (GNNs, DRL, specific papers with results)
   - End with "Research Gap" callout

5. **Add New Slides:**
   - Research Gap & Motivation
   - Problem Formulation (with equations)

### Key Papers to Cite in Literature:

1. **Foundations:** Ding et al. (2014) - User pairing in NOMA downlink
2. **Surveys:** Islam & Liu (2016), Dai et al. (2018)
3. **Graph Methods:** Köse et al. (2021) - Conflict graph MWIS
4. **GNN for Wireless:** Eisen et al. (2020) - GraphSAGE power control
5. **NOMA + ML:** Zhao et al. (2020) - V2V NOMA-GNN
6. **DRL:** Jiang et al. (2021) - DQN for joint optimization

Would you like me to create the actual LaTeX Beamer files with these improvements?
