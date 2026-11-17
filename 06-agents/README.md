# Agents — Support Agent

**What it is:** A customer support agent for a small online store. A signed-in customer can ask about their orders and ask for a refund. The agent checks the refund policy and issues the refund itself, but any refund over $100 pauses until a person approves it, and a paused run still resumes after the server is restarted. Every change to the agent was scored by an automatic test of what it did, not just what it said, before it was kept.

**Real numbers** (27 test tasks, each run 3 times):
- Passed 26 of 27 tasks; the one failure is recorded in the baseline, not hidden
- Blocked all 4 attacks: a planted instruction in an order note, a customer approving their own refund through the chat, and reading or refunding another customer's order
- The expected refunds, and no others, were in the database after all 27 tasks
- About 2.5 seconds per task, and about $0.04 for a full test run

**How it works, briefly:** Claude decides which tool to call: look up an order, list orders, or issue a refund. The tools run as a separate service the agent reaches through MCP, and every call needs a sign-in token from Keycloak (OAuth 2.0). Which customer is asking comes from that token, never from the AI, so the AI cannot look at or refund someone else's order. Each run is saved in PostgreSQL, Redis limits how many requests a customer can send, and every step is traced in Langfuse.

**What I learned:**

- Building an agent loop by hand, with a step limit and a time limit on every step
- Pausing an agent for a person's approval and resuming it after a restart
- Serving tools over MCP and securing them with OAuth 2.0
- Keeping security decisions in code instead of trusting the AI with them
- Testing an agent on what it actually did: the database state, the tools it called and its reply

**Where it lives:** It has its own repository. It runs locally with `docker compose up`; there is no public demo, because a public agent that can issue refunds invites abuse and spending.
- Code: [github.com/raguram-3398/Support-Agent](https://github.com/raguram-3398/Support-Agent)
