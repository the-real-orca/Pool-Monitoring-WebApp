# Benchmark ALL Models (10 images)

## Anthropic: Claude Opus 4.7

```
OpenRouter SDK version: 0.9.1
Model: anthropic/claude-opus-4.7
Images: 10

  Analyzing 20260524_115452.jpg (4080×1884 → 2048×946 px, 154 KB) ... OK
  Analyzing 20260525_094358.jpg (4080×1884 → 2048×946 px, 254 KB) ... FAILED → -1
  Analyzing 20260524_115516.jpg (4080×1884 → 2048×946 px, 216 KB) ... OK
  Analyzing 20260524_123629.jpg (4080×1884 → 2048×946 px, 294 KB) ... OK
  Analyzing 20260524_115506.jpg (4080×1884 → 2048×946 px, 275 KB) ... OK
  Analyzing 20260524_123636.jpg (4080×1884 → 2048×946 px, 263 KB) ... OK
  Analyzing 20260524_123656.jpg (4080×1884 → 2048×946 px, 208 KB) ... OK
  Analyzing 20260524_123639.jpg (4080×1884 → 2048×946 px, 247 KB) ... OK
  Analyzing 20260525_094358.jpg (4080×1884 → 2048×946 px, 254 KB) ... OK
  Analyzing 20260525_094404.jpg (4080×1884 → 2048×946 px, 206 KB) ... OK

============================================================
BENCHMARK RESULTS
============================================================

  20260524_115452.jpg
    Ground truth:  pH=7.0, Cl=0.0  (2026-05-24 11:54)
    Predicted:     pH=7.0, Cl=0.3
    Warnings:      GT: –  |  AI: –
    Scores:        pH=100%  Cl=70%  =>  Total: 85%

  20260525_094358.jpg
    Ground truth:  pH=-1.0, Cl=-1.0  (2026-05-25 09:43)
    Predicted:     pH=-1.0, Cl=-1.0
    Warnings:      GT: no reference scale  |  AI: analysis failed or refused
    Scores:        pH=100%  Cl=100%  =>  Total: 100%

  20260524_115516.jpg
    Ground truth:  pH=6.8, Cl=0.2  (2026-05-24 11:55)
    Predicted:     pH=7.0, Cl=0.2
    Warnings:      GT: –  |  AI: –
    Scores:        pH=80%  Cl=100%  =>  Total: 90%

  20260524_123629.jpg
    Ground truth:  pH=7.2, Cl=0.4  (2026-05-24 12:36)
    Predicted:     pH=6.8, Cl=3.0
    Warnings:      GT: –  |  AI: –
    Scores:        pH=60%  Cl=0%  =>  Total: 30%

  20260524_115506.jpg
    Ground truth:  pH=7.0, Cl=0.0  (2026-05-24 11:55)
    Predicted:     pH=7.2, Cl=0.0
    Warnings:      GT: –  |  AI: –
    Scores:        pH=80%  Cl=100%  =>  Total: 90%

  20260524_123636.jpg
    Ground truth:  pH=7.2, Cl=0.4  (2026-05-24 12:36)
    Predicted:     pH=6.8, Cl=1.0
    Warnings:      GT: –  |  AI: –
    Scores:        pH=60%  Cl=40%  =>  Total: 50%

  20260524_123656.jpg
    Ground truth:  pH=7.3, Cl=0.6  (2026-05-24 12:36)
    Predicted:     pH=7.2, Cl=3.0
    Warnings:      GT: –  |  AI: Test strip pads are difficult to distinguish from the bottle's reference chart due to orientation and overlap
    Scores:        pH=90%  Cl=0%  =>  Total: 34%  ⚠ mismatch (-25%)

  20260524_123639.jpg
    Ground truth:  pH=6.8, Cl=0.5  (2026-05-24 12:36)
    Predicted:     pH=6.8, Cl=1.0
    Warnings:      GT: –  |  AI: –
    Scores:        pH=100%  Cl=50%  =>  Total: 75%

  20260525_094358.jpg
    Ground truth:  pH=-1.0, Cl=-1.0  (2026-05-25 09:43)
    Predicted:     pH=-1.0, Cl=-1.0
    Warnings:      GT: no reference scale  |  AI: No color reference scale visible in image - cannot match pad colors to values
    Scores:        pH=100%  Cl=100%  =>  Total: 100%

  20260525_094404.jpg
    Ground truth:  pH=6.4, Cl=0.6  (2026-05-25 09:44)
    Predicted:     pH=7.2, Cl=1.5
    Warnings:      GT: –  |  AI: –
    Scores:        pH=20%  Cl=0%  =>  Total: 10%

  ────────────────────────────────────────
  Scores:   avg=66.4%  min=10%  max=100%
  Passed (≥50%):      6/10

============================================================
COST SUMMARY
============================================================
  gen-1779906503-5tbYdGSkHOi352jzNix3: $0.017760
  gen-1779906511-rLbtCRRC9itlLJ095DOV: $0.017760
  gen-1779906516-8hhzeZSKgxAPxRtFPCS6: $0.017710
  gen-1779906519-TaRr6Kg0YyhjDdUdPzZo: $0.018060
  gen-1779906523-MAnVB4FcRYhfieACUS4K: $0.017760
  gen-1779906527-bci1Y3stBA5HvPDRHMkX: $0.018835
  gen-1779906533-atIg4qU3Ku9ojNQBesRu: $0.017760
  gen-1779906537-T96dLQWEqVtPwnV3iXuj: $0.018635
  gen-1779906541-copU7voKx9JhlPmQf0gK: $0.018110
  ────────────────────────────────────────
  Total: $0.162390

Done.
```


## OpenAI: GPT-5.5

```
OpenRouter SDK version: 0.9.1
Model: openai/gpt-5.5
Images: 10

  Analyzing 20260524_115452.jpg (4080×1884 → 2048×946 px, 154 KB) ... FAILED → -1
  Analyzing 20260525_094358.jpg (4080×1884 → 2048×946 px, 254 KB) ... FAILED → -1
  Analyzing 20260524_115516.jpg (4080×1884 → 2048×946 px, 216 KB) ... FAILED → -1
  Analyzing 20260524_123629.jpg (4080×1884 → 2048×946 px, 294 KB) ... FAILED → -1
  Analyzing 20260524_115506.jpg (4080×1884 → 2048×946 px, 275 KB) ... FAILED → -1
  Analyzing 20260524_123636.jpg (4080×1884 → 2048×946 px, 263 KB) ... FAILED → -1
  Analyzing 20260524_123656.jpg (4080×1884 → 2048×946 px, 208 KB) ... FAILED → -1
  Analyzing 20260524_123639.jpg (4080×1884 → 2048×946 px, 247 KB) ... FAILED → -1
  Analyzing 20260525_094358.jpg (4080×1884 → 2048×946 px, 254 KB) ... FAILED → -1
  Analyzing 20260525_094404.jpg (4080×1884 → 2048×946 px, 206 KB) ... FAILED → -1

============================================================
BENCHMARK RESULTS
============================================================

  20260524_115452.jpg
    Ground truth:  pH=7.0, Cl=0.0  (2026-05-24 11:54)
    Predicted:     pH=-1.0, Cl=-1.0
    Warnings:      GT: –  |  AI: analysis failed or refused
    Scores:        pH=0%  Cl=0%  =>  Total: 0%

  20260525_094358.jpg
    Ground truth:  pH=-1.0, Cl=-1.0  (2026-05-25 09:43)
    Predicted:     pH=-1.0, Cl=-1.0
    Warnings:      GT: no reference scale  |  AI: analysis failed or refused
    Scores:        pH=100%  Cl=100%  =>  Total: 100%

  20260524_115516.jpg
    Ground truth:  pH=6.8, Cl=0.2  (2026-05-24 11:55)
    Predicted:     pH=-1.0, Cl=-1.0
    Warnings:      GT: –  |  AI: analysis failed or refused
    Scores:        pH=0%  Cl=0%  =>  Total: 0%

  20260524_123629.jpg
    Ground truth:  pH=7.2, Cl=0.4  (2026-05-24 12:36)
    Predicted:     pH=-1.0, Cl=-1.0
    Warnings:      GT: –  |  AI: analysis failed or refused
    Scores:        pH=0%  Cl=0%  =>  Total: 0%

  20260524_115506.jpg
    Ground truth:  pH=7.0, Cl=0.0  (2026-05-24 11:55)
    Predicted:     pH=-1.0, Cl=-1.0
    Warnings:      GT: –  |  AI: analysis failed or refused
    Scores:        pH=0%  Cl=0%  =>  Total: 0%

  20260524_123636.jpg
    Ground truth:  pH=7.2, Cl=0.4  (2026-05-24 12:36)
    Predicted:     pH=-1.0, Cl=-1.0
    Warnings:      GT: –  |  AI: analysis failed or refused
    Scores:        pH=0%  Cl=0%  =>  Total: 0%

  20260524_123656.jpg
    Ground truth:  pH=7.3, Cl=0.6  (2026-05-24 12:36)
    Predicted:     pH=-1.0, Cl=-1.0
    Warnings:      GT: –  |  AI: analysis failed or refused
    Scores:        pH=0%  Cl=0%  =>  Total: 0%

  20260524_123639.jpg
    Ground truth:  pH=6.8, Cl=0.5  (2026-05-24 12:36)
    Predicted:     pH=-1.0, Cl=-1.0
    Warnings:      GT: –  |  AI: analysis failed or refused
    Scores:        pH=0%  Cl=0%  =>  Total: 0%

  20260525_094358.jpg
    Ground truth:  pH=-1.0, Cl=-1.0  (2026-05-25 09:43)
    Predicted:     pH=-1.0, Cl=-1.0
    Warnings:      GT: no reference scale  |  AI: analysis failed or refused
    Scores:        pH=100%  Cl=100%  =>  Total: 100%

  20260525_094404.jpg
    Ground truth:  pH=6.4, Cl=0.6  (2026-05-25 09:44)
    Predicted:     pH=-1.0, Cl=-1.0
    Warnings:      GT: –  |  AI: analysis failed or refused
    Scores:        pH=0%  Cl=0%  =>  Total: 0%

  ────────────────────────────────────────
  Scores:   avg=20.0%  min=0%  max=100%
  Passed (≥50%):      2/10

Done.
```


## Google: Gemini 3.1 Pro Preview

