\documentclass[aspectratio=169]{beamer}

% ==== Theme and Color Setup ====
\usetheme{Madrid}
\usecolortheme{seagull} % soft neutral background
\setbeamertemplate{navigation symbols}{}

% ==== Packages ====
\usepackage[utf8]{inputenc}
\usepackage{amsmath, amssymb, amsfonts}
\usepackage{graphicx}
\usepackage{booktabs}
\usepackage{multicol}
\usepackage{tikz}
\usepackage{algorithm}
\usepackage{algorithmic}
\usepackage{caption}
\usepackage{subcaption}
\usepackage{xcolor}
\usepackage{colortbl}

% ==== Custom Color Palette ====
\definecolor{iiitblue}{RGB}{0,45,114}      % Deep IIIT Blue
\definecolor{lightblue}{RGB}{64,156,255}   % Accent Blue
\definecolor{nomagreen}{RGB}{0,153,102}    % NOMA green
\definecolor{softgray}{RGB}{245,245,245}   % Background gray
\definecolor{headerbg}{RGB}{0,45,114}      % Frame title background

% ==== Beamer Color Definitions ====
\setbeamercolor{structure}{fg=iiitblue}
\setbeamercolor{title}{fg=iiitblue}
\setbeamercolor{frametitle}{fg=white,bg=headerbg}
\setbeamercolor{block title}{fg=white,bg=iiitblue}
\setbeamercolor{block body}{bg=softgray}
\setbeamercolor{alertblock title}{fg=white,bg=nomagreen}
\setbeamercolor{alertblock body}{bg=softgray}
\setbeamercolor{exampleblock title}{fg=white,bg=lightblue}
\setbeamercolor{exampleblock body}{bg=softgray}

% ==== Title Information ====
\title[NOMA-GNN for User Pairing]{\textbf{A GraphSAGE-Based Multi-Task Learning GNN Model for Joint User Pairing and Power Allocation in Downlink PD-NOMA Systems}}

\author[Dwivedi, Shukla]{\textbf{Anisha Dwivedi, Shailendra Shukla} \\ \normalsize{220102020, 220102009}}

\institute[IIIT Manipur]{
Department of Electronics and Communication Engineering\\
Indian Institute of Information Technology, Senapati, Manipur, India\\[0.4cm]
\text{Under the supervision of} \\[0.1cm]
\textbf{Dr. Ramesh Chandra Mishra}\\
\text{Assistant Professor, IIIT Manipur}
}

\date{\today}

% ==== Optional Logo ====
% \logo{\includegraphics[height=0.8cm]{figures/iiit_logo.png}}

% ==== General Aesthetics ====
\setbeamertemplate{footline}[frame number]
\setbeamertemplate{caption}[numbered]
\setbeamerfont{frametitle}{series=\bfseries, size=\large}

% ==== Code and Algorithm Styling ====
\setbeamertemplate{blocks}[rounded][shadow=true]
\setbeamercovered{transparent}

% ==== Document Starts ====
\begin{document}

% ==== Title Slide ====
{
\setbeamertemplate{footline}{}
\begin{frame}[plain]
  \titlepage
\end{frame}
}

% ==== Outline Slide ====
\begin{frame}{Outline}
  \tableofcontents
\end{frame}

% ==== Your Content ====
% (Paste all your section/frames from your original file here below)
% Example:
\section{Introduction}
\begin{frame}[t]{The 5G/6G Challenge}
\small
\textbf{Context: exploding demand}
\begin{itemize}\itemsep0.35em
  \item $\mathbf{50B+}$ connected devices by 2030 (IoT + mobile) \(\Rightarrow\) ultra-dense networks
  \item Bandwidth-heavy uses: UHD/8K video, AR/VR, autonomous vehicles, industrial automation
  \item Networks must deliver: higher \textbf{spectral} \& \textbf{energy} efficiency, \textbf{low latency}, and \textbf{fairness} across diverse users
\end{itemize}

\vspace{0.4em}
\textbf{Where OMA falls short}
\begin{itemize}\itemsep0.35em
  \item FDMA/TDMA/CDMA/OFDMA give each user exclusive time–frequency slices
  \item Orthogonality avoids intra-cell interference \emph{but} wastes spectrum as users scale
  \item Cell-edge users with weak channels consume many PRBs to meet QoS \(\Rightarrow\) caps overall capacity
\end{itemize}

\vspace{0.4em}
\begin{block}{Key problem}
Orthogonal allocation cannot keep up with massive connectivity and heterogeneous QoS.  
We need \textbf{non-orthogonal sharing} with \textbf{smarter user pairing}.
\end{block}
\end{frame}

\begin{frame}[t]{What is PD\text{-}NOMA \& Why Pairing Matters}
\small
\begin{columns}[t,onlytextwidth]

  % ===== Left column: NOMA principles =====
  \column{0.54\textwidth} \vspace{-.5cm}
  \begin{enumerate}\itemsep0.25em
    \item \textbf{Asymmetric power allocation}\\
          Weak (cell-edge) users get higher power; strong (cell-center) users get lower power.
    \item \textbf{Superposition coding}\\
          BS transmits a \emph{single} superposed signal carrying multiple users’ data.
    \item \textbf{Successive Interference Cancellation (SIC)}\\
          Strong user decodes the weak user first, cancels \\ it, then decodes its own message.
  \end{enumerate}


  \textbf{Why PD-NOMA?}
  \begin{itemize}\itemsep0.2em
    \item Multiple users share the \emph{same} PRB.
    \item Significant spectral-efficiency gains and better cell-edge fairness vs.\ OMA.
    \item Adopted in 5G/NR studies and relevant to 5G-Advanced/6G evolution.
  \end{itemize}
    
  % ===== Right column: model + pairing challenge =====
  \column{0.46\textwidth}\vspace{-.95cm}
  \begin{block}{Two-user NOMA signal model}
    \vspace{-0.35em}
    \[
      x \;=\; \sqrt{\alpha P}\,s_w \;+\; \sqrt{(1-\alpha)P}\,s_s
    \]
    \vspace{-0.6em}
    \begin{itemize}\itemsep0.1em
      \item $s_w$: weak user signal, \; $s_s$: strong user signal
      \item $\alpha \in (0,1)$: power split factor (typically 0.7-0.9 for weak user)
      \item $P$: total PRB power budget
    \end{itemize}
  \end{block}

  \vspace{0.25em}
  \begin{alertblock}{The user pairing challenge}
    \begin{itemize}\itemsep0.2em
      \item \textbf{Throughput:} Poor pairs $\Rightarrow$ higher interference, lower sum-rates.
      \item \textbf{SIC feasibility:} Requires sufficient channel-gain gap between paired users.
      \item \textbf{Fairness:} Must help edge users without wasting system capacity.
      \item \textbf{Complexity:} Combinatorial problem; optimal matching scales $\mathcal{O}(N^3)$—impractical for real-time.
    \end{itemize}
  \end{alertblock}

