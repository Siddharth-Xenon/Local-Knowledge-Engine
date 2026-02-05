# Project: Local-First Enterprise Knowledge Engine (GraphRAG)

**Version:** 1.0 (Architecture)

**Status:** Discarded

**Hardware Profile:** Heterogeneous Service Cluster (RTX 2060 + GTX 1660)

---

## Engineering Post-Mortem: The Distributed Inference Experiment

**Objective:**
We initially attempted to distribute the LLM inference across both nodes (Tensor/Pipeline Parallelism) using Ethernet to maximize available VRAM.

**Outcome: Rejected.**
Our benchmarks revealed that while utilizing both GPUs is possible, it is architecturally inefficient for this specific hardware class.

* **Latency Variance:** On a standard Cat6 Gigabit connection, synchronization overhead (RPC round-trips) fluctuated between 200µs and 500µs per token. This "jitter" destroyed the Time-To-First-Token (TTFT), pushing it >10s.
* **The "Convoy Effect":** The heterogeneous nature of the cluster (RTX 2060 vs. GTX 1660) meant the faster GPU was constantly stalled, waiting for the slower GPU to finish its layers.
* **Conclusion:** Since the 4-bit quantized model (~5GB) fits entirely within the VRAM of a single RTX 2060 (6GB), **monolithic inference** provides 300% better throughput and significantly lower latency than a distributed setup. The architecture was pivoted to a **Service-Oriented approach**, dedicating the secondary GPU to retrieval tasks.
