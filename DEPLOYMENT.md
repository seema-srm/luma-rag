# Deploy Luma on Streamlit Community Cloud

The repository includes public snapshot settings at `deployment/ai.json` for the existing AI Pinecone namespace. They contain no API keys. Local `.luma/ai.json` takes priority when present. Ingestion always writes locally and does not overwrite the checked-in demo snapshot.

1. Open https://share.streamlit.io and sign in using the GitHub account that owns this repository.
2. Choose Create app and deploy from GitHub.
3. Select repository `seema-srm/luma-rag`, branch `main`, and main file `app.py`.
4. In Advanced settings, choose Python 3.12 and paste root-level TOML secrets using `deployment/secrets.example.toml` as the template. Replace the two key placeholders and model-ID placeholder privately with the values from the working local `.env`. Use quotes around every value; do not paste dotenv syntax or add section headers. Keep the same embedding model as the snapshot.
5. Deploy and wait for dependency installation. Record the actual URL assigned by the host.
6. Ask a few public AI questions, inspect sources, test both explanation styles, check latest-first order and clear conversation, then test the URL in a signed-out/private browser window.

Do not paste API keys in GitHub, chat, screenshots, or public logs. Actual keys belong only in the host's Secrets settings. Visitors use the deployment owner's credits. Provider availability and quotas still apply. No live cloud/provider test was performed during offline preparation.

If startup fails, check build logs for dependency errors. If it opens but requests fail, check privately stored keys, the exact working model ID, provider credits, and access to the remote index/namespace. The existing diagnostic script prints only safe response metadata; it is an optional live check and uses credits.

After adding/replacing/removing local documents and successfully re-indexing, copy the public `.luma/ai.json` to `deployment/ai.json` and commit it together with the updated public documents. Never publish a private collection reference. The old cloud snapshot otherwise remains active.

Official guides:
- https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/deploy
- https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/secrets-management