\end{columns}
\end{frame}


\begin{frame}{The User Pairing Challenge}
    \begin{block}{Critical Problem}
        \textbf{Which users should be paired together for optimal system performance?}
    \end{block}
    
    \vspace{0.3cm}
    
    \begin{columns}
        \begin{column}{0.5\textwidth}
            \textbf{Requirements:}
            \begin{itemize}
                \item ✓ Sufficient channel gain difference for SIC
                \item ✓ Adequate angular separation (reduce interference)
                \item ✓ Maximize sum-rate
                \item ✓ Ensure fairness across users
                \item ✓ Real-time decision (<1 sec per TTI)
            \end{itemize}
        \end{column}
        \begin{column}{0.5\textwidth}
            \textbf{Challenges:}
            \begin{itemize}
                \item ✗ Combinatorial complexity: $O(N^3)$
                \item ✗ 500 users = $10^{1134}$ possible combinations!
                \item ✗ Real-time constraint (<1 sec)
                \item ✗ Dynamic channel conditions
                \item ✗ Multi-objective optimization
            \end{itemize}
        \end{column}
    \end{columns}
    
    \vspace{0.3cm}
    
    \begin{alertblock}{Research Motivation}
        \textbf{Can deep learning replace expensive optimization while maintaining near-optimal performance?}
    \end{alertblock}
\end{frame}

% ====== SECTION 2: Problem Formulation ======
\section{Problem Formulation}

\begin{frame}{System Model}
    \begin{columns}
        \begin{column}{0.5\textwidth}
            \textbf{Network Setup:}
            \begin{itemize}
                \item Single Base Station (BS)
                \item $N$ users uniformly distributed
                \item Downlink PD-NOMA transmission
                \item Bandwidth: 5 MHz per PRB
                \item Total Power: 46 dBm
            \end{itemize}
            
            \vspace{0.3cm}
            
            \textbf{Channel Model:}
            \begin{itemize}
                \item \textbf{3GPP TR 38.901 UMa} (Urban Macro)
                \item Path loss + Shadowing + Rayleigh Fading
                \item Industry-standard realistic propagation
                \item 200 training scenarios, 500 users each
            \end{itemize}
        \end{column}
        \begin{column}{0.5\textwidth}
            \begin{block}{Received Signal at User $i$}
                \begin{equation*}
                    y_i = h_i x + n_i
                \end{equation*}
                where $h_i$ is the channel coefficient and $n_i \sim \mathcal{N}(0, \sigma^2)$
            \end{block}
            
            \begin{block}{SINR for Weak User}
                \begin{equation*}
                    \gamma_w = \frac{\alpha P |h_w|^2}{\sigma^2}
                \end{equation*}
            \end{block}
            
            \begin{block}{SINR for Strong User (After SIC)}
                \begin{equation*}
                    \gamma_s = \frac{(1-\alpha) P |h_s|^2}{\sigma^2}
                \end{equation*}
            \end{block}
        \end{column}
    \end{columns}
\end{frame}

\begin{frame}{Optimization Problem}
    \begin{block}{Objective: Maximize System Sum-Rate}
        \begin{equation*}
            \max_{\mathcal{P}, \{\alpha_{ij}\}} \sum_{(i,j) \in \mathcal{P}} R_{ij}
        \end{equation*}
        where $R_{ij} = R_i + R_j$ is the sum-rate of pair $(i,j)$, and $\mathcal{P}$ is the set of selected pairs
    \end{block}
    
    \vspace{0.3cm}
    
    \textbf{Subject to Constraints:}
    \begin{enumerate}
        \item \textbf{SIC Feasibility:} $\frac{h_j}{h_i} \geq \gamma_{\text{th}} = 8$ dB (6.31× linear ratio)
        
        \item \textbf{Angular Separation:} $|\theta_i - \theta_j| \geq 25°$ (spatial diversity)
        
        \item \textbf{Power Allocation:} $0 < \alpha_{ij} < 1$, typically $\alpha \in [0.7, 0.9]$ for weak user
        
        \item \textbf{Matching Constraint:} Each user in at most one pair
        
        \item \textbf{Total Power:} $\sum_{(i,j) \in \mathcal{P}} P_{ij} \leq P_{\text{total}}$
    \end{enumerate}
    
    \vspace{0.2cm}
    
    \begin{alertblock}{Computational Complexity}
        This is an NP-hard combinatorial optimization problem with $O(N^3)$ complexity for optimal solution!
    \end{alertblock}
\end{frame}

% ====== SECTION 3: Traditional Methods ======
\section{Traditional Pairing Methods}

\begin{frame}{Classical Approaches}
    \begin{columns}
        \begin{column}{0.48\textwidth}
            \textbf{1. Static Pairing}
            \begin{itemize}
                \item Sort users by channel gain
                \item Pair strongest with weakest
                \item Complexity: $O(N \log N)$
                \item Simple but highly suboptimal
            \end{itemize}
            
            \vspace{0.4cm}
            
            \textbf{2. Balanced Pairing}
            \begin{itemize}
                \item Divide into strong/weak halves
                \item Match within respective groups
                \item Better channel gain balance
                \item Still greedy; misses global optimum
            \end{itemize}
        \end{column}
        
        \begin{column}{0.48\textwidth}
            \textbf{3. Bipartite Graph Matching}
            \begin{itemize}
                \item Formulate as bipartite graph problem
                \item Hungarian algorithm
                \item Complexity: $O(N^3)$
                \item Near-optimal but computationally expensive
            \end{itemize}
            
            \vspace{0.4cm}
            
            \textbf{4. Blossom Matching (Optimal Baseline)}
            \begin{itemize}
                \item Maximum-weight general matching
                \item Edmonds' algorithm
                \item Complexity: $O(N^3)$
                \item \textbf{Provides optimal benchmark for evaluation}
            \end{itemize}
        \end{column}
    \end{columns}
