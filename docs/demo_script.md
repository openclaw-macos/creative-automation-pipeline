# Demo Video Script – Creative Automation Pipeline
**Length:** 3 minutes  
**Voice:** Your Voicebox Digital Twin (conversational, confident, slightly excited)  
**Visuals:** Screen recording of terminal, browser, and folder views.

---

## (0:00 – 0:30) INTRODUCTION

> **[Visual: Clean title screen with company logo and tagline “Creative Automation Pipeline – Proof of Concept”]**

**Voiceover:**  
“Hi, I’m [Your Name], and today I’m going to show you a proof‑of‑concept that’s going to change how we produce social ad creatives. Right now, every product launch needs dozens of images, each checked for brand compliance, legal safety, and consistency. That’s manual, slow, and error‑prone.

What if we could automate all of that—and still keep full control? That’s exactly what we built. Let me walk you through it.”

---

## (0:30 – 1:30) LOCAL SETUP

> **[Visual: Terminal window showing a few commands]**

**Voiceover:**  
“First, we start with the tools we already have: ComfyUI for image generation, and Voicebox for text‑to‑speech—both running locally on this Mac Studio. No cloud costs, no API limits.

We’ve extended ComfyUI with a Python script that adds three critical layers: brand compliance, legal guardrails, and detailed reporting. The whole thing lives in a clean, version‑controlled folder structure.

Let’s look at the repository. You can see `configs` for brand settings, `src` for the Python modules, `docs` for documentation, and `outputs` where everything gets saved. This separation lets brand managers tweak colors and logos without touching code, and developers can improve the engine without breaking the creative workflow.”

> **[Visual: Quick folder tree view, then open brand_config.json to show hex colors and prohibited‑word list]**

---

## (1:30 – 2:30) PIPELINE EXECUTION

> **[Visual: Terminal running the extended generation command]**

**Voiceover:**  
“Now, let’s run it. We’ll generate an image for our new coffee maker. The command looks like this:

```bash
python src/comfyui_generate.py \
  --prompt 'a sleek coffee maker on a kitchen counter' \
  --output outputs/images/coffee.png \
  --product 'Coffee Maker' \
  --campaign-message 'Start your day smarter with our premium coffee maker' \
  --compliance-check \
  --legal-check
```

We’re telling it to run brand‑compliance checks, scan the campaign message for prohibited words, and log everything to a database.

While it runs, you can see ComfyUI processing the image. A few seconds later… done! The image is saved, and the compliance module has already checked for our logo and brand colors. The legal guardrail scanned the campaign message—no banned words, so we’re clear.

But what’s really powerful is what happens next.”

---

## (2:30 – 3:00) REVIEWING OUTPUTS

> **[Visual: Quick view of the generated coffee maker image, then switch to DB Browser showing the SQLite log]**

**Voiceover:**  
“First, the image itself—professional, on‑brand, ready for social media. But behind the scenes, the pipeline logged every detail: product name, dimensions, compliance status, generation time, and which checks passed or failed.

We can open the SQLite database with DB Browser—a tool anyone on the marketing team can use. Here’s our coffee‑maker entry. It shows a PASS on brand colors, PASS on logo detection, PASS on legal check. Total generation time: 1.2 seconds.

If something had failed—say the logo was missing—the log would flag it immediately, and we could re‑run the generation before any human ever sees it.

And that’s the big idea: **automation with guardrails**. We can now generate hundreds of creatives overnight, knowing each one is on‑brand, legally safe, and fully tracked for audit.”

---

## (3:00 – 3:10) CLOSING

> **[Visual: Final screen with repository link and contact info]**

**Voiceover:**  
“This is just the start. We can extend it with more advanced vision models, region‑specific legal rules, and dashboards for real‑time analytics. But already, it turns a manual, risky process into a reliable, scalable pipeline.

Thanks for watching. If you’d like to try it yourself, the whole repository is ready to go.”

--- 

**Production Notes:**
- Pause slightly after each section to let visuals settle.
- Keep the tone enthusiastic but not rushed.
- Highlight the “guardrails” concept—it’s not just automation, it’s safe automation.
- End with a clear call‑to‑action (e.g., “Clone the repo and run the demo yourself”).