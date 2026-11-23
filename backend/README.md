# FutureFace AI backend

FastAPI server for real OpenAI image edits. Never put OPENAI_API_KEY in GitHub Pages or committed files.

Deploy with Render Blueprint using repository render.yaml. Set OPENAI_API_KEY as a secret in Render. The API exposes GET /health and POST /api/transform multipart fields photo and timeline.

This is a limited private-beta prototype, NOT production-ready. In-memory limits reset on restart, client IP handling behind proxies needs a trusted edge, and public access can incur costs. Before public launch implement authentication, persistent quotas, bot mitigation, moderation/abuse monitoring, and billing caps. Images are processed in memory, not deliberately stored by this application; provider processing and retention policies still apply.