```
OpenRouter SDK version: 0.9.1
Model: google/gemini-3.1-pro-preview
Images: 10

  Analyzing 20260524_115452.jpg (4080×1884 → 2048×946 px, 154 KB) ... OK
  Analyzing 20260525_094358.jpg (4080×1884 → 2048×946 px, 254 KB) ... OK
  Analyzing 20260524_115516.jpg (4080×1884 → 2048×946 px, 216 KB) ... OK
  Analyzing 20260524_123629.jpg (4080×1884 → 2048×946 px, 294 KB) ... OK
  Analyzing 20260524_115506.jpg (4080×1884 → 2048×946 px, 275 KB) ... OK
  Analyzing 20260524_123636.jpg (4080×1884 → 2048×946 px, 263 KB) ... OK
  Analyzing 20260524_123656.jpg (4080×1884 → 2048×946 px, 208 KB) ... OK
  Analyzing 20260524_123639.jpg (4080×1884 → 2048×946 px, 247 KB) ... OK
  Analyzing 20260525_094358.jpg (4080×1884 → 2048×946 px, 254 KB) ... OK
  Analyzing 20260525_094404.jpg (4080×1884 → 2048×946 px, 206 KB) ... OK

============================================================
BENCHMARK RESULTS
============================================================

  20260524_115452.jpg
    Ground truth:  pH=7.0, Cl=0.0  (2026-05-24 11:54)
    Predicted:     pH=6.4, Cl=0.0
    Warnings:      GT: –  |  AI: –
    Scores:        pH=40%  Cl=100%  =>  Total: 70%

  20260525_094358.jpg
    Ground truth:  pH=-1.0, Cl=-1.0  (2026-05-25 09:43)
    Predicted:     pH=-1.0, Cl=-1.0
    Warnings:      GT: no reference scale  |  AI: No reference scale is visible in the image.
    Scores:        pH=100%  Cl=100%  =>  Total: 100%

  20260524_115516.jpg
    Ground truth:  pH=6.8, Cl=0.2  (2026-05-24 11:55)
    Predicted:     pH=7.0, Cl=0.0
    Warnings:      GT: –  |  AI: –
    Scores:        pH=80%  Cl=80%  =>  Total: 80%

  20260524_123629.jpg
    Ground truth:  pH=7.2, Cl=0.4  (2026-05-24 12:36)
    Predicted:     pH=6.8, Cl=0.2
    Warnings:      GT: –  |  AI: –
    Scores:        pH=60%  Cl=80%  =>  Total: 70%

  20260524_115506.jpg
    Ground truth:  pH=7.0, Cl=0.0  (2026-05-24 11:55)
    Predicted:     pH=6.8, Cl=0.0
    Warnings:      GT: –  |  AI: –
    Scores:        pH=80%  Cl=100%  =>  Total: 90%

  20260524_123636.jpg
    Ground truth:  pH=7.2, Cl=0.4  (2026-05-24 12:36)
    Predicted:     pH=7.0, Cl=0.0
    Warnings:      GT: –  |  AI: –
    Scores:        pH=80%  Cl=60%  =>  Total: 70%

  20260524_123656.jpg
    Ground truth:  pH=7.3, Cl=0.6  (2026-05-24 12:36)
    Predicted:     pH=7.2, Cl=0.0
    Warnings:      GT: –  |  AI: –
    Scores:        pH=90%  Cl=40%  =>  Total: 65%

  20260524_123639.jpg
    Ground truth:  pH=6.8, Cl=0.5  (2026-05-24 12:36)
    Predicted:     pH=6.8, Cl=0.0
    Warnings:      GT: –  |  AI: –
    Scores:        pH=100%  Cl=50%  =>  Total: 75%

  20260525_094358.jpg
    Ground truth:  pH=-1.0, Cl=-1.0  (2026-05-25 09:43)
    Predicted:     pH=-1.0, Cl=-1.0
    Warnings:      GT: no reference scale  |  AI: No reference scale visible to compare against.
    Scores:        pH=100%  Cl=100%  =>  Total: 100%

  20260525_094404.jpg
    Ground truth:  pH=6.4, Cl=0.6  (2026-05-25 09:44)
    Predicted:     pH=6.8, Cl=0.0
    Warnings:      GT: –  |  AI: –
    Scores:        pH=60%  Cl=40%  =>  Total: 50%

  ────────────────────────────────────────
  Scores:   avg=77.0%  min=50%  max=100%
  Passed (≥50%):      10/10

============================================================
COST SUMMARY
============================================================
  gen-1779906580-PuQwchM8xWeyIitsrpPY: $0.016282
  gen-1779906594-7Yzn2JrwnH8nBNrhXd7o: $0.003310
  gen-1779906599-PEw42o5rz3hhLUChbB66: $0.003476
  gen-1779906603-vxDfyST3zhE7FKYvC9vx: $0.003392
  gen-1779906607-fc3F5CvEx4dliAfiUHyF: $0.012992
  gen-1779906618-3sdpYUhuuLKTsYnMk5jU: $0.111142
  gen-1779906684-p2XVDjCR4scqpf8CvhFO: $0.117610
  gen-1779906779-RZpGNpyAsu4iaCaTgupb: $0.050242
  gen-1779906812-otJqZKpgc1AUYTkenYDQ: $0.008612
  gen-1779906819-ECJW5p9TyO2v83TZOe5E: $0.067258
  ────────────────────────────────────────
  Total: $0.394316

Done.
```


## Google: Gemini 3.5 Flash

```
OpenRouter SDK version: 0.9.1
Model: google/gemini-3.5-flash
Images: 10

  Analyzing 20260524_115452.jpg (4080×1884 → 2048×946 px, 154 KB) ... OK
  Analyzing 20260525_094358.jpg (4080×1884 → 2048×946 px, 254 KB) ... OK
  Analyzing 20260524_115516.jpg (4080×1884 → 2048×946 px, 216 KB) ... OK
  Analyzing 20260524_123629.jpg (4080×1884 → 2048×946 px, 294 KB) ... OK
  Analyzing 20260524_115506.jpg (4080×1884 → 2048×946 px, 275 KB) ... OK
  Analyzing 20260524_123636.jpg (4080×1884 → 2048×946 px, 263 KB) ... OK
  Analyzing 20260524_123656.jpg (4080×1884 → 2048×946 px, 208 KB) ... OK
  Analyzing 20260524_123639.jpg (4080×1884 → 2048×946 px, 247 KB) ... OK
  Analyzing 20260525_094358.jpg (4080×1884 → 2048×946 px, 254 KB) ... OK
  Analyzing 20260525_094404.jpg (4080×1884 → 2048×946 px, 206 KB) ... OK

============================================================
BENCHMARK RESULTS
============================================================

  20260524_115452.jpg
    Ground truth:  pH=7.0, Cl=0.0  (2026-05-24 11:54)
    Predicted:     pH=6.6, Cl=0.0
    Warnings:      GT: –  |  AI: –
    Scores:        pH=60%  Cl=100%  =>  Total: 80%

  20260525_094358.jpg
    Ground truth:  pH=-1.0, Cl=-1.0  (2026-05-25 09:43)
    Predicted:     pH=-1.0, Cl=-1.0
    Warnings:      GT: no reference scale  |  AI: No color reference scale found in the image
    Scores:        pH=100%  Cl=100%  =>  Total: 100%

  20260524_115516.jpg
    Ground truth:  pH=6.8, Cl=0.2  (2026-05-24 11:55)
    Predicted:     pH=6.8, Cl=0.0
    Warnings:      GT: –  |  AI: –
    Scores:        pH=100%  Cl=80%  =>  Total: 90%

  20260524_123629.jpg
    Ground truth:  pH=7.2, Cl=0.4  (2026-05-24 12:36)
    Predicted:     pH=7.2, Cl=0.1
    Warnings:      GT: –  |  AI: –
    Scores:        pH=100%  Cl=70%  =>  Total: 85%

  20260524_115506.jpg
    Ground truth:  pH=7.0, Cl=0.0  (2026-05-24 11:55)
    Predicted:     pH=6.5, Cl=0.0
    Warnings:      GT: –  |  AI: –
    Scores:        pH=50%  Cl=100%  =>  Total: 75%

  20260524_123636.jpg
    Ground truth:  pH=7.2, Cl=0.4  (2026-05-24 12:36)
    Predicted:     pH=7.1, Cl=0.0
    Warnings:      GT: –  |  AI: –
    Scores:        pH=90%  Cl=60%  =>  Total: 75%

  20260524_123656.jpg
    Ground truth:  pH=7.3, Cl=0.6  (2026-05-24 12:36)
    Predicted:     pH=7.3, Cl=1.0
    Warnings:      GT: –  |  AI: –
    Scores:        pH=100%  Cl=26%  =>  Total: 63%

  20260524_123639.jpg
    Ground truth:  pH=6.8, Cl=0.5  (2026-05-24 12:36)
    Predicted:     pH=6.8, Cl=0.5
    Warnings:      GT: –  |  AI: –
    Scores:        pH=100%  Cl=100%  =>  Total: 100%

  20260525_094358.jpg
    Ground truth:  pH=-1.0, Cl=-1.0  (2026-05-25 09:43)
    Predicted:     pH=-1.0, Cl=-1.0
    Warnings:      GT: no reference scale  |  AI: Missing color reference scale
    Scores:        pH=100%  Cl=100%  =>  Total: 100%

  20260525_094404.jpg
    Ground truth:  pH=6.4, Cl=0.6  (2026-05-25 09:44)
    Predicted:     pH=7.2, Cl=0.5
    Warnings:      GT: –  |  AI: –
    Scores:        pH=20%  Cl=90%  =>  Total: 55%

  ────────────────────────────────────────
  Scores:   avg=82.3%  min=55%  max=100%
  Passed (≥50%):      10/10

============================================================
COST SUMMARY
============================================================
  gen-1779906880-44FQEhUC5cEGX5UyUkeR: $0.017106
  gen-1779906892-Klk6nnpMQsCDxepHYZN0: $0.009969
  gen-1779906901-Ek7aJe6sMWOkNMMbvrqD: $0.018321
  gen-1779906915-0Eok3mo6LEIuu2xUQGRe: $0.020949
  gen-1779906929-byMRq5UsOgvnspQxFUxD: $0.017088
  gen-1779906940-c4OoARYZvCOHDwE9lwLR: $0.028077
  gen-1779906957-0eQsDJVw4NjyuBN6X5AZ: $0.029076
  gen-1779906979-obZEF8FckTr70VMfOeMv: $0.015711
  gen-1779906989-z2YhjFwABfLW4yShWu26: $0.013380
  gen-1779906999-PWDoWYtJ3CD8JU9MY0tq: $0.027231
  ────────────────────────────────────────
  Total: $0.196908

Done.
```


