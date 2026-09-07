# Mathematical and DSP Specifications

## 1. DC Offset Removal
For complex baseband signal $x[n] = I[n] + j Q[n]$:
$$\mu_I = \frac{1}{N} \sum_{n=0}^{N-1} I[n], \quad \mu_Q = \frac{1}{N} \sum_{n=0}^{N-1} Q[n]$$
$$x_{\text{corrected}}[n] = x[n] - (\mu_I + j \mu_Q)$$
Magnitude DC offset: $\mu_{\text{mag}} = \sqrt{\mu_I^2 + \mu_Q^2}$.

---

## 2. Normalization
- **RMS Normalization**:
  $$x_{\text{rms}} = \sqrt{\frac{1}{N} \sum_{n=0}^{N-1} |x[n]|^2}, \quad x_{\text{norm}}[n] = \frac{x[n]}{x_{\text{rms}}}$$
- **Peak Normalization**:
  $$x_{\text{norm}}[n] = \frac{x[n]}{\max_{n} |x[n]|}$$

---

## 3. Analytic Signal & Instantaneous Properties
For a real passband signal $s(t)$, the complex analytic signal is:
$$z(t) = s(t) + j \mathcal{H}\{s(t)\} = A(t) e^{j \phi(t)}$$
- **Instantaneous Amplitude (Envelope)**: $A[n] = |z[n]|$
- **Instantaneous Phase**: $\phi[n] = \text{unwrap}(\arg(z[n]))$
- **Instantaneous Frequency**:
  $$f_{\text{inst}}[n] = \frac{f_s}{2\pi} \cdot \frac{d\phi[n]}{dt}$$
  Evaluated using Savitzky-Golay smoothed central differences.

---

## 4. Higher-Order Cumulants (HOC)
For a zero-mean complex baseband signal $x[n]$:
- $C_{20} = E[x^2]$
- $C_{21} = E[|x|^2]$
- $C_{40} = E[x^4] - 3(E[x^2])^2$
- $C_{41} = E[x^3 x^*] - 3 E[x^2] E[|x|^2]$
- $C_{42} = E[|x|^4] - |E[x^2]|^2 - 2(E[|x|^2])^2$

Normalized invariants:
$$f_{40} = \frac{|C_{40}|}{C_{21}^2}, \quad f_{41} = \frac{|C_{41}|}{C_{21}^2}, \quad f_{42} = \frac{|C_{42}|}{C_{21}^2}$$

### Theoretical Invariant Values:
| Modulation | $f_{40}$ | $f_{42}$ | Notes |
|:---|:---:|:---:|:---|
| **Gaussian Noise** | 0.00 | 0.00 | Both 4th cumulants vanish |
| **BPSK** | 2.00 | 2.00 | Pure 1D real constellation |
| **QPSK** | 1.00 | 1.00 | Quadrature symmetry ($x^4 = -1$) |
| **8PSK** | 0.00 | 1.00 | 8-phase circle ($E[x^4] = 0$) |
| **16-QAM** | 0.68 | 0.68 | Multi-level square grid |

---

## 5. Error Vector Magnitude (EVM)
For received symbols $r_k$ and nearest ideal reference symbols $s_k$:
$$e_k = r_k - s_k$$
$$\text{EVM}_{\text{rms}} = \sqrt{\frac{\sum_{k=1}^K |e_k|^2}{\sum_{k=1}^K |s_k|^2}} \times 100\%$$
$$\text{EVM}_{\text{peak}} = \frac{\max_k |e_k|}{\text{RMS}(|s|)} \times 100\%$$
$$\text{Magnitude Error} = \sqrt{\frac{1}{K} \sum_{k=1}^K (|r_k| - |s_k|)^2} \times 100\%$$
$$\text{Phase Error} = \sqrt{\frac{1}{K} \sum_{k=1}^K (\Delta \phi_k)^2} \times \frac{180^\circ}{\pi}$$