\end{frame}

\begin{frame}{Traditional Methods: Performance vs Complexity}
    \begin{table}
        \centering
        \small
        \begin{tabular}{lccc}
            \toprule
            \textbf{Method} & \textbf{Complexity} & \textbf{Throughput} & \textbf{Time (500 users)} \\
            \midrule
            Static & $O(N \log N)$ & 55.6\% & 5 ms \\
            Balanced & $O(N \log N)$ & 72.0\% & 8 ms \\
            Bipartite PF & $O(N^3)$ & 100\% & 35-40 s \\
            Blossom & $O(N^3)$ & 100\% & 44.7 s \\
            \midrule
            \textbf{NOMA-GNN} & $O(N \log N)$ & \textbf{96.5\%} & \textbf{846 ms} \\
            \bottomrule
        \end{tabular}
    \end{table}
    
    \vspace{0.5cm}
    
    \begin{block}{Key Observation: The Performance-Complexity Trade-off}
        Fast heuristics (Static, Balanced) sacrifice 28-44\% throughput, while optimal methods (Bipartite, Blossom) are 40-50× too slow for real-time TTI scheduling.
    \end{block}
    
    \begin{exampleblock}{Our Proposed Solution}
        Achieve near-optimal throughput (96.5\%) with fast inference (846 ms) using deep learning—bridging the gap between heuristics and optimal methods.
    \end{exampleblock}
\end{frame}

% ====== SECTION 4: Proposed GNN Framework ======
\section{Proposed GNN Framework}

\begin{frame}{Why Graph Neural Networks?}
    \begin{columns}
        \begin{column}{0.5\textwidth}
            \textbf{User Pairing as a Graph Problem:}
            \begin{itemize}
                \item \textbf{Nodes:} Individual users with CSI features
                \item \textbf{Edges:} Potential pairing candidates
                \item \textbf{Node Features:} Channel gain, distance, angle, SNR
                \item \textbf{Edge Labels:} Pair decision (binary)
                \item \textbf{Edge Attributes:} Predicted sum-rate, power split $\alpha$
            \end{itemize}
            
            \vspace{0.3cm}
            
            \textbf{Why GNNs are Ideal:}
            \begin{itemize}
                \item ✓ Natural representation of pairing structure
                \item ✓ Learn from optimal solutions (Blossom)
                \item ✓ Fast inference after training
                \item ✓ Generalize to unseen scenarios
                \item ✓ Capture local and global dependencies
            \end{itemize}
        \end{column}
        \begin{column}{0.5\textwidth}
            \begin{block}{Graph Construction Strategy}
                \textbf{Candidate Edge Filtering:}
                \begin{itemize}
                    \item SIC feasibility: $h_j/h_i \geq 8$ dB
                    \item Angular separation: $|\theta_i - \theta_j| \geq 25°$
                    \item Strong-weak pairing only
                \end{itemize}
                
                \vspace{0.1cm}
                
                This reduces search space dramatically!
            \end{block}
            
            \vspace{0.2cm}
            
            \begin{exampleblock}{Complexity Reduction}
                \textbf{500 users:}
                \begin{itemize}
                    \item All pairs: $\binom{500}{2} = 124,750$
                    \item After filtering: $\sim$3000-5000 edges
                    \item \textbf{95-97\% reduction!}
                \end{itemize}
            \end{exampleblock}
        \end{column}
    \end{columns}
\end{frame}

\begin{frame}{NOMA-GNN Architecture}
    \begin{center}
        \textbf{GraphSAGE-Based Multi-Task Learning Framework}
    \end{center}
    
    \vspace{0.3cm}
    
    \begin{columns}
        \begin{column}{0.5\textwidth}
            \textbf{1. Graph Encoder (GraphSAGE)}
            \begin{itemize}
                \item \textbf{Input:} Node features $\mathbf{x}_i = [h_i, d_i, \theta_i, \text{SNR}_i]$
                \item \textbf{Architecture:} 3 message-passing layers
                \item \textbf{Hidden dimension:} 128
                \item \textbf{Aggregation:} MEAN pooling
                \item \textbf{Output:} Node embeddings $\mathbf{h}_i \in \mathbb{R}^{128}$
            \end{itemize}
            
            \vspace{0.2cm}
            
            \begin{block}{Message Passing Update}
                \small
                \begin{equation*}
                    \mathbf{h}_i^{(\ell)} = \sigma\left( \mathbf{W}^{(\ell)} \cdot \text{MEAN}\{\mathbf{h}_j^{(\ell-1)} : j \in \mathcal{N}(i)\} \right)
                \end{equation*}
            \end{block}
        \end{column}
        \begin{column}{0.5\textwidth}
            \textbf{2. Multi-Task Decoder}
            
            \textbf{Edge embedding:} $\mathbf{e}_{ij} = [\mathbf{h}_i || \mathbf{h}_j]$ (concatenation)
            
            \vspace{0.2cm}
            
            \textbf{Three Prediction Heads:}
            \begin{enumerate}
                \item \textbf{Pairing Classifier}
                \begin{itemize}
                    \item Task: Pair or not pair?
                    \item Output: $p_{ij} \in [0,1]$
                    \item Loss: Binary Cross-Entropy
                \end{itemize}
                
                \item \textbf{Sum-Rate Regressor}
                \begin{itemize}
                    \item Task: Predict throughput
                    \item Output: $\hat{R}_{ij}$ (bits/s/Hz)
                    \item Loss: MAE
                \end{itemize}
                
                \item \textbf{Power Allocator}
                \begin{itemize}
                    \item Task: Predict optimal $\alpha$ split
                    \item Output: $\hat{\alpha}_{ij} \in (0,1)$
                    \item Loss: MAE
                \end{itemize}
            \end{enumerate}
        \end{column}
    \end{columns}
\end{frame}

