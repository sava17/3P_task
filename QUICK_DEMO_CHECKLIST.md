# Quick Demo Checklist ✅

## 🎯 5-Minute Demo Flow

### **BEFORE YOU START**
- [ ] Open `prototype_gui.py`
- [ ] Have file explorer ready to show documents folder
- [ ] Clear any old documents: `data/generated_docs/` folder

---

## **Phase 1: BEFORE LEARNING** (2 minutes)

### Tab 1: Setup
- [ ] Click "Extract & Build Knowledge Base"
- [ ] Wait for completion (~20 sec)
- [ ] Note: "5 chunks" in output

### Tab 2: Project Input
- [ ] Click "🏢 Office Building (BK2)" template
- [ ] Click "💾 Save Project"
- [ ] Done in 10 seconds!

### Tab 3: Generate (BASIC)
- [ ] **Verify "📚 Demo Mode" is CHECKED** ✅ ← CRITICAL!
- [ ] Keep pre-selected docs (START, DBK, KPLA) or select just START for speed
- [ ] Click "🚀 Generate Documents"
- [ ] Wait ~30 seconds
- [ ] Look for: "⚠️ DEMO MODE: Generating WITHOUT learned knowledge"
- [ ] Click "📁 Open Folder" - see basic documents

---

## **Phase 2: FEEDBACK & LEARNING** (2 minutes)

### Tab 4: Review & Feedback
- [ ] Select first document from dropdown
- [ ] Scroll through - notice missing BR18 §, distances, etc.
- [ ] Click template buttons:
  - [ ] "Missing BR18 §"
  - [ ] "Unclear distances"
  - [ ] "Fire resistance"
- [ ] Click "❌ Reject"
- [ ] Repeat for other docs (optional, can skip for speed)

### Tab 4: Learn
- [ ] Click "🧠 Learn from All Feedback"
- [ ] Wait ~10 seconds
- [ ] Look for: "Extracted 3 insights"
- [ ] Look for: "Knowledge base now has 8 chunks" (was 5!)
- [ ] **New button appears:** "🔄 Re-Generate Documents"

---

## **Phase 3: AFTER LEARNING** (1 minute)

### Tab 4: Re-Generate
- [ ] Click "🔄 Re-Generate Documents (With Learning)"
- [ ] Wait ~30 seconds
- [ ] Look for: "WITH 3 learned patterns"
- [ ] Look for: "IMPROVED_" prefix in file names

### Compare Documents
- [ ] Go to `data/generated_docs/` folder
- [ ] Find pairs:
  ```
  Kontorhus_Aarhus_City_START_20251208_014523.txt  ← BEFORE
  IMPROVED_Kontorhus_Aarhus_City_START_20251208_014847.txt  ← AFTER
  ```
- [ ] Open both in Notepad/text editor
- [ ] **SHOW THE DIFFERENCE!**
  - BEFORE: Missing BR18 §, vague descriptions
  - AFTER: Includes §508, specific distances (25m), fire class (REI 60), materials (K1 10/B-s1,d0)

---

## **Phase 4: PROOF** (30 seconds)

### Tab 5: Knowledge Base
- [ ] Click "🔄 Refresh Knowledge Base Stats"
- [ ] **Point out the growth:**
  - Total Chunks: **5 → 8** ✅
  - Learned Insights: **0 → 3** ✅
- [ ] Scroll down to see insights in the viewer

---

## 🎤 **What to Say During Demo**

**At Start:**
> "I'll show you how this system learns from feedback and generates better documents."

**Tab 3 (Demo Mode):**
> "First, I'm generating WITHOUT learned knowledge - like a first draft that might miss requirements."

**Tab 4 (Rejection):**
> "The document is missing BR18 paragraphs and specific distances. I'll reject it with template feedback."

**Tab 4 (Learning):**
> "Now Gemini analyzes the feedback and extracts patterns. See - it learned 3 specific improvements!"

**Tab 4 (Re-generate):**
> "Now I regenerate using those learned patterns... notice it says 'WITH 3 learned patterns'."

**File Comparison:**
> "Look at the difference - the first version was incomplete. The second has §508 references, 25-meter distances, REI 60 fire class... everything that was missing!"

**Tab 5:**
> "And here's proof - knowledge base grew from 5 to 8 chunks, with 3 new insights. The system actually learned!"

---

## ✅ Success Indicators

You know the demo worked if you can show:

1. ✅ **Two different document versions** (before/after files)
2. ✅ **Visible improvements** (BR18 §, distances, fire classes in AFTER version)
3. ✅ **Knowledge growth** (5 → 8 chunks shown)
4. ✅ **Extracted insights** (listed in Tab 5)
5. ✅ **Clear workflow** (easy to understand for audience)

---

## 🚨 Common Mistakes to Avoid

❌ **Forgot to check Demo Mode** → Both generations will look similar
   ✅ Always verify checkbox is checked before first generation!

❌ **Didn't give specific feedback** → Learning extracts nothing
   ✅ Use the template buttons! They provide clear, actionable feedback

❌ **Skipped the comparison** → No visual proof
   ✅ Always open both files side-by-side to show improvement

❌ **Didn't explain Demo Mode** → Audience confused why first doc is bad
   ✅ Say "I'm intentionally generating without knowledge first"

---

## 🎯 Ultra-Quick 2-Minute Version

For extremely time-constrained demos:

1. ✅ Tab 2: Template → Save (10 sec)
2. ✅ Tab 3: Demo Mode on → Generate START only (30 sec)
3. ✅ Tab 4: Reject with 2 template reasons (15 sec)
4. ✅ Tab 4: Learn (10 sec)
5. ✅ Tab 4: Re-generate (30 sec)
6. ✅ Show both .txt files side-by-side (25 sec)

**Total: 2 minutes, complete learning demonstration!**

---

## 📋 Pre-Demo Checklist

Before you present:

- [ ] Gemini API key is working (check .env file)
- [ ] `data/generated_docs/` folder exists (auto-created)
- [ ] No errors on startup
- [ ] You've run through the demo once yourself
- [ ] You know where to find the generated files
- [ ] Text editor ready to compare files

---

## 💡 Tips for Great Presentation

1. **Go slow** - Let each step complete before explaining next
2. **Read the logs** - Point out key messages like "Extracted 3 insights"
3. **Show the files** - Visual proof is most convincing
4. **Explain why** - "Demo Mode simulates first draft without knowledge"
5. **Compare visibly** - Open files side-by-side, highlight differences
6. **Show metrics** - "5 chunks became 8, that's 60% growth"

---

## 🎬 You're Ready!

This demo clearly shows:
- ✅ System works end-to-end
- ✅ Learning actually happens
- ✅ Documents measurably improve
- ✅ Knowledge base grows
- ✅ Workflow is practical

**Go show them what continuous learning looks like! 🚀**
