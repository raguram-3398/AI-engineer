# LLM APIs — Sales Call Intelligence

**What it is:** My first AI product. Upload a recording of a sales call and within about 30 seconds you get a written analysis — the customer's objections, agreed action items, overall sentiment and an executive summary — appearing live on screen as the AI writes it. Names, phone numbers, emails and card numbers are removed before the AI ever sees the conversation.

**Real numbers:** about $0.06 per analyzed call · about 28 seconds end to end for a 5–9 minute call · 95% of the code covered by automated tests · 27 of 27 personal details removed in the privacy test.

**How it works, briefly:** Speech-to-text (OpenAI Whisper) turns the audio into a transcript, private details are scrubbed out, then Claude analyzes it and the result streams to a simple web dashboard.

**What I learned:**

- Calling AI models from code and streaming their answers live
- Making the AI return structured results and retrying when it doesn't
- Keeping private data away from the AI
- Guarding against users trying to trick the AI with their input
- Tracking the cost of every call
- Time limits on every outside service

**Where it lives:** It has its own repository and a live demo:
- Code: [github.com/raguram-3398/Sales-Intelligence](https://github.com/raguram-3398/Sales-Intelligence)
- Live demo: [huggingface.co/spaces/raguram3398/sales-intelligence](https://huggingface.co/spaces/raguram3398/sales-intelligence)