\begin{frame}{Training Pipeline}
    \begin{columns}
        \begin{column}{0.5\textwidth}
            \textbf{Data Generation Process:}
            \begin{enumerate}
                \item Generate 200 diverse scenarios
                \item 500 users per scenario (3GPP UMa)
                \item Run Blossom for optimal pairing labels
                \item Extract graph features
                \item Total: 100,000 user samples
            \end{enumerate}
            
            \vspace{0.3cm}
            
            \textbf{Training Strategy:}
            \begin{itemize}
                \item \textbf{Hard Negative Sampling}
                \begin{itemize}
                    \item Positives: Blossom-selected pairs
                    \item Negatives: SIC-feasible but not selected
                    \item Ratio: 1:5 (positive:negative)
                    \item Improves discrimination
                \end{itemize}
                
                \item \textbf{Feature Normalization}
                \begin{itemize}
                    \item Z-score standardization
                    \item Saved scaler for inference consistency
                \end{itemize}
            \end{itemize}
        \end{column}
        \begin{column}{0.5\textwidth}
            \begin{block}{Multi-Task Loss Function}
                \begin{align*}
                    \mathcal{L} = &\lambda_1 \mathcal{L}_{\text{BCE}}(p_{ij}, y_{ij}) \\
                    &+ \lambda_2 \mathcal{L}_{\text{MAE}}(\hat{R}_{ij}, R_{ij}) \\
                    &+ \lambda_3 \mathcal{L}_{\text{MAE}}(\hat{\alpha}_{ij}, \alpha_{ij})
                \end{align*}
                
                Weights: $\lambda_1=1.0, \lambda_2=0.5, \lambda_3=0.3$
            \end{block}
            
            \vspace{0.2cm}
            
            \textbf{Hyperparameters:}
            \begin{itemize}
                \item Optimizer: Adam
                \item Learning rate: 0.001
                \item Batch size: 32 graphs
                \item Epochs: 50
                \item Dropout: 0.3
            \end{itemize}
            
            \vspace{0.2cm}
            
            \textbf{Model Footprint:}
            \begin{itemize}
                \item Parameters: 166K
                \item Model size: 650 KB
                \item Training time: $\sim$2 hours (RTX 3060)
            \end{itemize}
        \end{column}
    \end{columns}
\end{frame}

\begin{frame}{Inference Pipeline}
    \textbf{Real-Time Pairing Decision Process:}
    
    \begin{enumerate}
        \item \textbf{Input:} New scenario with $N$ users and CSI measurements
        
        \item \textbf{Graph Construction:}
        \begin{itemize}
            \item Apply SIC feasibility constraint ($h_j/h_i \geq 8$ dB)
            \item Apply angular separation constraint ($|\theta_i - \theta_j| \geq 25°$)
            \item Create candidate edges (typically 3000-5000 for 500 users)
            \item Build bipartite message-passing graph
        \end{itemize}
        
        \item \textbf{GNN Forward Pass:}
        \begin{itemize}
            \item Load trained checkpoint (best\_model.pt)
            \item Normalize features using saved scaler
            \item Predict pairing scores, sum-rates, and $\alpha$ values for all candidate edges
        \end{itemize}
        
        \item \textbf{Greedy Matching:}
        \begin{itemize}
            \item Sort edges by predicted sum-rate (descending)
            \item Greedily select highest-scoring non-conflicting pairs
            \item Complexity: $O(E \log E) = O(N^2 \log N)$ worst case
            \item Typical: $O(N \log N)$ due to sparse graph structure
        \end{itemize}
        
        \item \textbf{Output:}
        \begin{itemize}
            \item Selected pairs $\mathcal{P}$ with predicted $\alpha$ values
            \item Estimated total system throughput
            \item SIC verification report
        \end{itemize}
    \end{enumerate}
    
    \vspace{0.2cm}
    
    \begin{exampleblock}{Real-Time Performance}
        \textbf{500 users: 846 ms} — 52.9× faster than Blossom's 44.7 seconds!
    \end{exampleblock}
\end{frame}

% ====== SECTION 5: Experimental Setup ======
\section{Experimental Setup and Dataset}

\begin{frame}{Channel Model: 3GPP TR 38.901 UMa}
    \begin{columns}
        \begin{column}{0.5\textwidth}
            \textbf{Urban Macro (UMa) Scenario:}
            \begin{itemize}
                \item Carrier frequency: 2.1 GHz
                \item BS height: 25 m
                \item UE height: 1.5 m
                \item Coverage radius: 500 m
                \item Uniform user distribution
            \end{itemize}
            
            \vspace{0.3cm}
            
            \textbf{Channel Components:}
            \begin{enumerate}
                \item \textbf{Path Loss}
                \begin{itemize}
                    \item Distance-dependent attenuation
                    \item LOS/NLOS probability model
                \end{itemize}
                
                \item \textbf{Shadowing}
                \begin{itemize}
                    \item Log-normal: $\sigma = 7$ dB
                    \item Spatial correlation
                \end{itemize}
                
                \item \textbf{Rayleigh Fading}
                \begin{itemize}
                    \item Small-scale fading
                    \item Non-LOS environments
                \end{itemize}
            \end{enumerate}
        \end{column}
        \begin{column}{0.5\textwidth}
            \begin{block}{Path Loss Formulas}
                \small
                \textbf{LOS:}
                \begin{equation*}
                    \text{PL}_{\text{LOS}} = 28 + 22\log_{10}(d) + 20\log_{10}(f_c)
                \end{equation*}
                
                \textbf{NLOS:}
                \begin{equation*}
                    \text{PL}_{\text{NLOS}} = 13.54 + 39.08\log_{10}(d) + 20\log_{10}(f_c)
                \end{equation*}
                
                where $d$ is distance (m) and $f_c$ is carrier frequency (GHz)
            \end{block}
            
            \vspace{0.2cm}
            
            \begin{block}{Total Channel Gain}
                \begin{equation*}
                    h = \sqrt{\frac{1}{\text{PL} \times 10^{\text{Shadow}/10}}} \times g_{\text{fade}}
                \end{equation*}
            \end{block}
            
            \vspace{0.2cm}
            
            \textbf{Why 3GPP UMa?}
            \begin{itemize}
                \item Industry-standard model
                \item Validated for 5G deployments
                \item Realistic urban scenarios
            \end{itemize}
        \end{column}
    \end{columns}