## OpenAI: GPT-5.4

```
OpenRouter SDK version: 0.9.1
Model: openai/gpt-5.4
Images: 10

  Analyzing 20260524_115452.jpg (4080×1884 → 2048×946 px, 154 KB) ... FAILED → -1
  Analyzing 20260525_094358.jpg (4080×1884 → 2048×946 px, 254 KB) ... FAILED → -1
  Analyzing 20260524_115516.jpg (4080×1884 → 2048×946 px, 216 KB) ... FAILED → -1
  Analyzing 20260524_123629.jpg (4080×1884 → 2048×946 px, 294 KB) ... FAILED → -1
  Analyzing 20260524_115506.jpg (4080×1884 → 2048×946 px, 275 KB) ... FAILED → -1
  Analyzing 20260524_123636.jpg (4080×1884 → 2048×946 px, 263 KB) ... FAILED → -1
  Analyzing 20260524_123656.jpg (4080×1884 → 2048×946 px, 208 KB) ... FAILED → -1
  Analyzing 20260524_123639.jpg (4080×1884 → 2048×946 px, 247 KB) ... FAILED → -1
  Analyzing 20260525_094358.jpg (4080×1884 → 2048×946 px, 254 KB) ... FAILED → -1
  Analyzing 20260525_094404.jpg (4080×1884 → 2048×946 px, 206 KB) ... FAILED → -1

============================================================
BENCHMARK RESULTS
============================================================

  20260524_115452.jpg
    Ground truth:  pH=7.0, Cl=0.0  (2026-05-24 11:54)
    Predicted:     pH=-1.0, Cl=-1.0
    Warnings:      GT: –  |  AI: analysis failed or refused
    Scores:        pH=0%  Cl=0%  =>  Total: 0%

  20260525_094358.jpg
    Ground truth:  pH=-1.0, Cl=-1.0  (2026-05-25 09:43)
    Predicted:     pH=-1.0, Cl=-1.0
    Warnings:      GT: no reference scale  |  AI: analysis failed or refused
    Scores:        pH=100%  Cl=100%  =>  Total: 100%

  20260524_115516.jpg
    Ground truth:  pH=6.8, Cl=0.2  (2026-05-24 11:55)
    Predicted:     pH=-1.0, Cl=-1.0
    Warnings:      GT: –  |  AI: analysis failed or refused
    Scores:        pH=0%  Cl=0%  =>  Total: 0%

  20260524_123629.jpg
    Ground truth:  pH=7.2, Cl=0.4  (2026-05-24 12:36)
    Predicted:     pH=-1.0, Cl=-1.0
    Warnings:      GT: –  |  AI: analysis failed or refused
    Scores:        pH=0%  Cl=0%  =>  Total: 0%

  20260524_115506.jpg
    Ground truth:  pH=7.0, Cl=0.0  (2026-05-24 11:55)
    Predicted:     pH=-1.0, Cl=-1.0
    Warnings:      GT: –  |  AI: analysis failed or refused
    Scores:        pH=0%  Cl=0%  =>  Total: 0%

  20260524_123636.jpg
    Ground truth:  pH=7.2, Cl=0.4  (2026-05-24 12:36)
    Predicted:     pH=-1.0, Cl=-1.0
    Warnings:      GT: –  |  AI: analysis failed or refused
    Scores:        pH=0%  Cl=0%  =>  Total: 0%

  20260524_123656.jpg
    Ground truth:  pH=7.3, Cl=0.6  (2026-05-24 12:36)
    Predicted:     pH=-1.0, Cl=-1.0
    Warnings:      GT: –  |  AI: analysis failed or refused
    Scores:        pH=0%  Cl=0%  =>  Total: 0%

  20260524_123639.jpg
    Ground truth:  pH=6.8, Cl=0.5  (2026-05-24 12:36)
    Predicted:     pH=-1.0, Cl=-1.0
    Warnings:      GT: –  |  AI: analysis failed or refused
    Scores:        pH=0%  Cl=0%  =>  Total: 0%

  20260525_094358.jpg
    Ground truth:  pH=-1.0, Cl=-1.0  (2026-05-25 09:43)
    Predicted:     pH=-1.0, Cl=-1.0
    Warnings:      GT: no reference scale  |  AI: analysis failed or refused
    Scores:        pH=100%  Cl=100%  =>  Total: 100%

  20260525_094404.jpg
    Ground truth:  pH=6.4, Cl=0.6  (2026-05-25 09:44)
    Predicted:     pH=-1.0, Cl=-1.0
    Warnings:      GT: –  |  AI: analysis failed or refused
    Scores:        pH=0%  Cl=0%  =>  Total: 0%

  ────────────────────────────────────────
  Scores:   avg=20.0%  min=0%  max=100%
  Passed (≥50%):      2/10

Done.
```


## Anthropic: Claude Sonnet 4.6

```
OpenRouter SDK version: 0.9.1
Model: anthropic/claude-sonnet-4.6
Images: 10

  Analyzing 20260524_115452.jpg (4080×1884 → 2048×946 px, 154 KB) ... OK
  Analyzing 20260525_094358.jpg (4080×1884 → 2048×946 px, 254 KB) ... OK
  Analyzing 20260524_115516.jpg (4080×1884 → 2048×946 px, 216 KB) ... OK
  Analyzing 20260524_123629.jpg (4080×1884 → 2048×946 px, 294 KB) ... OK
  Analyzing 20260524_115506.jpg (4080×1884 → 2048×946 px, 275 KB) ... OK
  Analyzing 20260524_123636.jpg (4080×1884 → 2048×946 px, 263 KB) ... OK
  Analyzing 20260524_123656.jpg (4080×1884 → 2048×946 px, 208 KB) ... OK
  Analyzing 20260524_123639.jpg (4080×1884 → 2048×946 px, 247 KB) ... OK
  Analyzing 20260525_094358.jpg (4080×1884 → 2048×946 px, 254 KB) ... OK
  Analyzing 20260525_094404.jpg (4080×1884 → 2048×946 px, 206 KB) ... OK

============================================================
BENCHMARK RESULTS
============================================================

  20260524_115452.jpg
    Ground truth:  pH=7.0, Cl=0.0  (2026-05-24 11:54)
    Predicted:     pH=7.2, Cl=0.5
    Warnings:      GT: –  |  AI: –
    Scores:        pH=80%  Cl=50%  =>  Total: 65%

  20260525_094358.jpg
    Ground truth:  pH=-1.0, Cl=-1.0  (2026-05-25 09:43)
    Predicted:     pH=7.4, Cl=0.5
    Warnings:      GT: no reference scale  |  AI: No color reference scale visible in the image, making accurate calibration difficult
    Scores:        pH=0%  Cl=0%  =>  Total: 0%

  20260524_115516.jpg
    Ground truth:  pH=6.8, Cl=0.2  (2026-05-24 11:55)
    Predicted:     pH=7.2, Cl=1.5
    Warnings:      GT: –  |  AI: –
    Scores:        pH=60%  Cl=0%  =>  Total: 30%

  20260524_123629.jpg
    Ground truth:  pH=7.2, Cl=0.4  (2026-05-24 12:36)
    Predicted:     pH=7.2, Cl=1.0
    Warnings:      GT: –  |  AI: –
    Scores:        pH=100%  Cl=40%  =>  Total: 70%

  20260524_115506.jpg
    Ground truth:  pH=7.0, Cl=0.0  (2026-05-24 11:55)
    Predicted:     pH=7.2, Cl=0.5
    Warnings:      GT: –  |  AI: –
    Scores:        pH=80%  Cl=50%  =>  Total: 65%

  20260524_123636.jpg
    Ground truth:  pH=7.2, Cl=0.4  (2026-05-24 12:36)
    Predicted:     pH=7.2, Cl=0.5
    Warnings:      GT: –  |  AI: –
    Scores:        pH=100%  Cl=90%  =>  Total: 95%

  20260524_123656.jpg
    Ground truth:  pH=7.3, Cl=0.6  (2026-05-24 12:36)
    Predicted:     pH=7.2, Cl=0.5
    Warnings:      GT: –  |  AI: –
    Scores:        pH=90%  Cl=90%  =>  Total: 90%

  20260524_123639.jpg
    Ground truth:  pH=6.8, Cl=0.5  (2026-05-24 12:36)
    Predicted:     pH=7.2, Cl=0.5
    Warnings:      GT: –  |  AI: –
    Scores:        pH=60%  Cl=100%  =>  Total: 80%

  20260525_094358.jpg
    Ground truth:  pH=-1.0, Cl=-1.0  (2026-05-25 09:43)
    Predicted:     pH=7.4, Cl=1.5
    Warnings:      GT: no reference scale  |  AI: No color reference chart visible in image; values estimated from pad colors alone, which reduces confidence
    Scores:        pH=0%  Cl=0%  =>  Total: 0%

  20260525_094404.jpg
    Ground truth:  pH=6.4, Cl=0.6  (2026-05-25 09:44)
    Predicted:     pH=7.2, Cl=3.0
    Warnings:      GT: –  |  AI: –
    Scores:        pH=20%  Cl=0%  =>  Total: 10%

  ────────────────────────────────────────
  Scores:   avg=50.5%  min=0%  max=95%
  Passed (≥50%):      6/10

============================================================
COST SUMMARY
============================================================
  gen-1779907041-0AcuYej8rE0TFXmyHwd4: $0.006816
  gen-1779907047-Dh4FvwuuvH1zxI7miz6Z: $0.007026
  gen-1779907052-8Jd0ZcLWGGG0fRXtdKy5: $0.006741
  gen-1779907056-ZdigA0ASMoW8ZIrSPO8X: $0.006741
  gen-1779907059-7stgyeLptjxpeW3SCzut: $0.006816
  gen-1779907063-Um7r4Y6aO667YWJJvbeT: $0.006741
  gen-1779907069-WXjJMFDsf7YKprg9XaXb: $0.006741
  gen-1779907072-OrCM1PHcraal2IhojQxb: $0.006741
  gen-1779907076-7SSsSXXGue54BDKsmzX9: $0.007176
  gen-1779907080-vpxzvcBZtBq8yprqbrUs: $0.006816
  ────────────────────────────────────────
  Total: $0.068355

Done.
```


## Google: Gemini 3 Flash Preview

