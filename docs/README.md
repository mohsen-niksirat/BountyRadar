# GitHub Pages

This site is a **static product page + interactive sample demo** for Bounty Radar Pro.

It does **not** run the Python scanner. Live scanning needs the local app:

```bash
git clone https://github.com/mohsen-niksirat/BountyRadar.git
cd BountyRadar
# Windows: double-click Bounty Radar.bat
python bounty_radar.py
```

## Enable Pages (once)

1. Repo **Settings → Pages**
2. **Source**: GitHub Actions  
   (or *Deploy from a branch* → `main` / `/docs`)
3. After the first push to `docs/`, the site is at:
   `https://mohsen-niksirat.github.io/BountyRadar/`

The workflow `.github/workflows/pages.yml` deploys `docs/` automatically on every push to `main`.