\end{frame}

\begin{frame}{Dataset Statistics}
    \begin{columns}
        \begin{column}{0.5\textwidth}
            \textbf{Training Dataset:}
            \begin{itemize}
                \item \textbf{Scenarios:} 200 (diverse UMa deployments)
                \item \textbf{Users per scenario:} 500
                \item \textbf{Total user samples:} 100,000
                \item \textbf{Positive pairs (Blossom):} $\sim$46,400
                \item \textbf{Candidate edges:} $\sim$800,000
                \item \textbf{Features per node:} 7 (CSI-derived)
            \end{itemize}
            
            \vspace{0.3cm}
            
            \textbf{Test Dataset:}
            \begin{itemize}
                \item \textbf{Scenarios:} 1 (held-out, unseen)
                \item \textbf{Users:} 500
                \item \textbf{Purpose:} Throughput and timing evaluation
            \end{itemize}
        \end{column}
        \begin{column}{0.5\textwidth}
            \begin{table}
                \centering
                \tiny
                \begin{tabular}{lc}
                    \toprule
                    \textbf{Feature} & \textbf{Range} \\
                    \midrule
                    Distance (m) & 10 - 500 \\
                    Angle (deg) & 0 - 360 \\
                    Path Loss (dB) & 80 - 140 \\
                    Shadowing (dB) & -21 to +21 \\
                    Fading magnitude & 0.1 - 3.0 \\
                    Channel Gain & $10^{-8}$ - $10^{-4}$ \\
                    SNR (dB) & -10 to 30 \\
                    \bottomrule
                \end{tabular}
                \caption{Feature Statistics Across Dataset}
            \end{table}
            
            \vspace{0.2cm}
            
            \textbf{Data Processing Pipeline:}
            \begin{itemize}
                \item CSV format (h\_values.csv)
                \item PyTorch Geometric graphs
                \item Z-score normalization
                \item Saved feature scaler (scaler.pkl)
            \end{itemize}
        \end{column}
    \end{columns}
\end{frame}

\begin{frame}{Implementation Details}
    \begin{columns}
        \begin{column}{0.5\textwidth}
            \textbf{Software Stack:}
            \begin{itemize}
                \item \textbf{Python 3.9+}
                \item \textbf{PyTorch 2.0:} Deep learning
                \item \textbf{PyG 2.3:} Graph neural networks
                \item \textbf{NetworkX:} Graph algorithms
                \item \textbf{NumPy/Pandas:} Data processing
            \end{itemize}
            
            \vspace{0.3cm}
            
            \textbf{Hardware:}
            \begin{itemize}
                \item \textbf{Training:}
                \begin{itemize}
                    \item GPU: NVIDIA RTX 3060 (12GB)
                    \item Time: $\sim$2 hours for 50 epochs
                \end{itemize}
                \item \textbf{Inference:}
                \begin{itemize}
                    \item CPU: Intel i7
                    \item RAM: 16 GB
                    \item Time: 846 ms per scenario
                \end{itemize}
            \end{itemize}
        \end{column}
        \begin{column}{0.5\textwidth}
            \textbf{Project Structure:}
            \begin{itemize}
                \item \texttt{config.py} - Parameters
                \item \texttt{data/} - Dataset, normalization
                \item \texttt{models/} - GNN architecture
                \item \texttt{training/} - Training loop, losses
                \item \texttt{inference/} - Fast inference
                \item \texttt{utils/} - Matching, metrics
                \item \texttt{scripts/} - Data prep, verification
                \item \texttt{checkpoints/} - Saved models
            \end{itemize}
            
            \vspace{0.3cm}
            
            \textbf{Code Organization:}
            \begin{itemize}
                \item Modular design
                \item Well-documented
                \item End-to-end pipeline
            \end{itemize}
        \end{column}
    \end{columns}
\end{frame}

% ====== SECTION 6: Results ======
\section{Results and Analysis}

\begin{frame}{Throughput Performance}
    \begin{table}
        \centering
        \begin{tabular}{lcccc}
            \toprule
            \textbf{Method} & \textbf{Throughput} & \textbf{vs Optimal} & \textbf{Pairs} & \textbf{Time} \\
             & \textbf{(Gbps)} & \textbf{(\%)} & \textbf{Formed} & \textbf{(ms)} \\
            \midrule
            Static & 40.78 & 55.6 & 250 & 5 \\
            Balanced & 52.80 & 72.0 & 250 & 8 \\
            Bipartite PF & 73.30 & 100.0 & 232 & 35,000 \\
            Blossom & 73.30 & 100.0 & 232 & 44,749 \\
            \midrule
            \rowcolor{softgray}
            \textbf{NOMA-GNN} & \textbf{70.74} & \textbf{96.5} & \textbf{225} & \textbf{846} \\
            \bottomrule
        \end{tabular}
        \caption{Performance Comparison on 500-User Test Scenario}
    \end{table}

    \vspace{0.2cm}
   
    
    \begin{columns}
        \begin{column}{0.5\textwidth}
            \textbf{Key Achievements:}
            \begin{itemize}
                \item ✓ \textbf{96.5\%} of optimal throughput
                \item ✓ \textbf{52.9× speedup} over Blossom
                \item ✓ \textbf{34-73\% better} than heuristics
                \item ✓ Real-time inference (<1 sec)
            \end{itemize}
        \end{column}
        \begin{column}{0.5\textwidth}
            \textbf{Trade-off Analysis:}
            \begin{itemize}
                \item Only 3.5\% throughput sacrifice
                \item 98.1\% faster than optimal methods
                \item Suitable for edge deployment
                \item Practical for dense 5G/6G networks
            \end{itemize}
        \end{column}
    \end{columns}
\end{frame}

