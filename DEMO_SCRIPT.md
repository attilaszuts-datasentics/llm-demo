# Workshop Demo Script
**Extracting Data from Reports with AI — Azure & Databricks**
Total time: ~30 min (20–25 min presentation + 5–10 min Q&A)

---

## Before the session

1. Run `./run_demos.sh` — all 4 apps start in the background
2. Open 4 browser tabs: ports 8501 / 8502 / 8503 / 8504
3. In tab 8501 (Pipeline), pre-select **CZ_Office_Q12025_Savills** in the sidebar — do NOT click Run yet
4. Have the actual PDF open in Preview as a visual anchor

---

## Part 1 — The problem (2 min)

> "We get these quarterly market reports from 10+ brokers. Each one is different — different layout, different language, some are mostly charts. Someone has to read them and type the numbers into a spreadsheet. Today we're going to show how AI can do that automatically."

Hold up (or screen-share) one of the PDFs. Point out:
- The summary table on page 1 (Savills is the clearest example)
- The fact that the same number — vacancy rate — is in a different place in every report
- CBRE Retail: barely any text at all, mostly images

> "So the challenge is: how do you build a system that works reliably across all of these, not just the easy ones?"

---

## Part 2 — The pipeline (7 min)
**Tab: `http://localhost:8501`**

> "Let's start at the beginning. A new report arrives. What happens?"

1. Confirm **CZ_Office_Q12025_Savills** is selected. Click **▶ Run Pipeline**.
2. Walk through each step as it animates:
   - **Azure Blob Storage** — "First it lands in cloud storage. Every incoming report gets stored here automatically — think of it as the intake tray. Nothing gets processed until it's safely stored."
   - **Azure Document Intelligence** — "This Azure service reads the document structure — it finds the tables, the labels, the layout. It doesn't understand what 'vacancy rate' means, but it can see that it's a table with rows and columns." Point at the extracted table in the UI. "This is what Doc Intelligence gives us — already structured, with a confidence score per element."
   - **Azure OpenAI (GPT-4o)** — "Now we send this structured content to a language model. It understands context — it knows that 7.0% next to the word 'vacancy' means vacancy rate, not something else. It also normalizes: one broker writes '7.0%', another writes '700 bps', GPT-4o makes those consistent." Point at the JSON output and the token count. "The whole thing costs about two cents per report."
   - **Delta Lake (Bronze → Silver → Gold)** — Click through the three tabs. "Bronze is the raw dump — exactly what came back from the model, no changes. Silver is typed and normalized. Gold is validated against our schema and ready for analytics. If a field fails validation — say, a yield of 42% instead of 4.2% — it never reaches Gold."

3. Now switch to **AT_Retail_Q12025_CBRE** and run again.
   - Doc Intelligence step: "No tables detected — this one is mostly images, the text layer is almost empty."
   - Gold tab: only 3 fields, confidence is red.
   > "This is an important point — the system doesn't silently fail. It surfaces the uncertainty rather than writing a bad number to the table. Low-confidence fields go to a review queue, which we'll see in a minute."

---

## Part 3 — Why strategy matters (4 min)
**Tab: `http://localhost:8502`**

> "Not all extraction approaches are equal. Let me show you what happens if we use different techniques on the same report."

1. Select **CZ_Office_Q12025_Savills**, click **▶ Compare strategies**.
2. Point at the three columns:
   - **Raw OCR** — "Just reading the text, using pattern matching. Works on simple PDFs, breaks on anything complex."
   - **Document Intelligence** — "Much better on structured reports. Still misses context."
   - **Azure OpenAI** — "Highest accuracy, and crucially — it can tell you *where* it found the number."
3. Toggle on **Show source quotes** if not already on. Point at a quote. "Every value has a citation. We can verify it."

4. Switch to **AT_Retail_Q12025_CBRE**.
   > "Same three strategies, different report. Raw OCR basically fails. Doc Intelligence fails too — no tables to read. OpenAI does better but confidence is still low because the information just isn't in the text."

5. Scroll down to "When does each strategy struggle?"
   > "The honest answer is: no single approach wins everywhere. A production system combines all three — use Doc Intelligence to pre-process, OpenAI to extract and verify, and always surface what it isn't sure about."

---

## Part 4 — Human review (4 min)
**Tab: `http://localhost:8503`**

> "So what happens to the fields the system isn't confident about?"

1. The queue loads showing low-confidence fields sorted to the top (🔴 first).
2. Point at the top items — they're mostly from CBRE and Knight Frank.
   > "These are exactly the two reports we just saw struggle. The system is correctly routing them here."
