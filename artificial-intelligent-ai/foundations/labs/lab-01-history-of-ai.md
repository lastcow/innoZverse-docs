# Lab 01: The History of AI — From Turing to Transformers

## Objective

Understand how artificial intelligence evolved from a philosophical thought experiment into the most transformative technology of our era. By the end of this lab you will be able to:

- Trace the key milestones from 1950 to 2025
- Explain the three "AI winters" and what ended each one
- Identify which breakthroughs made modern LLMs possible
- Describe where the field stands today and where it is heading

---

## The Turing Test and the Dawn of AI (1950–1956)

In 1950, British mathematician Alan Turing published *Computing Machinery and Intelligence*, asking the question: **"Can machines think?"** He proposed the **Imitation Game** — now called the Turing Test — where a human interrogator converses with a machine and a human via text, trying to tell them apart. If the machine is indistinguishable, it "passes."

Turing was not just theorising. By 1950 he had already designed the architecture of the modern computer, cracked the German Enigma cipher during World War II, and built one of the first chess-playing programs. He understood computation at a level few others did.

> 💡 **Why it matters:** The Turing Test set the earliest benchmark for AI. Even today, passing it remains controversial — modern LLMs can fool most people most of the time, yet researchers debate whether that constitutes "intelligence."

**1956 — The Dartmouth Conference**

The word "artificial intelligence" was coined by John McCarthy at the **Dartmouth Summer Research Project**. Attendees included Marvin Minsky, Claude Shannon, and Herbert Simon — the founding generation of AI. Their optimism was extraordinary: they believed a small group of researchers could solve AI in a single summer.

They were wrong. But they launched a field.

---

## The First Golden Age and the First Winter (1956–1974)

The early years produced genuine excitement. Programs like:
- **Logic Theorist (1956)** — proved 38 of 52 theorems in *Principia Mathematica*
- **ELIZA (1966)** — a chatbot that mimicked a Rogerian therapist; users frequently forgot they were talking to a machine
- **SHRDLU (1970)** — understood natural language instructions about blocks in a simulated world

But the limits were stark. These systems were **brittle** — ELIZA could not actually understand; it pattern-matched. The real world was messier than any simulated environment.

**First AI Winter (1974–1980)**

The UK's Lighthill Report (1973) concluded that AI had failed to deliver on its promises. US and UK government funding was slashed. The field contracted to a small group of true believers.

---

## Expert Systems and the Second Winter (1980–1993)

AI revived with **expert systems** — programs encoding human expertise as `IF-THEN` rules. Companies spent millions:
- **XCON (1980)** — Digital Equipment Corporation used it to configure computer orders, saving an estimated $40M/year
- **MYCIN** — diagnosed blood infections as accurately as physicians

But expert systems required enormous manual effort to build and maintain. They couldn't learn. When the rules changed, the system broke.

**Second AI Winter (1987–1993)**

The specialised Lisp machines that ran expert systems were obliterated by cheaper general-purpose hardware. The $500M expert systems industry collapsed. DARPA cut funding again.

---

## The Statistical Revolution (1990s–2010)

Out of the rubble came a different approach: instead of encoding rules, **learn from data**.

Key milestones:
- **1989** — Yann LeCun applies backpropagation to handwritten digit recognition using convolutional neural networks (CNNs). The US Post Office begins using it to read zip codes.
- **1997** — IBM Deep Blue defeats Garry Kasparov at chess. Not AI in the general sense, but proof that machines could surpass humans at specific cognitive tasks.
- **1998** — LeCun's LeNet-5 establishes the CNN architecture still used today.
- **2006** — Geoffrey Hinton coins "deep learning" and shows that deep neural networks can be trained effectively. The third golden age begins.

---

## Deep Learning Takes Over (2012–2017)

**2012: AlexNet**

Alex Krizhevsky, Ilya Sutskever, and Geoffrey Hinton enter the **ImageNet** competition — classifying 1.2 million images into 1,000 categories. AlexNet achieves 15.3% error rate; the second-place entry: 26.2%. The gap is so large it shocks the field. Computer vision would never be the same.

**2014: GANs**

Ian Goodfellow invents **Generative Adversarial Networks** — two neural networks competing: one generates fake images, one tries to detect them. The result: synthetic images indistinguishable from photographs.

**2016: AlphaGo**