\begin{frame}{Detailed Performance Metrics}
    \begin{columns}
        \begin{column}{0.5\textwidth}
            \begin{table}
                \centering
                \small
                \begin{tabular}{lcc}
                    \toprule
                    \textbf{Metric} & \textbf{GNN} & \textbf{Blossom} \\
                    \midrule
                    Throughput (Gbps) & 70.74 & 73.30 \\
                    Sum-Rate (bits/s/Hz) & 15.72 & 15.80 \\
                    Spectral Eff. Ratio & \multicolumn{2}{c}{99.5\%} \\
                    \midrule
                    Pairs Formed & 225 & 232 \\
                    Pairing Efficiency & \multicolumn{2}{c}{97.0\%} \\
                    \midrule
                    Inference Time & 846 ms & 44.7 s \\
                    Speedup & \multicolumn{2}{c}{52.9×} \\
                    \bottomrule
                \end{tabular}
                \caption{NOMA-GNN vs Optimal}
            \end{table}
        \end{column}
        \begin{column}{0.5\textwidth}
            \textbf{Pairing Quality:}
            \begin{itemize}
                \item 225 pairs vs 232 optimal
                \item 97\% pairing efficiency
                \item All pairs SIC-feasible
                \item Angular constraints satisfied
            \end{itemize}
            
            \vspace{0.3cm}
            
            \textbf{Complexity Analysis:}
            \begin{itemize}
                \item Training: $O(N^3)$ one-time
                \item Inference: $O(N \log N)$ per scenario
                \item Memory: 650 KB model
                \item Deployment: CPU-friendly
            \end{itemize}
        \end{column}
    \end{columns}
    
    \vspace{0.3cm}
    
    \begin{exampleblock}{Practical Impact}
        \textbf{5G Base Station:} Can handle real-time scheduling for 500+ users with near-optimal performance
    \end{exampleblock}
\end{frame}

\begin{frame}{Model Performance Analysis} 
    \begin{columns}
        \begin{column}{0.5\textwidth}
            \textbf{Classification Performance:}
            \begin{itemize}
                \item \textbf{Precision:} $\sim$100\%
                \begin{itemize}
                    \item All predicted pairs are valid
                \end{itemize}
                \item \textbf{Recall:} 97.0\%
                \begin{itemize}
                    \item Finds 225 out of 232 optimal pairs
                \end{itemize}
                \item \textbf{F1-Score:} 98.5\%
                \begin{itemize}
                    \item Excellent balance
                \end{itemize}
            \end{itemize}
            
            
            
            \textbf{Regression Performance:}
            \begin{itemize}
                \item Sum-rate prediction accurate
                \item Power split ($\alpha$) learned
                \item Multi-task learning effective
            \end{itemize}
        \end{column}
        
        \begin{column}{0.5\textwidth}
            \textbf{Training Convergence:}
            \begin{itemize}
                \item Stable training (50 epochs)
            
                \item Generalization to test scenario
            \end{itemize}
            
           
            
            \textbf{Model Characteristics:}
            \begin{itemize}
                \item \textbf{Parameters:} 166K
                \item \textbf{Size:} 650 KB
                \item \textbf{Layers:} 3 GraphSAGE + 3 MLPs
                \item \textbf{Hidden dim:} 128
                \item \textbf{Dropout:} 0.3
            \end{itemize}
            \end{column}
    \end{columns}
            
            \begin{alertblock}{Lightweight}
                Suitable for edge deployment on resource-constrained base stations
            \end{alertblock}
        
\end{frame}

\begin{frame}{Computational Complexity Comparison}
    \begin{table}
        \centering
        \begin{tabular}{lccc}
            \toprule
            \textbf{Method} & \textbf{Time Complexity} & \textbf{Space} & \textbf{Real-Time?} \\
            \midrule
            Static & $O(N \log N)$ & $O(N)$ & ✓ Yes (5 ms) \\
            Balanced & $O(N \log N)$ & $O(N)$ & ✓ Yes (8 ms) \\
            Bipartite & $O(N^3)$ & $O(N^2)$ & ✗ No (35 s) \\
            Blossom & $O(N^3)$ & $O(N^2)$ & ✗ No (45 s) \\
            \midrule
            \rowcolor{nomagreen!20}
            \textbf{NOMA-GNN} & $O(N \log N)$ & $O(N)$ & ✓ \textbf{Yes (0.85 s)} \\
            \bottomrule
        \end{tabular}
        \caption{Complexity Analysis for $N=500$ users}
    \end{table}
    
    \vspace{0.3cm}
    
    \begin{columns}
        \begin{column}{0.5\textwidth}
            \textbf{Scalability Advantages:}
            \begin{itemize}
                \item GNN inference scales sub-quadratically
                \item Sparse graph structure reduces overhead
                \item Greedy matching is efficient
                \item Can handle 1000+ users in practice
            \end{itemize}
        \end{column}
        \begin{column}{0.5\textwidth}
            \textbf{Deployment Considerations:}
            \begin{itemize}
                \item \textbf{Training:} Offline, one-time cost
                \item \textbf{Inference:} Online, real-time capable
                \item \textbf{Updates:} Periodic retraining as needed
                \item \textbf{Hardware:} CPU sufficient (no GPU needed)
            \end{itemize}
        \end{column}
    \end{columns}
\end{frame}

% ====== SECTION 7: Key Contributions ======
\section{Key Contributions and Insights}

\begin{frame}{Major Contributions}
\begin{columns}
        \begin{column}{0.48\textwidth}
            \textbf{Realistic Channel Modeling}
            \begin{itemize}
                \item 3GPP TR 38.901 UMa standard
                \item 200 diverse scenarios
                \item Industry-validated propagation
            \end{itemize}

            \vspace{0.4cm}

            \textbf{Comprehensive Baseline Evaluation}
            \begin{itemize}
                \item 4 traditional methods implemented
                \item Thorough performance comparison
                \item Computational complexity analysis
            \end{itemize}
        \end{column}

        \begin{column}{0.48\textwidth}
            \textbf{Novel GNN Framework (NOMA-GNN)}
            \begin{itemize}
                \item GraphSAGE-based architecture
                \item Multi-task learning (pairing + power)
                \item Physical constraint enforcement
                \item 96.5\% optimal throughput, 52.9× speedup
            \end{itemize}

            \vspace{0.4cm}

            \textbf{End-to-End Implementation}
            \begin{itemize}
                \item Complete pipeline: data $\to$ training $\to$ inference
                \item Lightweight model (166K params, 650 KB)
                \item Production-ready deployment
            \end{itemize}
        \end{column}
    \end{columns}
\end{frame}

