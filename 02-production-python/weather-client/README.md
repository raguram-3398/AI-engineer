# Weather Client

**What it does:** Enter a location's latitude and longitude and it fetches the current weather from a free public weather service (Open-Meteo): temperature, wind speed and a weather condition code. If the service is slow, unreachable or returns an error, you get a clear message instead of the program freezing or crashing.

**Why it's here:** My first program that talks to an outside service over the internet. It never waits forever — every request has a 10-second time limit — and the data that comes back is checked against an expected shape before it's used. Both habits carry into every AI project, where the outside service is the AI model.

**What I learned:**

- Calling web APIs
- Time limits on network calls
- Validating outside data before trusting it

**Run it:** `uv run python -m weather.main` · Tests: `uv run pytest` (2 passing)
