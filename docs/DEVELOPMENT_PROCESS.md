<p align="center">
  <img src="../brand/Marca-Completa-Mekatronik-Colorido-cropped.png" alt="Mekatronik - Advanced Engineering" width="400">
</p>

<h1 align="center">Development Process</h1>

<p align="center">
  <strong>How a Domain Expert + AI Code Assistant Built an Industrial Modbus Simulator</strong>
</p>

---

## The Story

This document chronicles how **ModbusDeviceSIM** was developed through a collaborative process between a **domain expert in industrial automation** and **Claude Code**, an AI-powered development assistant. It serves as a case study for how AI code assistants can empower engineers with deep domain knowledge to build professional software tools — even without a dedicated software development team.

## The Domain Expert's Role

The human in this process is an engineer at **Mekatronik — Advanced Engineering** with expertise in:

- Industrial communication protocols (Modbus RTU/TCP, EtherNet/IP, PROFINET)
- SCADA systems and PLC programming
- Industrial network architecture and device integration
- Energy monitoring and power quality analysis

This is the kind of knowledge that takes years to accumulate and cannot be replaced by an AI. The engineer knows *what* needs to be built, *why* it matters, and *how real devices behave* — the AI assists with the *how to code it* part.

## The AI Assistant's Role

Claude Code served as the development partner, contributing:

- Software architecture design and technology selection
- Code generation, debugging, and testing
- Documentation writing and project scaffolding
- Image processing and asset preparation
- Knowledge of libraries, frameworks, and best practices

## Development Timeline

### Phase 1 — Project Definition & Technology Selection

**What happened:** The engineer described the need — a Modbus device simulator supporting both serial (RTU) and Ethernet (TCP) transports. The AI assistant asked targeted questions to understand the scope.

**Key decisions made collaboratively:**

| Decision | Engineer's Input | AI's Contribution |
|---|---|---|
| **Protocol** | "Modbus RTU and TCP" | Explained transport differences, framing formats |
| **Virtual serial** | "Can you build a virtual serial port?" | Assessed feasibility: recommended com0com for virtual COM ports rather than attempting kernel-driver development |
| **Tech stack** | "Can we run on Windows, Linux, and Raspberry Pi?" | Recommended Python + pymodbus + pyserial for cross-platform support |
| **First device** | "Energy monitoring device" | Proposed register map based on industry-standard meters |

**Insight:** The engineer drove *what* to build. The AI mapped those requirements to the right technologies and identified what was realistic (e.g., virtual serial ports need a driver like com0com — not something to code from scratch).

### Phase 2 — Architecture & Documentation

**What happened:** Before writing any code, the project was documented with a comprehensive README and CLAUDE.md. This "docs-first" approach ensured alignment on architecture before implementation.

**Artifacts produced:**
- `CLAUDE.md` — Technical guidance for AI assistants working in the repo
- `README.md` — Full project documentation with architecture diagrams, register encoding specs, and platform-specific setup
- `docs/DEVELOPMENT_PROCESS.md` — This document

**Insight:** The AI generated architecture diagrams (ASCII), register encoding tables, and platform setup instructions. The engineer validated that these matched real-world industrial conventions (e.g., big-endian word order for IEEE 754 floats — a detail that matters for Modbus interoperability).

### Phase 3 — Brand Integration

**What happened:** The engineer provided Mekatronik brand assets (logo PNG + brand pack PDF). The AI processed these:

- Analyzed the brand pack to extract the color palette and logo variants
- Cropped the logo PNG to remove whitespace
- Made the background transparent for use in documentation
- Integrated the brand into all project documentation

**Insight:** A small but telling example — the engineer provided raw assets, and the AI handled the image processing (Python + Pillow) and integration without requiring design tools or manual editing.

### Phase 4 — Implementation *(in progress)*

Building the actual simulator: device models, simulation engine, transport servers, and CLI interface.

---

## What This Demonstrates

### 1. Domain Knowledge is Irreplaceable

The AI cannot know that Modbus energy meters typically use IEEE 754 floats in big-endian word order, or that com0com is the standard tool for virtual serial ports in industrial development, or that a Raspberry Pi with an RS-485 hat makes a perfect low-cost Modbus slave. **The engineer's domain expertise shaped every architectural decision.**

### 2. AI Removes the "Implementation Barrier"

The engineer knows exactly what a Modbus energy monitor should look like — the registers, the data types, the behavior. Without an AI assistant, translating that knowledge into working Python code, proper project structure, documentation, and tooling would require either:
- Learning software engineering practices from scratch
- Hiring a software developer who would then need to learn industrial protocols

The AI assistant bridges this gap instantly.

### 3. The Conversation IS the Specification

Traditional development requires writing detailed specifications, then handing them to developers, then iterating on misunderstandings. In this process, the specification emerged naturally through conversation:

- *"I want to simulate Modbus RTU and TCP devices"* → scope defined
- *"Can you build a virtual serial port?"* → technical feasibility assessed
- *"We can run on Raspberry Pi, right?"* → platform requirements confirmed
- *"Check the brand directory"* → brand integration triggered

No specification document was written. The conversation itself served as the requirements process, with the AI asking clarifying questions and the engineer making decisions.

### 4. Quality Doesn't Require a Large Team

The output of this process includes:
- Professional documentation with architecture diagrams
- Cross-platform design (Windows / Linux / Raspberry Pi)
- Industry-standard protocol implementation
- Proper project structure with testing framework
- Brand-consistent presentation

This level of engineering rigor typically requires a multi-person team. An AI assistant enables a single domain expert to produce it.

### 5. Speed of Iteration

Decisions that would normally span multiple meetings and email chains happened in minutes:

- Technology evaluation → instant comparison tables
- Architecture design → immediate diagram generation
- Documentation → produced alongside decisions, not as an afterthought
- Asset processing → image cropping and transparency in one step

## The Broader Implication

Industrial automation engineers, process engineers, and other domain experts often have ideas for tools that would dramatically improve their work — but lack the software development resources to build them. AI code assistants change this equation fundamentally.

**The new model:**
```
Domain Expert  +  AI Assistant  =  Working Software
(knows WHAT)      (knows HOW)      (built together)
```

This is not about replacing developers. It's about **empowering the people closest to the problem** to build solutions directly — with AI handling the syntax, structure, and scaffolding while the human provides the knowledge, judgment, and vision that no AI can replicate.

---

<p align="center">
  <em>Developed by Mekatronik — Advanced Engineering</em><br>
  <em>With Claude Code as AI development assistant</em>
</p>