3. Click on a field that has a source quote. Read the quote aloud.
   > "The reviewer doesn't need to go back to the PDF. The exact sentence the AI used is right there. They can check it in two seconds."
4. Click **✅ Approve**.
5. Click on a field with no source quote (one of the CBRE ones).
   > "No quote — means the value came from a chart or an image. The AI is guessing. This one we'd reject and verify manually."
6. Click **❌ Reject**.
7. Point at the sidebar progress bar.
   > "High-confidence fields — above 80% — are auto-approved and never appear here. Analysts only review the tail. In practice, for a clean report like Savills, the queue is empty."
8. Point at the **Commit to Delta Lake** button.
   > "Once everything is reviewed, one click writes the approved fields to the Gold table. Rejected ones stay out."

---

## Part 5 — Querying the data (4 min)
**Tab: `http://localhost:8504`**

> "Once the data is in Delta Lake, this is where Databricks Genie comes in. This is the part that tends to surprise people."

1. Point at the suggested questions across the top.
   > "An analyst can just type a question. No SQL, no knowing which table to look in, no knowing column names."

2. Click **"Compare prime yields across all asset classes"**.
3. Watch the thinking animation — point out the steps: understanding the question, finding the right table, writing SQL.
4. Point at the generated SQL.
   > "This is the SQL Genie wrote. If you know SQL you can read it and verify it's right. If you don't, you don't have to."
5. Point at the bar chart.
   > "Czech retail at 4.25%, Austrian offices at 5%. This took about two seconds and zero SQL knowledge."
6. Point at the explanation text.
   > "Genie also interprets the result — not just a table, but a sentence saying what it means."

7. Click **"Which reports had low-confidence extractions?"**
   > "This is a meta-question about the process itself. Which brokers are giving us data that needs more review? That's useful for prioritizing where to invest in better extraction."

8. Click **"Show me take-up volumes across all office markets"** — point at the grouped bar chart.
   > "Vienna versus Prague, gross versus net, side by side. Two seconds from question to chart."

---

## Wrap-up (2 min)

> "So to recap the end-to-end flow:"

Point at fingers:
1. **PDF arrives → Azure Blob Storage**
2. **Azure Document Intelligence reads the structure**
3. **Azure OpenAI extracts and grounds the values**
4. **Low-confidence fields go to a human review queue**
5. **Approved data lands in Delta Lake Gold table**
6. **Analysts query it in plain English with Genie**

> "What we showed today is a v0 — real data from your actual broker reports, real extraction logic, fake service calls for the demo. The patterns hold in production: the pipeline, the confidence gating, the review queue, and Genie on top."

> "The key design choices worth remembering: Azure Document Intelligence handles structure so the LLM doesn't have to guess layout. Every value has a source quote so nothing is a black box. Low confidence goes to humans, not to production. And once it's in Delta Lake, anyone can query it without touching the data engineering layer."

---

---

## Q&A (5–10 min)

### Prompts in case the room is quiet

- *"How accurate is it really?"* — Depends on the report. Clean tabular PDFs like Savills hit 95%+. Image-heavy ones like CBRE need pre-processing or a different approach (e.g. Doc Intelligence layout model with higher resolution).
- *"What about reports in German or Czech?"* — OpenAI handles multilingual natively. Doc Intelligence supports 100+ languages. We saw this with the Otto report.
- *"Can it handle new report formats automatically?"* — Yes, that's the advantage over rule-based extraction. No maintenance when a broker changes their layout.
- *"What's the cost?"* — Azure OpenAI is priced per token. A 4-page report costs roughly $0.01–0.03 per run. Doc Intelligence adds a small fixed cost per page.
- *"How do we know the AI didn't hallucinate a number?"* — The grounded strategy forces the model to cite its source. If the quote isn't in the document, it gets flagged. The review queue is the last safety net.

---

## Files

| File | Purpose |
|------|---------|
| `demo_pipeline.py` | Demo 2 — animated ingestion pipeline |
| `demo_compare.py` | Demo 3 — strategy comparison |
| `demo_review.py` | Demo 4 — human review queue |
| `demo_genie.py` | Demo 5 — Databricks Genie NL queries |
| `fixtures.py` | Pre-extracted data for all 7 PDFs (no API calls) |
| `run_demos.sh` | Starts all 4 apps on ports 8501–8504 |
| `demo.py` | CLI script — runs real LLM extraction (needs `ANTHROPIC_API_KEY`) |
| `app.py` | Streamlit version of the real extraction review (needs `ANTHROPIC_API_KEY`) |
| `strategies.py` | 5 extraction strategies (vanilla, table-first, regex+LLM, grounded, self-consistency) |
| `schema.py` | Pydantic model with field validators |
| `utils.py` | PDF text/table extraction helpers |