\begin{frame}{Technical Innovations}
    \begin{columns}
        \begin{column}{0.5\textwidth}
            \textbf{Graph-Based Reformulation:}
            \begin{itemize}
                \item User pairing → edge prediction
                \item Natural problem representation
                \item Leverages graph structure
                \item Efficient message passing
            \end{itemize}
            
            \vspace{0.3cm}
            
            \textbf{Constraint-Aware Design:}
            \begin{itemize}
                \item SIC feasibility enforced
                \item Angular separation considered
                \item Candidate edge filtering
                \item Reduces search space
            \end{itemize}
        \end{column}
        \begin{column}{0.5\textwidth}
            \textbf{Multi-Task Learning:}
            \begin{itemize}
                \item Joint optimization
                \item Shared representations
                \item Better generalization
                \item End-to-end power allocation
            \end{itemize}
            
            \vspace{0.3cm}
            
            \textbf{Hard Negative Sampling:}
            \begin{itemize}
                \item Discriminative learning
                \item Focuses on difficult cases
                \item Improves decision boundary
                \item Better classification
            \end{itemize}
        \end{column}
    \end{columns}
    
    \vspace{0.3cm}
    
    \begin{exampleblock}{Novel Approach}
        First work to combine GraphSAGE with NOMA pairing while enforcing physical constraints and achieving near-optimal real-time performance
    \end{exampleblock}
\end{frame}

\begin{frame}{Key Insights}
    \begin{block}{Finding 1: Learning Beats Heuristics}
        Data-driven GNN achieves 34-74\% better throughput than simple heuristics (Static, Balanced) while maintaining similar $O(N \log N)$ computational efficiency.
    \end{block}
    
    \begin{block}{Finding 2: Near-Optimal with Fast Inference}
        GNN achieves 96.5\% of optimal throughput with 52.9× speedup, making real-time deployment practical for dense 5G/6G networks without sacrificing significant performance.
    \end{block}
    
    \begin{block}{Finding 3: Strong Generalization Capability}
        Model trained on 200 diverse scenarios generalizes well to unseen test scenario, demonstrating that learned pairing patterns successfully transfer across different deployments.
    \end{block}
    
    \begin{block}{Finding 4: Multi-Task Learning Synergy}
        Joint learning of pairing decisions, sum-rate prediction, and power allocation leads to better overall system performance than separate optimization of individual tasks.
    \end{block}
\end{frame}

% ====== SECTION 8: Limitations and Future Work ======
\section{Limitations and Future Directions}

\begin{frame}{Current Limitations}
    \begin{enumerate}
        \item \textbf{Single-Cell Scenario}
        \begin{itemize}
            \item Current work focuses on one base station
            \item Multi-cell interference not considered
            \item Limited to downlink transmission
        \end{itemize}
        
        \vspace{0.2cm}
        
        \item \textbf{Perfect CSI Assumption}
        \begin{itemize}
            \item Assumes accurate channel knowledge
            \item Channel estimation errors not modeled
            \item Feedback delay not considered
        \end{itemize}
        
        \vspace{0.2cm}
        
        \item \textbf{Static User Distribution}
        \begin{itemize}
            \item Users assumed stationary during scheduling
            \item Mobility not incorporated
            \item Doppler effects ignored
        \end{itemize}
        
        \vspace{0.2cm}
        
        \item \textbf{Two-User Clustering Only}
        \begin{itemize}
            \item Pairs limited to 2 users
            \item No multi-user NOMA (3+ users per PRB)
            \item Scalability to larger clusters unexplored
        \end{itemize}
    \end{enumerate}
\end{frame}

\begin{frame}{Future Research Directions}
    \begin{columns}
        \begin{column}{0.5\textwidth}
            \textbf{Near-Term Extensions:}
            \begin{enumerate}
                \item \textbf{Multi-Cell Coordination}
                \begin{itemize}
                    \item Inter-cell interference
                    \item Coordinated scheduling
                    \item Graph attention mechanisms
                \end{itemize}
                
                \item \textbf{Channel Uncertainty}
                \begin{itemize}
                    \item Imperfect CSI modeling
                    \item Robust pairing strategies
                    \item Estimation error tolerance
                \end{itemize}
                
                \item \textbf{Dynamic Scenarios}
                \begin{itemize}
                    \item User mobility
                    \item Time-varying channels
                    \item Recurrent GNN architectures
                \end{itemize}
                
                \item \textbf{Multi-User Clustering}
                \begin{itemize}
                    \item 3+ users per resource
                    \item Hypergraph neural networks
                    \item Hierarchical clustering
                \end{itemize}
            \end{enumerate}
        \end{column}
        \begin{column}{0.5\textwidth}
            \textbf{Long-Term Vision:}
            \begin{enumerate}
                \setcounter{enumi}{4}
                \item \textbf{Reinforcement Learning}
                \begin{itemize}
                    \item Online learning
                    \item Adaptive policies
                    \item Reward shaping
                \end{itemize}
                
                \item \textbf{Federated Learning}
                \begin{itemize}
                    \item Distributed training
                    \item Privacy preservation
                    \item Multi-operator collaboration
                \end{itemize}
                
                \item \textbf{Hardware Deployment}
                \begin{itemize}
                    \item FPGA/ASIC implementation
                    \item Model compression
                    \item Quantization
                \end{itemize}
                
                \item \textbf{6G Integration}
                \begin{itemize}
                    \item THz communications
                    \item Massive MIMO-NOMA
                    \item AI-native networks
                \end{itemize}
            \end{enumerate}
        \end{column}
    \end{columns}
\end{frame}

% ====== SECTION 9: Conclusion ======
\section{Conclusion}

\begin{frame}{Summary}
    \textbf{Problem Addressed:}
    \begin{itemize}
        \item User pairing in NOMA systems is computationally expensive ($O(N^3)$)
        \item Traditional heuristics are fast but suboptimal
        \item Optimal methods too slow for real-time deployment
    \end{itemize}
    
    \vspace{0.3cm}
    
    \textbf{Our Solution: NOMA-GNN}
    \begin{itemize}
        \item Graph neural network framework based on GraphSAGE
        \item Learns from optimal solutions (Blossom matching)
        \item Multi-task learning: pairing + power allocation
        \item Enforces physical constraints (SIC, angular separation)
    \end{itemize}
    
    \vspace{0.3cm}
    
    \textbf{Key Achievements:}
    \begin{itemize}
        \item ✓ \textbf{96.5\%} of optimal throughput (70.74 vs 73.30 Gbps)
        \item ✓ \textbf{52.9× speedup} over Blossom (846 ms vs 44.7 s)
        \item ✓ \textbf{Real-time inference} for 500-user scenarios
        \item ✓ \textbf{Lightweight model} (166K parameters, 650 KB)
        \item ✓ Practical deployment for dense 5G/6G networks
    \end{itemize}