```
OpenRouter SDK version: 0.9.1
Model: google/gemini-3-flash-preview
Images: 10

  Analyzing 20260524_115452.jpg (4080×1884 → 2048×946 px, 154 KB) ... OK
  Analyzing 20260525_094358.jpg (4080×1884 → 2048×946 px, 254 KB) ... OK
  Analyzing 20260524_115516.jpg (4080×1884 → 2048×946 px, 216 KB) ... OK
  Analyzing 20260524_123629.jpg (4080×1884 → 2048×946 px, 294 KB) ... OK
  Analyzing 20260524_115506.jpg (4080×1884 → 2048×946 px, 275 KB) ... OK
  Analyzing 20260524_123636.jpg (4080×1884 → 2048×946 px, 263 KB) ... OK
  Analyzing 20260524_123656.jpg (4080×1884 → 2048×946 px, 208 KB) ... OK
  Analyzing 20260524_123639.jpg (4080×1884 → 2048×946 px, 247 KB) ... OK
  Analyzing 20260525_094358.jpg (4080×1884 → 2048×946 px, 254 KB) ... OK
  Analyzing 20260525_094404.jpg (4080×1884 → 2048×946 px, 206 KB) ... OK

============================================================
BENCHMARK RESULTS
============================================================

  20260524_115452.jpg
    Ground truth:  pH=7.0, Cl=0.0  (2026-05-24 11:54)
    Predicted:     pH=6.5, Cl=0.0
    Warnings:      GT: –  |  AI: –
    Scores:        pH=50%  Cl=100%  =>  Total: 75%

  20260525_094358.jpg
    Ground truth:  pH=-1.0, Cl=-1.0  (2026-05-25 09:43)
    Predicted:     pH=-1.0, Cl=-1.0
    Warnings:      GT: no reference scale  |  AI: Missing reference color scale in image
    Scores:        pH=100%  Cl=100%  =>  Total: 100%

  20260524_115516.jpg
    Ground truth:  pH=6.8, Cl=0.2  (2026-05-24 11:55)
    Predicted:     pH=6.7, Cl=0.0
    Warnings:      GT: –  |  AI: –
    Scores:        pH=90%  Cl=80%  =>  Total: 85%

  20260524_123629.jpg
    Ground truth:  pH=7.2, Cl=0.4  (2026-05-24 12:36)
    Predicted:     pH=7.3, Cl=0.3
    Warnings:      GT: –  |  AI: –
    Scores:        pH=90%  Cl=90%  =>  Total: 90%

  20260524_115506.jpg
    Ground truth:  pH=7.0, Cl=0.0  (2026-05-24 11:55)
    Predicted:     pH=6.7, Cl=0.0
    Warnings:      GT: –  |  AI: –
    Scores:        pH=70%  Cl=100%  =>  Total: 85%

  20260524_123636.jpg
    Ground truth:  pH=7.2, Cl=0.4  (2026-05-24 12:36)
    Predicted:     pH=7.1, Cl=1.5
    Warnings:      GT: –  |  AI: –
    Scores:        pH=90%  Cl=0%  =>  Total: 45%

  20260524_123656.jpg
    Ground truth:  pH=7.3, Cl=0.6  (2026-05-24 12:36)
    Predicted:     pH=7.4, Cl=0.3
    Warnings:      GT: –  |  AI: –
    Scores:        pH=90%  Cl=70%  =>  Total: 80%

  20260524_123639.jpg
    Ground truth:  pH=6.8, Cl=0.5  (2026-05-24 12:36)
    Predicted:     pH=6.9, Cl=0.3
    Warnings:      GT: –  |  AI: –
    Scores:        pH=90%  Cl=80%  =>  Total: 85%

  20260525_094358.jpg
    Ground truth:  pH=-1.0, Cl=-1.0  (2026-05-25 09:43)
    Predicted:     pH=-1.0, Cl=-1.0
    Warnings:      GT: no reference scale  |  AI: Missing reference color scale in image.
    Scores:        pH=100%  Cl=100%  =>  Total: 100%

  20260525_094404.jpg
    Ground truth:  pH=6.4, Cl=0.6  (2026-05-25 09:44)
    Predicted:     pH=7.0, Cl=0.3
    Warnings:      GT: –  |  AI: –
    Scores:        pH=40%  Cl=70%  =>  Total: 55%

  ────────────────────────────────────────
  Scores:   avg=80.0%  min=45%  max=100%
  Passed (≥50%):      9/10

============================================================
COST SUMMARY
============================================================
  gen-1779907104-pcwFVyrlHT3bRrLT5cUv: $0.000923
  gen-1779907107-3p7Q1hvD9uEcTLpe7C3V: $0.000872
  gen-1779907110-swDdM7XuMxq5LbwDieqh: $0.000869
  gen-1779907113-0uxbhMZuQSloJWRrwioA: $0.000920
  gen-1779907117-FFw3sF0KYFdXGzxo9d2c: $0.000887
  gen-1779907120-wTf3XuMg84EH1MOHakfc: $0.000863
  gen-1779907123-z6PNhRevwk1FI7KzDO42: $0.000887
  gen-1779907126-hm3hENA52bnaaEMNaF6k: $0.000887
  gen-1779907129-gIH9oUvZotvJxSkRG2X8: $0.000905
  gen-1779907132-s3IkaHAKaPhclYm4jWJb: $0.000866
  ────────────────────────────────────────
  Total: $0.008879

Done.
```


## Google: Gemini 2.5 Pro

```
OpenRouter SDK version: 0.9.1
Model: google/gemini-2.5-pro
Images: 10

  Analyzing 20260524_115452.jpg (4080×1884 → 2048×946 px, 154 KB) ... OK
  Analyzing 20260525_094358.jpg (4080×1884 → 2048×946 px, 254 KB) ... FAILED → -1
  Analyzing 20260524_115516.jpg (4080×1884 → 2048×946 px, 216 KB) ... OK
  Analyzing 20260524_123629.jpg (4080×1884 → 2048×946 px, 294 KB) ... OK
  Analyzing 20260524_115506.jpg (4080×1884 → 2048×946 px, 275 KB) ... OK
  Analyzing 20260524_123636.jpg (4080×1884 → 2048×946 px, 263 KB) ... OK
  Analyzing 20260524_123656.jpg (4080×1884 → 2048×946 px, 208 KB) ... OK
  Analyzing 20260524_123639.jpg (4080×1884 → 2048×946 px, 247 KB) ... OK
  Analyzing 20260525_094358.jpg (4080×1884 → 2048×946 px, 254 KB) ... FAILED → -1
  Analyzing 20260525_094404.jpg (4080×1884 → 2048×946 px, 206 KB) ... OK

============================================================
BENCHMARK RESULTS
============================================================

  20260524_115452.jpg
    Ground truth:  pH=7.0, Cl=0.0  (2026-05-24 11:54)
    Predicted:     pH=-1.0, Cl=0.0
    Warnings:      GT: –  |  AI: –
    Scores:        pH=0%  Cl=100%  =>  Total: 50%

  20260525_094358.jpg
    Ground truth:  pH=-1.0, Cl=-1.0  (2026-05-25 09:43)
    Predicted:     pH=-1.0, Cl=-1.0
    Warnings:      GT: no reference scale  |  AI: analysis failed or refused
    Scores:        pH=100%  Cl=100%  =>  Total: 100%

  20260524_115516.jpg
    Ground truth:  pH=6.8, Cl=0.2  (2026-05-24 11:55)
    Predicted:     pH=7.1, Cl=0.1
    Warnings:      GT: –  |  AI: –
    Scores:        pH=70%  Cl=90%  =>  Total: 80%

  20260524_123629.jpg
    Ground truth:  pH=7.2, Cl=0.4  (2026-05-24 12:36)
    Predicted:     pH=7.2, Cl=0.2
    Warnings:      GT: –  |  AI: –
    Scores:        pH=100%  Cl=80%  =>  Total: 90%

  20260524_115506.jpg
    Ground truth:  pH=7.0, Cl=0.0  (2026-05-24 11:55)
    Predicted:     pH=7.2, Cl=0.0
    Warnings:      GT: –  |  AI: –
    Scores:        pH=80%  Cl=100%  =>  Total: 90%

  20260524_123636.jpg
    Ground truth:  pH=7.2, Cl=0.4  (2026-05-24 12:36)
    Predicted:     pH=7.2, Cl=0.0
    Warnings:      GT: –  |  AI: –
    Scores:        pH=100%  Cl=60%  =>  Total: 80%

  20260524_123656.jpg
    Ground truth:  pH=7.3, Cl=0.6  (2026-05-24 12:36)
    Predicted:     pH=7.6, Cl=0.1
    Warnings:      GT: –  |  AI: –
    Scores:        pH=70%  Cl=50%  =>  Total: 60%

  20260524_123639.jpg
    Ground truth:  pH=6.8, Cl=0.5  (2026-05-24 12:36)
    Predicted:     pH=7.2, Cl=0.3
    Warnings:      GT: –  |  AI: –
    Scores:        pH=60%  Cl=80%  =>  Total: 70%

  20260525_094358.jpg
    Ground truth:  pH=-1.0, Cl=-1.0  (2026-05-25 09:43)
    Predicted:     pH=-1.0, Cl=-1.0
    Warnings:      GT: no reference scale  |  AI: analysis failed or refused
    Scores:        pH=100%  Cl=100%  =>  Total: 100%

  20260525_094404.jpg
    Ground truth:  pH=6.4, Cl=0.6  (2026-05-25 09:44)
    Predicted:     pH=7.2, Cl=0.8
    Warnings:      GT: –  |  AI: –
    Scores:        pH=20%  Cl=58%  =>  Total: 39%

  ────────────────────────────────────────
  Scores:   avg=75.9%  min=39%  max=100%
  Passed (≥50%):      9/10

============================================================
COST SUMMARY
============================================================
  gen-1779907145-TyQkmGB9jeIfzq1VtV14: $0.017034
  gen-1779907176-W5b29X6u6oaNwZZMvYQq: $0.015114
  gen-1779907190-CIQoJf18d3sG5VadvwBK: $0.024334
  gen-1779907215-DIGCtD6LxKPODkz2pouv: $0.010884
  gen-1779907226-l5UaNGPSQZkE20rLWJeZ: $0.022314
  gen-1779907246-S6zk78nJqLjdi2oJfOoJ: $0.015074
  gen-1779907261-I2jkPtI5ce2i7A9o07sV: $0.015684
  gen-1779907282-wFxCeYdZKkQ959I0SCBQ: $0.014014
  ────────────────────────────────────────
  Total: $0.134450

Done.
```