DeepMind's AlphaGo defeats Lee Sedol, the world's best Go player, 4-1. Go has more possible positions than atoms in the observable universe. The AI community expected this to take another decade.

---

## The Transformer Era (2017–Present)

**2017: "Attention Is All You Need"**

Google researchers publish the **Transformer architecture**. Instead of processing sequences step-by-step (like RNNs), Transformers process the entire sequence at once using **self-attention** — each word attends to every other word simultaneously.

This was the unlock. Transformers could be scaled. More data + more compute = better performance, with no ceiling in sight.

**2018–2019: BERT and GPT**

- **BERT** (Google, 2018) — bidirectional Transformer pre-trained on the entire Wikipedia + BookCorpus. Fine-tuned on specific tasks, it achieves state-of-the-art on 11 NLP benchmarks.
- **GPT** (OpenAI, 2018) → **GPT-2** (2019) — OpenAI initially refuses to release GPT-2, claiming it is "too dangerous." The hype is enormous. In retrospect, GPT-2 is tiny compared to what follows.

**2020: GPT-3**

175 billion parameters. Few-shot learning. No fine-tuning required — just show it a few examples in the prompt and it generalises. Developers build hundreds of applications on the API. The era of **Large Language Models** begins.

**2022: ChatGPT**

OpenAI wraps GPT-3.5 in a chat interface using **RLHF** (Reinforcement Learning from Human Feedback) to make it helpful and safe. ChatGPT reaches 100 million users in 2 months — the fastest consumer product adoption in history.

**2023–2025: The LLM Race**

| Model | Organisation | Notable |
|-------|-------------|---------|
| GPT-4 | OpenAI | Multimodal; scores 90th percentile on bar exam |
| Claude 3 Opus | Anthropic | Constitutional AI; strong reasoning |
| Gemini Ultra | Google DeepMind | Natively multimodal; outperforms GPT-4 on MMLU |
| Llama 3 | Meta | Open weights; runs locally |
| Grok | xAI | Real-time web access; irreverent personality |
| Claude 4 | Anthropic | 2025; extended context, agentic capabilities |

---

## Key Figures in AI History

| Person | Contribution |
|--------|-------------|
| Alan Turing | Theoretical foundation; Turing Test |
| John McCarthy | Coined "artificial intelligence"; Lisp programming language |
| Marvin Minsky | Neural networks pioneer; MIT AI Lab co-founder |
| Geoffrey Hinton | Backpropagation; deep learning; "Godfather of AI" |
| Yann LeCun | Convolutional neural networks; Meta Chief AI Scientist |
| Yoshua Bengio | Deep learning theory; co-winner Turing Award 2018 |
| Ilya Sutskever | AlexNet; OpenAI co-founder |
| Sam Altman | OpenAI CEO; commercialised LLMs |
| Demis Hassabis | DeepMind; AlphaFold; Nobel Prize in Chemistry 2024 |

---

## The Pattern: Hype, Winter, Breakthrough

Every AI era follows the same pattern:
1. **Bold claims** by researchers
2. **Failure** to deliver on timeline
3. **Funding cuts** and disillusionment (winter)
4. **Quiet breakthroughs** from the remaining true believers
5. **Unexpected unlock** — new data, compute, or architecture — that changes everything

The Transformer + scale + internet data was the unlock that ended the possibility of a third winter. We are now in an era of continuous improvement with no floor visible.

---

## Summary

| Era | Period | Key Idea | Why It Stalled |
|-----|--------|----------|----------------|
| Symbolic AI | 1956–1974 | Rules and logic | Too brittle, too narrow |
| Expert Systems | 1980–1987 | Encode human expertise | Too expensive to maintain |
| Statistical ML | 1990–2011 | Learn from data | Limited compute and data |
| Deep Learning | 2012–2017 | Many-layer neural nets | Needed more scale |
| LLM Era | 2017–now | Transformers + scale | No ceiling yet visible |

---

## Further Reading

- Turing, A.M. (1950). *Computing Machinery and Intelligence*. Mind, 59, 433–460.
- Vaswani et al. (2017). *Attention Is All You Need*. NeurIPS.
- Marcus, G. & Davis, E. (2019). *Rebooting AI*. Pantheon Books.
- [AI Timeline — Our World in Data](https://ourworldindata.org/brief-history-of-ai)
- [The Bitter Lesson — Rich Sutton](http://www.incompleteideas.net/IncIdeas/BitterLesson.html)
