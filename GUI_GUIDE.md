# BR18 Automation GUI Demo Guide

## Overview

The GUI provides a visual, step-by-step demonstration of the BR18 document automation system with continuous learning. Perfect for presentations and showcasing the learning cycle.

## Features

### 🎨 Visual Interface
- **Dark theme** matching your other automation tools
- **Step-by-step progress indicators** showing current stage
- **Real-time console output** showing all processing details
- **Live metrics dashboard** tracking improvement

### 📊 Six Interactive Steps

1. **Extract Examples** - Load and index BR18 PDFs
2. **Generate Initial** - Create documents before learning (40% approval)
3. **Get Feedback** - Simulate municipality reviews
4. **Learn Patterns** ⭐ - Gemini analyzes feedback (THE KEY INNOVATION)
5. **Generate Improved** - Create documents after learning (75% approval)
6. **Show Metrics** - Display performance improvements

### 🎮 Two Operation Modes

**Full Demo Mode:**
- Click "▶️ Start Full Demo" to run all 6 steps automatically
- Perfect for presentations
- Takes 3-5 minutes total

**Step-by-Step Mode:**
- Click individual step buttons (Step 1, Step 2, etc.)
- Great for detailed walkthroughs
- Pause between steps to explain concepts

## Quick Start

### Windows
```bash
run_demo_gui.bat
```

### Python
```bash
python demo_gui.py
```

## GUI Layout

```
┌─────────────────────────────────────────────────────────────────┐
│  🧠 BR18 Document Automation with Continuous Learning           │
│  Intelligent BR18 document generation powered by Gemini AI      │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  [Step 1] [Step 2] [Step 3] [Step 4] [Step 5] [Step 6]        │
│  Extract  Generate Get      Learn    Generate Show             │
│  Examples Initial  Feedback Patterns Improved Metrics          │
│                                                                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  📋 Console Output                                              │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ Processing: START - Starterklæring.pdf                  │   │
│  │   - Extracted 12450 characters                          │   │
│  │   - Created 25 chunks                                   │   │
│  │                                                         │   │
│  │ ✨ Extracted 8 Learning Insights:                       │   │
│  │ 1. København requires explicit BR18 §508...             │   │
│  │    Confidence: 85%                                      │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  [▶️ Start Full Demo] [Step 1] [Step 2] [Step 3] [Step 4]     │
│                       [Extract] [Generate] [Feedback] [Learn]  │
│                       [Step 5] [Step 6]                        │
│                       [Improve] [Metrics]                      │
│                                                                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Initial Rate   After Learning   Improvement    Knowledge       │
│      40%            75%             +35%          125 chunks    │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## What Each Step Shows

### Step 1: Extract Examples
**What happens:**
- Loads START and DBK PDFs from `data/example_pdfs/`
- Uses Gemini Vision to extract text and metadata
- Creates 500-word chunks with 50-word overlap
- Generates embeddings using Gemini
- Builds vector index

**Console Output:**
```
Processing: START - Starterklæring.pdf
  - Extracted 12450 characters
  - Created 25 chunks
  - Metadata: START

Adding 50 chunks to vector database...
Built vector index with 50 chunks
```

**Metrics Updated:**
- Knowledge Chunks: 50

---

### Step 2: Generate Initial Documents
**What happens:**
- Creates 5 test building projects
- For each project:
  - Queries RAG system for relevant context
  - Generates START document using Gemini + context
  - Saves to `data/generated_docs/`

**Console Output:**
```
Project: Test Building 1
  Municipality: København
  Fire Classification: BK2
  Retrieved 5 relevant context chunks from RAG
  Generated START document (3420 chars)
```

**Time:** ~45 seconds

---

### Step 3: Get Feedback
**What happens:**
- Simulates municipality review of generated documents
- 40% approval rate (2 approved, 3 rejected)
- Rejected documents include:
  - Specific rejection reasons
  - Suggestions for improvement
  - Feedback text

**Console Output:**
```
❌ REJECTED: Test Building 1
  Municipality: København
  Reasons: Missing BR18 §508, Unclear evacuation...

✅ APPROVED: Test Building 2
  Municipality: Aarhus
```

**Metrics Updated:**
- Initial Approval Rate: 40%

---

### Step 4: Learn Patterns ⭐ THE MAGIC
**What happens:**
- Groups feedback by municipality
- Sends feedback batch to Gemini for analysis
- Gemini extracts 5-10 specific patterns:
  - What causes rejections
  - Municipality-specific requirements
  - Successful document patterns
- Converts insights to knowledge chunks
- Adds to vector database

**Console Output:**
```
Analyzing 5 feedback items...
Using Gemini 2.5 Flash to extract patterns...

✨ Extracted 8 Learning Insights:

1. København requires explicit BR18 §508 reference in declaration
   Confidence: 85%
   Municipality: København

2. Evacuation distances must be in meters, not "adequate"
   Confidence: 78%
   Municipality: København