## OpenAI: o3

```
OpenRouter SDK version: 0.9.1
Model: openai/o3
Images: 10

  Analyzing 20260524_115452.jpg (4080×1884 → 2048×946 px, 154 KB) ... FAILED → -1
  Analyzing 20260525_094358.jpg (4080×1884 → 2048×946 px, 254 KB) ... FAILED → -1
  Analyzing 20260524_115516.jpg (4080×1884 → 2048×946 px, 216 KB) ... FAILED → -1
  Analyzing 20260524_123629.jpg (4080×1884 → 2048×946 px, 294 KB) ... FAILED → -1
  Analyzing 20260524_115506.jpg (4080×1884 → 2048×946 px, 275 KB) ... FAILED → -1
  Analyzing 20260524_123636.jpg (4080×1884 → 2048×946 px, 263 KB) ... FAILED → -1
  Analyzing 20260524_123656.jpg (4080×1884 → 2048×946 px, 208 KB) ... FAILED → -1
  Analyzing 20260524_123639.jpg (4080×1884 → 2048×946 px, 247 KB) ... FAILED → -1
  Analyzing 20260525_094358.jpg (4080×1884 → 2048×946 px, 254 KB) ... FAILED → -1
  Analyzing 20260525_094404.jpg (4080×1884 → 2048×946 px, 206 KB) ... FAILED → -1

============================================================
BENCHMARK RESULTS
============================================================

  20260524_115452.jpg
    Ground truth:  pH=7.0, Cl=0.0  (2026-05-24 11:54)
    Predicted:     pH=-1.0, Cl=-1.0
    Warnings:      GT: –  |  AI: analysis failed or refused
    Scores:        pH=0%  Cl=0%  =>  Total: 0%

  20260525_094358.jpg
    Ground truth:  pH=-1.0, Cl=-1.0  (2026-05-25 09:43)
    Predicted:     pH=-1.0, Cl=-1.0
    Warnings:      GT: no reference scale  |  AI: analysis failed or refused
    Scores:        pH=100%  Cl=100%  =>  Total: 100%

  20260524_115516.jpg
    Ground truth:  pH=6.8, Cl=0.2  (2026-05-24 11:55)
    Predicted:     pH=-1.0, Cl=-1.0
    Warnings:      GT: –  |  AI: analysis failed or refused
    Scores:        pH=0%  Cl=0%  =>  Total: 0%

  20260524_123629.jpg
    Ground truth:  pH=7.2, Cl=0.4  (2026-05-24 12:36)
    Predicted:     pH=-1.0, Cl=-1.0
    Warnings:      GT: –  |  AI: analysis failed or refused
    Scores:        pH=0%  Cl=0%  =>  Total: 0%

  20260524_115506.jpg
    Ground truth:  pH=7.0, Cl=0.0  (2026-05-24 11:55)
    Predicted:     pH=-1.0, Cl=-1.0
    Warnings:      GT: –  |  AI: analysis failed or refused
    Scores:        pH=0%  Cl=0%  =>  Total: 0%

  20260524_123636.jpg
    Ground truth:  pH=7.2, Cl=0.4  (2026-05-24 12:36)
    Predicted:     pH=-1.0, Cl=-1.0
    Warnings:      GT: –  |  AI: analysis failed or refused
    Scores:        pH=0%  Cl=0%  =>  Total: 0%

  20260524_123656.jpg
    Ground truth:  pH=7.3, Cl=0.6  (2026-05-24 12:36)
    Predicted:     pH=-1.0, Cl=-1.0
    Warnings:      GT: –  |  AI: analysis failed or refused
    Scores:        pH=0%  Cl=0%  =>  Total: 0%

  20260524_123639.jpg
    Ground truth:  pH=6.8, Cl=0.5  (2026-05-24 12:36)
    Predicted:     pH=-1.0, Cl=-1.0
    Warnings:      GT: –  |  AI: analysis failed or refused
    Scores:        pH=0%  Cl=0%  =>  Total: 0%

  20260525_094358.jpg
    Ground truth:  pH=-1.0, Cl=-1.0  (2026-05-25 09:43)
    Predicted:     pH=-1.0, Cl=-1.0
    Warnings:      GT: no reference scale  |  AI: analysis failed or refused
    Scores:        pH=100%  Cl=100%  =>  Total: 100%

  20260525_094404.jpg
    Ground truth:  pH=6.4, Cl=0.6  (2026-05-25 09:44)
    Predicted:     pH=-1.0, Cl=-1.0
    Warnings:      GT: –  |  AI: analysis failed or refused
    Scores:        pH=0%  Cl=0%  =>  Total: 0%

  ────────────────────────────────────────
  Scores:   avg=20.0%  min=0%  max=100%
  Passed (≥50%):      2/10

Done.
```


## OpenAI: GPT-4.1

```
OpenRouter SDK version: 0.9.1
Model: openai/gpt-4.1
Images: 10

  Analyzing 20260524_115452.jpg (4080×1884 → 2048×946 px, 154 KB) ... FAILED → -1
  Analyzing 20260525_094358.jpg (4080×1884 → 2048×946 px, 254 KB) ... FAILED → -1
  Analyzing 20260524_115516.jpg (4080×1884 → 2048×946 px, 216 KB) ... FAILED → -1
  Analyzing 20260524_123629.jpg (4080×1884 → 2048×946 px, 294 KB) ... FAILED → -1
  Analyzing 20260524_115506.jpg (4080×1884 → 2048×946 px, 275 KB) ... FAILED → -1
  Analyzing 20260524_123636.jpg (4080×1884 → 2048×946 px, 263 KB) ... FAILED → -1
  Analyzing 20260524_123656.jpg (4080×1884 → 2048×946 px, 208 KB) ... FAILED → -1
  Analyzing 20260524_123639.jpg (4080×1884 → 2048×946 px, 247 KB) ... FAILED → -1
  Analyzing 20260525_094358.jpg (4080×1884 → 2048×946 px, 254 KB) ... FAILED → -1
  Analyzing 20260525_094404.jpg (4080×1884 → 2048×946 px, 206 KB) ... FAILED → -1

============================================================
BENCHMARK RESULTS
============================================================

  20260524_115452.jpg
    Ground truth:  pH=7.0, Cl=0.0  (2026-05-24 11:54)
    Predicted:     pH=-1.0, Cl=-1.0
    Warnings:      GT: –  |  AI: analysis failed or refused
    Scores:        pH=0%  Cl=0%  =>  Total: 0%

  20260525_094358.jpg
    Ground truth:  pH=-1.0, Cl=-1.0  (2026-05-25 09:43)
    Predicted:     pH=-1.0, Cl=-1.0
    Warnings:      GT: no reference scale  |  AI: analysis failed or refused
    Scores:        pH=100%  Cl=100%  =>  Total: 100%

  20260524_115516.jpg
    Ground truth:  pH=6.8, Cl=0.2  (2026-05-24 11:55)
    Predicted:     pH=-1.0, Cl=-1.0
    Warnings:      GT: –  |  AI: analysis failed or refused
    Scores:        pH=0%  Cl=0%  =>  Total: 0%

  20260524_123629.jpg
    Ground truth:  pH=7.2, Cl=0.4  (2026-05-24 12:36)
    Predicted:     pH=-1.0, Cl=-1.0
    Warnings:      GT: –  |  AI: analysis failed or refused
    Scores:        pH=0%  Cl=0%  =>  Total: 0%

  20260524_115506.jpg
    Ground truth:  pH=7.0, Cl=0.0  (2026-05-24 11:55)
    Predicted:     pH=-1.0, Cl=-1.0
    Warnings:      GT: –  |  AI: analysis failed or refused
    Scores:        pH=0%  Cl=0%  =>  Total: 0%

  20260524_123636.jpg
    Ground truth:  pH=7.2, Cl=0.4  (2026-05-24 12:36)
    Predicted:     pH=-1.0, Cl=-1.0
    Warnings:      GT: –  |  AI: analysis failed or refused
    Scores:        pH=0%  Cl=0%  =>  Total: 0%

  20260524_123656.jpg
    Ground truth:  pH=7.3, Cl=0.6  (2026-05-24 12:36)
    Predicted:     pH=-1.0, Cl=-1.0
    Warnings:      GT: –  |  AI: analysis failed or refused
    Scores:        pH=0%  Cl=0%  =>  Total: 0%

  20260524_123639.jpg
    Ground truth:  pH=6.8, Cl=0.5  (2026-05-24 12:36)
    Predicted:     pH=-1.0, Cl=-1.0
    Warnings:      GT: –  |  AI: analysis failed or refused
    Scores:        pH=0%  Cl=0%  =>  Total: 0%

  20260525_094358.jpg
    Ground truth:  pH=-1.0, Cl=-1.0  (2026-05-25 09:43)
    Predicted:     pH=-1.0, Cl=-1.0
    Warnings:      GT: no reference scale  |  AI: analysis failed or refused
    Scores:        pH=100%  Cl=100%  =>  Total: 100%

  20260525_094404.jpg
    Ground truth:  pH=6.4, Cl=0.6  (2026-05-25 09:44)
    Predicted:     pH=-1.0, Cl=-1.0
    Warnings:      GT: –  |  AI: analysis failed or refused
    Scores:        pH=0%  Cl=0%  =>  Total: 0%

  ────────────────────────────────────────
  Scores:   avg=20.0%  min=0%  max=100%
  Passed (≥50%):      2/10

Done.
```


## Qwen: Qwen3 VL 235B A22B Instruct