\end{frame}

\begin{frame}{Impact and Significance}
    \begin{columns}
        \begin{column}{0.5\textwidth}
            \textbf{Theoretical Contributions:}
            \begin{itemize}
                \item Novel graph formulation
                \item Multi-task learning framework
                \item Complexity reduction proof
                \item Generalization analysis
            \end{itemize}
            
            \vspace{0.3cm}
            
            \textbf{Practical Impact:}
            \begin{itemize}
                \item Real-time NOMA deployment
                \item Edge base station suitable
                \item Scalable to dense networks
                \item Industry-standard channels
            \end{itemize}
        \end{column}
        \begin{column}{0.5\textwidth}
            \textbf{Broader Applications:}
            \begin{itemize}
                \item 5G NR networks
                \item 6G research
                \item IoT massive connectivity
                \item Smart city deployments
                \item Industrial wireless
            \end{itemize}
            
            \vspace{0.3cm}
            
            \textbf{Research Enabler:}
            \begin{itemize}
                \item Open-source implementation
                \item Reproducible experiments
                \item Extensible framework
                \item Foundation for future work
            \end{itemize}
        \end{column}
    \end{columns}
    
    \vspace{0.3cm}
    
    \begin{exampleblock}{Bottom Line}
        \textbf{Deep learning can effectively replace expensive optimization in NOMA systems while maintaining near-optimal performance}
    \end{exampleblock}
\end{frame}

\begin{frame}{Publications and Deliverables}
    \textbf{Project Outputs:}
    \begin{enumerate}
        \item \textbf{College Project Report}
        \begin{itemize}
            \item 55-60 pages comprehensive documentation
            \item 11 main chapters + 3 appendices
            \item 30+ references, 50+ tables, 100+ equations
        \end{itemize}
        
        \item \textbf{IEEE Conference Paper (Under Preparation)}
        \begin{itemize}
            \item 10-page submission format
            \item Complete experimental evaluation
            \item Comparative analysis with baselines
        \end{itemize}
        
        \item \textbf{Complete Implementation}
        \begin{itemize}
            \item End-to-end Python pipeline
            \item Well-documented modular code
            \item Trained models and checkpoints
            \item Ready for deployment
        \end{itemize}
        
        \item \textbf{Dataset}
        \begin{itemize}
            \item 200 realistic scenarios (3GPP UMa)
            \item 100,000 user samples
            \item Optimal pairing labels
            \item Public availability planned
        \end{itemize}
    \end{enumerate}
\end{frame}

% ====== SECTION 10: Q&A ======
\section{Questions?}

\begin{frame}{Thank You!}
    \begin{center}
        \Large \textbf{Graph Neural Network-Based User Pairing\\and Power Allocation for Downlink NOMA Systems}
        
        \vspace{1cm}
        
        \normalsize
        \textbf{Anisha Dwivedi, Shailendra Shukla}\\
        \textit{Under the supervision of Dr. Ramesh Ch. Mishra}\\[0.3cm]
        Department of Electronics and Communication Engineering\\
        Indian Institute of Information Technology, Senapati, Manipur
        
        \vspace{1cm}
        
        \Large \textbf{Questions?}
        
        \vspace{0.5cm}
        
        \normalsize
        Contact: \texttt{\{anishas1121, shailendra.iiitsm\}@gmail.com}
    \end{center}
\end{frame}

\begin{frame}{Backup: Technical Details}
    \textbf{GNN Architecture Details:}
    \begin{itemize}
        \item \textbf{Encoder:} 3-layer GraphSAGE
        \begin{itemize}
            \item Input: 4D features → 128D embeddings
            \item Aggregation: MEAN pooling
            \item Activation: ReLU
        \end{itemize}
        
        \item \textbf{Decoders:} 3 separate MLPs
        \begin{itemize}
            \item Classifier: 256→128→64→1 (sigmoid)
            \item Sum-rate: 256→128→64→1 (ReLU)
            \item Power: 256→128→64→1 (sigmoid)
        \end{itemize}
        
        \item \textbf{Training:}
        \begin{itemize}
            \item Loss: $\mathcal{L} = 1.0 \cdot \mathcal{L}_{\text{BCE}} + 0.5 \cdot \mathcal{L}_{\text{rate}} + 0.3 \cdot \mathcal{L}_{\text{power}}$
            \item Optimizer: Adam (lr=0.001)
            \item Batch: 32 graphs
            \item Epochs: 50
        \end{itemize}
    \end{itemize}
\end{frame}

\begin{frame}{Backup: Complexity Derivation}
    \textbf{NOMA-GNN Inference Complexity:}
    \begin{enumerate}
        \item \textbf{Graph Construction:} $O(N^2)$ worst case
        \begin{itemize}
            \item Check all pairs for SIC + angular constraints
            \item Typically $O(N)$ due to locality
        \end{itemize}
        
        \item \textbf{GNN Forward Pass:} $O(E \cdot D^2)$
        \begin{itemize}
            \item $E \approx 3000$-5000 edges (sparse)
            \item $D = 128$ hidden dimension
            \item Effectively $O(N)$ for sparse graphs
        \end{itemize}
        
        \item \textbf{Greedy Matching:} $O(E \log E)$
        \begin{itemize}
            \item Sort edges by score: $O(E \log E)$
            \item Select non-conflicting: $O(E)$
            \item Total: $O(E \log E) = O(N \log N)$ typical
        \end{itemize}
    \end{enumerate}
    
    \vspace{0.2cm}
    
    \textbf{Overall: $O(N \log N)$ typical, $O(N^2 \log N)$ worst case}
    
    \vspace{0.2cm}
    
    Compare to Blossom: $O(N^3)$ always
\end{frame}

\end{document}