Converting insights to knowledge chunks...
Added 8 new knowledge chunks from learning
```

**Metrics Updated:**
- Knowledge Chunks: 50 → 58 (examples + insights)

**Time:** ~60 seconds (Gemini analysis)

---

### Step 5: Generate Improved Documents
**What happens:**
- Creates 5 new test projects
- RAG now retrieves BOTH:
  - Original approved examples
  - Learned insights from Step 4
- Generates documents with learned patterns applied

**Console Output:**
```
Project: Test Building 6
  Retrieved 5 context chunks (includes learned insights)
  Including 2 learned insight chunks
  Generated improved START document
```

**Simulated Result:** 75% approval rate

**Time:** ~45 seconds

---

### Step 6: Show Metrics
**What happens:**
- Displays comprehensive performance metrics
- Shows before/after comparison
- Knowledge base growth
- Municipality-specific learning

**Console Output:**
```
📊 PERFORMANCE METRICS:
  Initial Approval Rate:   40%
  After Learning:          75%
  Improvement:             +35%

📈 KNOWLEDGE BASE GROWTH:
  Total Knowledge Chunks:  58
  From Approved Docs:      50
  From Learned Insights:   8

🎯 MUNICIPALITY-SPECIFIC LEARNING:
  København: 30 knowledge chunks
  Aarhus: 18 knowledge chunks
```

**Metrics Updated:**
- After Learning Rate: 75%
- Improvement: +35%

---

## Color Coding

### Step Progress Indicators
- **Blue** - Current step in progress
- **Green** - Completed steps
- **Gray** - Not yet started

### Console Text
- ✅ Green check - Success
- ❌ Red X - Failure/Rejection
- ⭐ Star - Important highlight
- 📊 📈 🎯 - Section headers

## Tips for Presentations

### Before Presenting
1. Run the demo once to verify everything works
2. Delete `data/knowledge_base/` to start fresh
3. Have your `.env` file with Gemini API key ready

### During Presentation

**Full Demo Mode (Recommended):**
1. Click "▶️ Start Full Demo"
2. Let it run while explaining each step as it executes
3. Point out the console output in real-time
4. Highlight Step 4 (learning) as the key innovation
5. Show final metrics at the end

**Step-by-Step Mode (For Deep Dive):**
1. Run Step 1, explain PDF extraction
2. Run Step 2, show document generation
3. Run Step 3, discuss feedback simulation
4. **Pause before Step 4** - This is the wow moment!
5. Run Step 4, highlight the Gemini analysis extracting patterns
6. Run Step 5, show how insights improve generation
7. Run Step 6, emphasize the 35% improvement

### Key Talking Points

**Step 4 Focus:**
- "This is where the magic happens"
- "Gemini analyzes complex feedback automatically"
- "No manual rule extraction needed"
- "Confidence scores show pattern strength"
- "Municipality-specific learning paths"

**Metrics Focus:**
- "40% → 75% is a 35 percentage point improvement"
- "Knowledge base grew from 50 to 125 chunks"
- "System learns from every project automatically"

## Troubleshooting

### GUI Won't Start
```bash
# Install CustomTkinter
pip install customtkinter

# Or reinstall all dependencies
pip install -r requirements.txt
```

### Steps Show Errors
- Make sure you have `.env` file with `GEMINI_API_KEY`
- Check you have the example PDFs in `data/example_pdfs/`
- Run steps in order (1→2→3→4→5→6)

### Slow Performance
- Steps 2, 4, and 5 involve Gemini API calls
- Each takes 30-60 seconds
- This is normal for demonstration

### Console Text Too Small
- Edit `demo_gui.py` line with `font=ctk.CTkFont(family="Consolas", size=11)`
- Change `size=11` to `size=13` or larger

## Keyboard Shortcuts

- **Window Close**: Alt+F4 or click X
- **Copy from Console**: Ctrl+C (select text first)

## File Outputs

During demo, files are created in:

**Generated Documents:**
```
data/generated_docs/
├── {uuid}_START.txt
├── {uuid}_START.txt
└── ...
```

**Feedback Data:**
```
data/feedback/
└── feedback_batch_{timestamp}.json
```

**Knowledge Base:**
```
data/knowledge_base/
├── embeddings.ann (vector index)
└── chunks.json (all knowledge)
```

## Customization

### Change Number of Projects
Edit `demo_gui.py`:
```python
# Line ~350
self.initial_docs = self.demo_system.step2_generate_initial_documents(
    num_projects=5  # Change this
)
```

### Adjust Approval Rates
Edit `demo_gui.py`:
```python
# Line ~360
self.feedbacks = self.demo_system.step3_simulate_municipality_feedback(
    self.initial_docs,
    initial_approval_rate=0.4  # Change this (0.0-1.0)
)
```

### Change Window Size
Edit `demo_gui.py`:
```python
# Line ~43
self.geometry("1600x1000")  # Change dimensions
```

---

**Enjoy showcasing your continuous learning system!** 🚀

The GUI makes it easy to demonstrate the power of AI-driven learning without remembering CLI commands.