```
OpenRouter SDK version: 0.9.1
Model: qwen/qwen3-vl-235b-a22b-instruct
Images: 10

  Analyzing 20260524_115452.jpg (4080×1884 → 2048×946 px, 154 KB) ... OK
  Analyzing 20260525_094358.jpg (4080×1884 → 2048×946 px, 254 KB) ... OK
  Analyzing 20260524_115516.jpg (4080×1884 → 2048×946 px, 216 KB) ... OK
  Analyzing 20260524_123629.jpg (4080×1884 → 2048×946 px, 294 KB) ... OK
  Analyzing 20260524_115506.jpg (4080×1884 → 2048×946 px, 275 KB) ... OK
  Analyzing 20260524_123636.jpg (4080×1884 → 2048×946 px, 263 KB) ... OK
  Analyzing 20260524_123656.jpg (4080×1884 → 2048×946 px, 208 KB) ... OK
  Analyzing 20260524_123639.jpg (4080×1884 → 2048×946 px, 247 KB) ... OK
  Analyzing 20260525_094358.jpg (4080×1884 → 2048×946 px, 254 KB) ... OK
  Analyzing 20260525_094404.jpg (4080×1884 → 2048×946 px, 206 KB) ... OK

============================================================
BENCHMARK RESULTS
============================================================

  20260524_115452.jpg
    Ground truth:  pH=7.0, Cl=0.0  (2026-05-24 11:54)
    Predicted:     pH=7.5, Cl=3.5
    Warnings:      GT: –  |  AI: –
    Scores:        pH=50%  Cl=0%  =>  Total: 25%

  20260525_094358.jpg
    Ground truth:  pH=-1.0, Cl=-1.0  (2026-05-25 09:43)
    Predicted:     pH=-1.0, Cl=-1.0
    Warnings:      GT: no reference scale  |  AI: Test strip is out of focus and too small to reliably match pad colors to reference scale.
    Scores:        pH=100%  Cl=100%  =>  Total: 100%

  20260524_115516.jpg
    Ground truth:  pH=6.8, Cl=0.2  (2026-05-24 11:55)
    Predicted:     pH=7.0, Cl=0.5
    Warnings:      GT: –  |  AI: –
    Scores:        pH=80%  Cl=70%  =>  Total: 75%

  20260524_123629.jpg
    Ground truth:  pH=7.2, Cl=0.4  (2026-05-24 12:36)
    Predicted:     pH=7.6, Cl=1.0
    Warnings:      GT: –  |  AI: –
    Scores:        pH=60%  Cl=40%  =>  Total: 50%

  20260524_115506.jpg
    Ground truth:  pH=7.0, Cl=0.0  (2026-05-24 11:55)
    Predicted:     pH=7.0, Cl=0.5
    Warnings:      GT: –  |  AI: –
    Scores:        pH=100%  Cl=50%  =>  Total: 75%

  20260524_123636.jpg
    Ground truth:  pH=7.2, Cl=0.4  (2026-05-24 12:36)
    Predicted:     pH=-1.0, Cl=-1.0
    Warnings:      GT: –  |  AI: Test strip is upside down relative to the reference scale, making pad alignment unreliable., Image is blurry and poorly lit, preventing accurate color matching for pH and chlorine pads.
    Scores:        pH=0%  Cl=0%  =>  Total: 0%  ⚠ mismatch (-25%)

  20260524_123656.jpg
    Ground truth:  pH=7.3, Cl=0.6  (2026-05-24 12:36)
    Predicted:     pH=7.4, Cl=1.0
    Warnings:      GT: –  |  AI: –
    Scores:        pH=90%  Cl=26%  =>  Total: 58%

  20260524_123639.jpg
    Ground truth:  pH=6.8, Cl=0.5  (2026-05-24 12:36)
    Predicted:     pH=7.0, Cl=0.5
    Warnings:      GT: –  |  AI: –
    Scores:        pH=80%  Cl=100%  =>  Total: 90%

  20260525_094358.jpg
    Ground truth:  pH=-1.0, Cl=-1.0  (2026-05-25 09:43)
    Predicted:     pH=-1.0, Cl=-1.0
    Warnings:      GT: no reference scale  |  AI: Test strip is severely blurred and out of focus, making pad colors unreadable., Image orientation is rotated 90 degrees, complicating pad identification., Insufficient lighting and low contrast prevent reliable color matching to reference scale.
    Scores:        pH=100%  Cl=100%  =>  Total: 100%

  20260525_094404.jpg
    Ground truth:  pH=6.4, Cl=0.6  (2026-05-25 09:44)
    Predicted:     pH=-1.0, Cl=-1.0
    Warnings:      GT: –  |  AI: Severe blur and poor lighting make pad colors indistinct and unreliable for matching against reference scale.
    Scores:        pH=0%  Cl=0%  =>  Total: 0%  ⚠ mismatch (-25%)

  ────────────────────────────────────────
  Scores:   avg=57.3%  min=0%  max=100%
  Passed (≥50%):      7/10

============================================================
COST SUMMARY
============================================================
  gen-1779907336-kOetVNspPK4hA90pEUKm: $0.000532
  gen-1779907339-CfUuLdbJhh8Jz0geAkc0: $0.000746
  gen-1779907343-aPujfk7J0ggQ5Hf921ie: $0.000614
  gen-1779907346-kuFKpUiSiH21QYAFr3sS: $0.000551
  gen-1779907349-ruwegr4vPNWIGR6GNJh1: $0.000613
  gen-1779907351-L1dQ84mb5z2ANMpTCiPB: $0.000586
  gen-1779907354-7RCgdAYuOBO7iGhJ2Qs9: $0.000549
  gen-1779907358-tGYoqyHdbjZPvFwYDdyA: $0.000534
  gen-1779907361-vUUL68DtVF7FZWY58S6x: $0.000625
  gen-1779907365-TLI7fctpIq037GjA4Ioc: $0.000540
  ────────────────────────────────────────
  Total: $0.005892

Done.
```


## Google: Gemini 2.5 Flash

```
OpenRouter SDK version: 0.9.1
Model: google/gemini-2.5-flash
Images: 10

  Analyzing 20260524_115452.jpg (4080×1884 → 2048×946 px, 154 KB) ... OK
  Analyzing 20260525_094358.jpg (4080×1884 → 2048×946 px, 254 KB) ... OK
  Analyzing 20260524_115516.jpg (4080×1884 → 2048×946 px, 216 KB) ... OK
  Analyzing 20260524_123629.jpg (4080×1884 → 2048×946 px, 294 KB) ... OK
  Analyzing 20260524_115506.jpg (4080×1884 → 2048×946 px, 275 KB) ... OK
  Analyzing 20260524_123636.jpg (4080×1884 → 2048×946 px, 263 KB) ... OK
  Analyzing 20260524_123656.jpg (4080×1884 → 2048×946 px, 208 KB) ... OK
  Analyzing 20260524_123639.jpg (4080×1884 → 2048×946 px, 247 KB) ... OK
  Analyzing 20260525_094358.jpg (4080×1884 → 2048×946 px, 254 KB) ... OK
  Analyzing 20260525_094404.jpg (4080×1884 → 2048×946 px, 206 KB) ... OK

============================================================
BENCHMARK RESULTS
============================================================

  20260524_115452.jpg
    Ground truth:  pH=7.0, Cl=0.0  (2026-05-24 11:54)
    Predicted:     pH=7.0, Cl=0.3
    Warnings:      GT: –  |  AI: –
    Scores:        pH=100%  Cl=70%  =>  Total: 85%

  20260525_094358.jpg
    Ground truth:  pH=-1.0, Cl=-1.0  (2026-05-25 09:43)
    Predicted:     pH=7.0, Cl=-1.0
    Warnings:      GT: no reference scale  |  AI: The chlorine pad is unreadable due to blur and poor lighting.
    Scores:        pH=0%  Cl=100%  =>  Total: 50%

  20260524_115516.jpg
    Ground truth:  pH=6.8, Cl=0.2  (2026-05-24 11:55)
    Predicted:     pH=6.8, Cl=3.0
    Warnings:      GT: –  |  AI: –
    Scores:        pH=100%  Cl=0%  =>  Total: 50%

  20260524_123629.jpg
    Ground truth:  pH=7.2, Cl=0.4  (2026-05-24 12:36)
    Predicted:     pH=7.4, Cl=0.5
    Warnings:      GT: –  |  AI: –
    Scores:        pH=80%  Cl=90%  =>  Total: 85%

  20260524_115506.jpg
    Ground truth:  pH=7.0, Cl=0.0  (2026-05-24 11:55)
    Predicted:     pH=7.4, Cl=1.0
    Warnings:      GT: –  |  AI: –
    Scores:        pH=60%  Cl=0%  =>  Total: 30%

  20260524_123636.jpg
    Ground truth:  pH=7.2, Cl=0.4  (2026-05-24 12:36)
    Predicted:     pH=7.4, Cl=0.5
    Warnings:      GT: –  |  AI: –
    Scores:        pH=80%  Cl=90%  =>  Total: 85%

  20260524_123656.jpg
    Ground truth:  pH=7.3, Cl=0.6  (2026-05-24 12:36)
    Predicted:     pH=7.4, Cl=3.0
    Warnings:      GT: –  |  AI: –
    Scores:        pH=90%  Cl=0%  =>  Total: 45%

  20260524_123639.jpg
    Ground truth:  pH=6.8, Cl=0.5  (2026-05-24 12:36)
    Predicted:     pH=7.4, Cl=-1.0
    Warnings:      GT: –  |  AI: –
    Scores:        pH=40%  Cl=0%  =>  Total: 20%

  20260525_094358.jpg
    Ground truth:  pH=-1.0, Cl=-1.0  (2026-05-25 09:43)
    Predicted:     pH=7.2, Cl=3.0
    Warnings:      GT: no reference scale  |  AI: –
    Scores:        pH=0%  Cl=0%  =>  Total: 0%  ⚠ mismatch (-25%)

  20260525_094404.jpg
    Ground truth:  pH=6.4, Cl=0.6  (2026-05-25 09:44)
    Predicted:     pH=7.4, Cl=0.5
    Warnings:      GT: –  |  AI: –
    Scores:        pH=0%  Cl=90%  =>  Total: 45%

  ────────────────────────────────────────
  Scores:   avg=49.5%  min=0%  max=85%
  Passed (≥50%):      5/10

============================================================
COST SUMMARY
============================================================
  gen-1779907388-GvnRD98923fmhAxlpT4z: $0.000878
  gen-1779907390-YLXPtn9D1Z1LUOsd7x2W: $0.000941
  gen-1779907392-WeWksgeuvH748QI7csK7: $0.000898
  gen-1779907395-RKhszg8XbR4d15RJmbpf: $0.000896
  gen-1779907397-kBL0g8MZM2NmRZ5YgwmA: $0.000898
  gen-1779907399-PPCoAkWbaghlYFDyWI6I: $0.000896
  gen-1779907401-e8YbAxCx9MiqkQgQtpZA: $0.000876
  gen-1779907404-PSQOE0fBhwiwXD4IqVDq: $0.000893
  gen-1779907406-tI6v6RiHXt5VZTWtKSWH: $0.000896
  gen-1779907408-PTIc5XiJ8TWaxU68TZPp: $0.000896
  ────────────────────────────────────────
  Total: $0.008968

Done.
```


## Google: Gemma 4 31B

```
OpenRouter SDK version: 0.9.1
Model: google/gemma-4-31b-it
Images: 10

  Analyzing 20260524_115452.jpg (4080×1884 → 2048×946 px, 154 KB) ... OK
  Analyzing 20260525_094358.jpg (4080×1884 → 2048×946 px, 254 KB) ... FAILED → -1
  Analyzing 20260524_115516.jpg (4080×1884 → 2048×946 px, 216 KB) ... OK
  Analyzing 20260524_123629.jpg (4080×1884 → 2048×946 px, 294 KB) ... OK
  Analyzing 20260524_115506.jpg (4080×1884 → 2048×946 px, 275 KB) ... OK
  Analyzing 20260524_123636.jpg (4080×1884 → 2048×946 px, 263 KB) ... OK
  Analyzing 20260524_123656.jpg (4080×1884 → 2048×946 px, 208 KB) ... FAILED → -1
  Analyzing 20260524_123639.jpg (4080×1884 → 2048×946 px, 247 KB) ... FAILED → -1
  Analyzing 20260525_094358.jpg (4080×1884 → 2048×946 px, 254 KB) ... FAILED → -1
  Analyzing 20260525_094404.jpg (4080×1884 → 2048×946 px, 206 KB) ... OK

============================================================
BENCHMARK RESULTS
============================================================

  20260524_115452.jpg
    Ground truth:  pH=7.0, Cl=0.0  (2026-05-24 11:54)
    Predicted:     pH=7.5, Cl=0.0
    Warnings:      GT: –  |  AI: –
    Scores:        pH=50%  Cl=100%  =>  Total: 75%

  20260525_094358.jpg
    Ground truth:  pH=-1.0, Cl=-1.0  (2026-05-25 09:43)
    Predicted:     pH=-1.0, Cl=-1.0
    Warnings:      GT: no reference scale  |  AI: analysis failed or refused
    Scores:        pH=100%  Cl=100%  =>  Total: 100%

  20260524_115516.jpg
    Ground truth:  pH=6.8, Cl=0.2  (2026-05-24 11:55)
    Predicted:     pH=-1.0, Cl=-1.0
    Warnings:      GT: –  |  AI: No test strip is present in the image; only the reference bottle is shown.
    Scores:        pH=0%  Cl=0%  =>  Total: 0%  ⚠ mismatch (-25%)

  20260524_123629.jpg
    Ground truth:  pH=7.2, Cl=0.4  (2026-05-24 12:36)
    Predicted:     pH=7.4, Cl=1.5
    Warnings:      GT: –  |  AI: –
    Scores:        pH=80%  Cl=0%  =>  Total: 40%

  20260524_115506.jpg
    Ground truth:  pH=7.0, Cl=0.0  (2026-05-24 11:55)
    Predicted:     pH=7.4, Cl=0.5
    Warnings:      GT: –  |  AI: –
    Scores:        pH=60%  Cl=50%  =>  Total: 55%

  20260524_123636.jpg
    Ground truth:  pH=7.2, Cl=0.4  (2026-05-24 12:36)
    Predicted:     pH=7.6, Cl=0.5
    Warnings:      GT: –  |  AI: –
    Scores:        pH=60%  Cl=90%  =>  Total: 75%

  20260524_123656.jpg
    Ground truth:  pH=7.3, Cl=0.6  (2026-05-24 12:36)
    Predicted:     pH=-1.0, Cl=-1.0
    Warnings:      GT: –  |  AI: analysis failed or refused
    Scores:        pH=0%  Cl=0%  =>  Total: 0%

  20260524_123639.jpg
    Ground truth:  pH=6.8, Cl=0.5  (2026-05-24 12:36)
    Predicted:     pH=-1.0, Cl=-1.0
    Warnings:      GT: –  |  AI: analysis failed or refused
    Scores:        pH=0%  Cl=0%  =>  Total: 0%

  20260525_094358.jpg
    Ground truth:  pH=-1.0, Cl=-1.0  (2026-05-25 09:43)
    Predicted:     pH=-1.0, Cl=-1.0
    Warnings:      GT: no reference scale  |  AI: analysis failed or refused
    Scores:        pH=100%  Cl=100%  =>  Total: 100%

  20260525_094404.jpg
    Ground truth:  pH=6.4, Cl=0.6  (2026-05-25 09:44)
    Predicted:     pH=7.2, Cl=0.0
    Warnings:      GT: –  |  AI: –
    Scores:        pH=20%  Cl=40%  =>  Total: 30%

  ────────────────────────────────────────
  Scores:   avg=47.5%  min=0%  max=100%
  Passed (≥50%):      5/10

============================================================
COST SUMMARY
============================================================
  gen-1779907430-uw0rgag1eFHVwiHA4JRZ: $0.000102
  gen-1779907462-ic7CgcPBduGS0rz1pgYT: $0.000107
  gen-1779907502-2XiAoU5IPPgys02IdnwZ: $0.000102
  gen-1779907521-9qHY0DIMouWZt6Mtbt98: $0.000078
  gen-1779907544-FSI4GEsJ8O2YMD6zrZ9P: $0.000086
  gen-1779907647-StplMc693UnJNVpILpVj: $0.000102
  ────────────────────────────────────────
  Total: $0.000578

Done.
```


## Z.ai: GLM 5V Turbo

```
OpenRouter SDK version: 0.9.1
Model: z-ai/glm-5v-turbo
Images: 10

  Analyzing 20260524_115452.jpg (4080×1884 → 2048×946 px, 154 KB) ... FAILED → -1
  Analyzing 20260525_094358.jpg (4080×1884 → 2048×946 px, 254 KB) ... FAILED → -1
  Analyzing 20260524_115516.jpg (4080×1884 → 2048×946 px, 216 KB) ... FAILED → -1
  Analyzing 20260524_123629.jpg (4080×1884 → 2048×946 px, 294 KB) ... FAILED → -1
  Analyzing 20260524_115506.jpg (4080×1884 → 2048×946 px, 275 KB) ... FAILED → -1
  Analyzing 20260524_123636.jpg (4080×1884 → 2048×946 px, 263 KB) ... FAILED → -1
  Analyzing 20260524_123656.jpg (4080×1884 → 2048×946 px, 208 KB) ... FAILED → -1
  Analyzing 20260524_123639.jpg (4080×1884 → 2048×946 px, 247 KB) ... FAILED → -1
  Analyzing 20260525_094358.jpg (4080×1884 → 2048×946 px, 254 KB) ... FAILED → -1
  Analyzing 20260525_094404.jpg (4080×1884 → 2048×946 px, 206 KB) ... FAILED → -1

============================================================
BENCHMARK RESULTS
============================================================

  20260524_115452.jpg
    Ground truth:  pH=7.0, Cl=0.0  (2026-05-24 11:54)
    Predicted:     pH=-1.0, Cl=-1.0
    Warnings:      GT: –  |  AI: analysis failed or refused
    Scores:        pH=0%  Cl=0%  =>  Total: 0%

  20260525_094358.jpg
    Ground truth:  pH=-1.0, Cl=-1.0  (2026-05-25 09:43)
    Predicted:     pH=-1.0, Cl=-1.0
    Warnings:      GT: no reference scale  |  AI: analysis failed or refused
    Scores:        pH=100%  Cl=100%  =>  Total: 100%

  20260524_115516.jpg
    Ground truth:  pH=6.8, Cl=0.2  (2026-05-24 11:55)
    Predicted:     pH=-1.0, Cl=-1.0
    Warnings:      GT: –  |  AI: analysis failed or refused
    Scores:        pH=0%  Cl=0%  =>  Total: 0%

  20260524_123629.jpg
    Ground truth:  pH=7.2, Cl=0.4  (2026-05-24 12:36)
    Predicted:     pH=-1.0, Cl=-1.0
    Warnings:      GT: –  |  AI: analysis failed or refused
    Scores:        pH=0%  Cl=0%  =>  Total: 0%

  20260524_115506.jpg
    Ground truth:  pH=7.0, Cl=0.0  (2026-05-24 11:55)
    Predicted:     pH=-1.0, Cl=-1.0
    Warnings:      GT: –  |  AI: analysis failed or refused
    Scores:        pH=0%  Cl=0%  =>  Total: 0%

  20260524_123636.jpg
    Ground truth:  pH=7.2, Cl=0.4  (2026-05-24 12:36)
    Predicted:     pH=-1.0, Cl=-1.0
    Warnings:      GT: –  |  AI: analysis failed or refused
    Scores:        pH=0%  Cl=0%  =>  Total: 0%

  20260524_123656.jpg
    Ground truth:  pH=7.3, Cl=0.6  (2026-05-24 12:36)
    Predicted:     pH=-1.0, Cl=-1.0
    Warnings:      GT: –  |  AI: analysis failed or refused
    Scores:        pH=0%  Cl=0%  =>  Total: 0%

  20260524_123639.jpg
    Ground truth:  pH=6.8, Cl=0.5  (2026-05-24 12:36)
    Predicted:     pH=-1.0, Cl=-1.0
    Warnings:      GT: –  |  AI: analysis failed or refused
    Scores:        pH=0%  Cl=0%  =>  Total: 0%

  20260525_094358.jpg
    Ground truth:  pH=-1.0, Cl=-1.0  (2026-05-25 09:43)
    Predicted:     pH=-1.0, Cl=-1.0
    Warnings:      GT: no reference scale  |  AI: analysis failed or refused
    Scores:        pH=100%  Cl=100%  =>  Total: 100%

  20260525_094404.jpg
    Ground truth:  pH=6.4, Cl=0.6  (2026-05-25 09:44)
    Predicted:     pH=-1.0, Cl=-1.0
    Warnings:      GT: –  |  AI: analysis failed or refused
    Scores:        pH=0%  Cl=0%  =>  Total: 0%

  ────────────────────────────────────────
  Scores:   avg=20.0%  min=0%  max=100%
  Passed (≥50%):      2/10

Done.
```


## Meta: Llama 4 Maverick

```
OpenRouter SDK version: 0.9.1
Model: meta-llama/llama-4-maverick
Images: 10

  Analyzing 20260524_115452.jpg (4080×1884 → 2048×946 px, 154 KB) ... OK
  Analyzing 20260525_094358.jpg (4080×1884 → 2048×946 px, 254 KB) ... OK
  Analyzing 20260524_115516.jpg (4080×1884 → 2048×946 px, 216 KB) ... FAILED → -1
  Analyzing 20260524_123629.jpg (4080×1884 → 2048×946 px, 294 KB) ... OK
  Analyzing 20260524_115506.jpg (4080×1884 → 2048×946 px, 275 KB) ... OK
  Analyzing 20260524_123636.jpg (4080×1884 → 2048×946 px, 263 KB) ... OK
  Analyzing 20260524_123656.jpg (4080×1884 → 2048×946 px, 208 KB) ... OK
  Analyzing 20260524_123639.jpg (4080×1884 → 2048×946 px, 247 KB) ... FAILED → -1
  Analyzing 20260525_094358.jpg (4080×1884 → 2048×946 px, 254 KB) ... OK
  Analyzing 20260525_094404.jpg (4080×1884 → 2048×946 px, 206 KB) ... OK

============================================================
BENCHMARK RESULTS
============================================================

  20260524_115452.jpg
    Ground truth:  pH=7.0, Cl=0.0  (2026-05-24 11:54)
    Predicted:     pH=7.5, Cl=0.3
    Warnings:      GT: –  |  AI: –
    Scores:        pH=50%  Cl=70%  =>  Total: 60%

  20260525_094358.jpg
    Ground truth:  pH=-1.0, Cl=-1.0  (2026-05-25 09:43)
    Predicted:     pH=7.8, Cl=0.5
    Warnings:      GT: no reference scale  |  AI: reference scale missing
    Scores:        pH=0%  Cl=0%  =>  Total: 0%

  20260524_115516.jpg
    Ground truth:  pH=6.8, Cl=0.2  (2026-05-24 11:55)
    Predicted:     pH=-1.0, Cl=-1.0
    Warnings:      GT: –  |  AI: analysis failed or refused
    Scores:        pH=0%  Cl=0%  =>  Total: 0%

  20260524_123629.jpg
    Ground truth:  pH=7.2, Cl=0.4  (2026-05-24 12:36)
    Predicted:     pH=7.4, Cl=0.2
    Warnings:      GT: –  |  AI: reversed orientation
    Scores:        pH=80%  Cl=80%  =>  Total: 60%  ⚠ mismatch (-25%)

  20260524_115506.jpg
    Ground truth:  pH=7.0, Cl=0.0  (2026-05-24 11:55)
    Predicted:     pH=7.4, Cl=3.5
    Warnings:      GT: –  |  AI: severe blur
    Scores:        pH=60%  Cl=0%  =>  Total: 22%  ⚠ mismatch (-25%)

  20260524_123636.jpg
    Ground truth:  pH=7.2, Cl=0.4  (2026-05-24 12:36)
    Predicted:     pH=7.2, Cl=0.8
    Warnings:      GT: –  |  AI: severe blur in right image, not used for analysis
    Scores:        pH=100%  Cl=60%  =>  Total: 60%  ⚠ mismatch (-25%)

  20260524_123656.jpg
    Ground truth:  pH=7.3, Cl=0.6  (2026-05-24 12:36)
    Predicted:     pH=7.4, Cl=5.0
    Warnings:      GT: –  |  AI: –
    Scores:        pH=90%  Cl=0%  =>  Total: 45%

  20260524_123639.jpg
    Ground truth:  pH=6.8, Cl=0.5  (2026-05-24 12:36)
    Predicted:     pH=-1.0, Cl=-1.0
    Warnings:      GT: –  |  AI: analysis failed or refused
    Scores:        pH=0%  Cl=0%  =>  Total: 0%

  20260525_094358.jpg
    Ground truth:  pH=-1.0, Cl=-1.0  (2026-05-25 09:43)
    Predicted:     pH=7.8, Cl=0.5
    Warnings:      GT: no reference scale  |  AI: no reference
    Scores:        pH=0%  Cl=0%  =>  Total: 0%

  20260525_094404.jpg
    Ground truth:  pH=6.4, Cl=0.6  (2026-05-25 09:44)
    Predicted:     pH=7.8, Cl=3.0
    Warnings:      GT: –  |  AI: –
    Scores:        pH=0%  Cl=0%  =>  Total: 0%

  ────────────────────────────────────────
  Scores:   avg=24.7%  min=0%  max=60%
  Passed (≥50%):      3/10

============================================================
COST SUMMARY
============================================================
  gen-1779908198-YbEequ5Fj7Al7hIhBzSH: $0.000948
  gen-1779908200-PKdVrd7N1gGhkLnmUWlc: $0.000741
  gen-1779908206-tHzJf68HJl4ZdWjdujfS: $0.000662 (estimated)
  gen-1779908209-EKusCLV7LWE1auFiW5Kt: $0.000960
  gen-1779908212-PyltoiWGp7UtOBNzEh7O: $0.000418
  gen-1779908215-Iot0pMOBFwWWcPviE2c1: $0.000412
  gen-1779908221-4uoFTYRnchYo4GpBFmNW: $0.000740
  gen-1779908223-fbItMUptDXBOs1Y0Pqb2: $0.000413
  ────────────────────────────────────────
  Total: $0.005292

Done.
```


## Meta: Llama 4 Scout

```
OpenRouter SDK version: 0.9.1
Model: meta-llama/llama-4-scout
Images: 10

  Analyzing 20260524_115452.jpg (4080×1884 → 2048×946 px, 154 KB) ... OK
  Analyzing 20260525_094358.jpg (4080×1884 → 2048×946 px, 254 KB) ... OK
  Analyzing 20260524_115516.jpg (4080×1884 → 2048×946 px, 216 KB) ... OK
  Analyzing 20260524_123629.jpg (4080×1884 → 2048×946 px, 294 KB) ... OK
  Analyzing 20260524_115506.jpg (4080×1884 → 2048×946 px, 275 KB) ... OK
  Analyzing 20260524_123636.jpg (4080×1884 → 2048×946 px, 263 KB) ... OK
  Analyzing 20260524_123656.jpg (4080×1884 → 2048×946 px, 208 KB) ... OK
  Analyzing 20260524_123639.jpg (4080×1884 → 2048×946 px, 247 KB) ... OK
  Analyzing 20260525_094358.jpg (4080×1884 → 2048×946 px, 254 KB) ... OK
  Analyzing 20260525_094404.jpg (4080×1884 → 2048×946 px, 206 KB) ... OK

============================================================
BENCHMARK RESULTS
============================================================

  20260524_115452.jpg
    Ground truth:  pH=7.0, Cl=0.0  (2026-05-24 11:54)
    Predicted:     pH=7.8, Cl=0.0
    Warnings:      GT: –  |  AI: –
    Scores:        pH=20%  Cl=100%  =>  Total: 60%

  20260525_094358.jpg
    Ground truth:  pH=-1.0, Cl=-1.0  (2026-05-25 09:43)
    Predicted:     pH=-1.0, Cl=-1.0
    Warnings:      GT: no reference scale  |  AI: blurry, poor lighting
    Scores:        pH=100%  Cl=100%  =>  Total: 100%

  20260524_115516.jpg
    Ground truth:  pH=6.8, Cl=0.2  (2026-05-24 11:55)
    Predicted:     pH=7.5, Cl=1.5
    Warnings:      GT: –  |  AI: –
    Scores:        pH=30%  Cl=0%  =>  Total: 15%

  20260524_123629.jpg
    Ground truth:  pH=7.2, Cl=0.4  (2026-05-24 12:36)
    Predicted:     pH=7.5, Cl=1.5
    Warnings:      GT: –  |  AI: –
    Scores:        pH=70%  Cl=0%  =>  Total: 35%

  20260524_115506.jpg
    Ground truth:  pH=7.0, Cl=0.0  (2026-05-24 11:55)
    Predicted:     pH=7.6, Cl=0.5
    Warnings:      GT: –  |  AI: –
    Scores:        pH=40%  Cl=50%  =>  Total: 45%

  20260524_123636.jpg
    Ground truth:  pH=7.2, Cl=0.4  (2026-05-24 12:36)
    Predicted:     pH=6.5, Cl=1.5
    Warnings:      GT: –  |  AI: –
    Scores:        pH=30%  Cl=0%  =>  Total: 15%

  20260524_123656.jpg
    Ground truth:  pH=7.3, Cl=0.6  (2026-05-24 12:36)
    Predicted:     pH=-1.0, Cl=-1.0
    Warnings:      GT: –  |  AI: poor lighting, blurry image
    Scores:        pH=0%  Cl=0%  =>  Total: 0%  ⚠ mismatch (-25%)

  20260524_123639.jpg
    Ground truth:  pH=6.8, Cl=0.5  (2026-05-24 12:36)
    Predicted:     pH=7.5, Cl=1.5
    Warnings:      GT: –  |  AI: –
    Scores:        pH=30%  Cl=0%  =>  Total: 15%

  20260525_094358.jpg
    Ground truth:  pH=-1.0, Cl=-1.0  (2026-05-25 09:43)
    Predicted:     pH=-1.0, Cl=-1.0
    Warnings:      GT: no reference scale  |  AI: severe blur, poor lighting, obstructed view
    Scores:        pH=100%  Cl=100%  =>  Total: 100%

  20260525_094404.jpg
    Ground truth:  pH=6.4, Cl=0.6  (2026-05-25 09:44)
    Predicted:     pH=6.5, Cl=1.8
    Warnings:      GT: –  |  AI: –
    Scores:        pH=90%  Cl=0%  =>  Total: 45%

  ────────────────────────────────────────
  Scores:   avg=43.0%  min=0%  max=100%
  Passed (≥50%):      3/10

============================================================
COST SUMMARY
============================================================
  gen-1779908270-3d65XIUFFSaabTsmprym: $0.000220
  gen-1779908274-8abfCZSljlDkrYocWg0J: $0.000222
  gen-1779908276-TUUHEXD73hfMS90sd29G: $0.000220
  gen-1779908280-mkiLooaXgwvBjky7kCTo: $0.000220
  gen-1779908285-hcDi5UeBIgrmivrrpGJd: $0.000220
  gen-1779908289-SfYGdmB8c7dOb1lQEDtQ: $0.000220
  gen-1779908294-t8seRjPPMvS8DOj4Ftw5: $0.000222
  gen-1779908297-EfgqJQmFk5vcRvj2ww1z: $0.000220
  gen-1779908300-y6Iu81R0GjRQEsd0nxAu: $0.000223
  gen-1779908303-gF2tSEtMLAXXEnTjcynN: $0.000220
  ────────────────────────────────────────
  Total: $0.002209

Done.
```


