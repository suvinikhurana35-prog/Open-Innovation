# Deploying JanNiti — Vercel (frontend) + Render (backend), free tier

Written for someone who has a GitHub account but has never pushed code.
Follow in order. Copy-paste the commands exactly.

Your setup: FREE live link (RAG off, KB-served) + RAG kept for LOCAL evaluation.

---------------------------------------------------------------------------
## IMPORTANT FIRST: the free-tier problem, and how this pack solves it
---------------------------------------------------------------------------
Render's free tier gives 512 MB RAM. Your original backend loads a ~400 MB AI
model + ChromaDB and WILL crash there.

This pack adds "LITE MODE": set DISABLE_RAG=1 and the backend skips the heavy
model entirely and serves every scheme from backend/data/kb/*.md (which is what
it already does for all 18 schemes). It uses a small requirements-lite.txt.
Result: it fits comfortably in the free tier.

You lose nothing that you use today. The AI (Anthropic) still powers chat,
translations, and comparisons.

---------------------------------------------------------------------------
## STEP 0 — Protect your API key (do this first!)
---------------------------------------------------------------------------
Your backend/.env contains a real API key. It must NEVER go to GitHub.

1. The included .gitignore already excludes .env — good.
2. Because you pasted that key in a chat, ROTATE IT:
   console.anthropic.com -> API Keys -> delete old key -> Create Key -> copy new.
   You will paste the NEW key into Render's dashboard later (not into any file).

---------------------------------------------------------------------------
## STEP 1 — Install Git (if you don't have it)
---------------------------------------------------------------------------
Download: https://git-scm.com/download/win  -> install with all defaults.
Then close and reopen your terminal, and check:

    git --version

If it prints a version, you're good.

---------------------------------------------------------------------------
## STEP 2 — Create an empty GitHub repository
---------------------------------------------------------------------------
1. Go to github.com -> click "+" (top right) -> "New repository".
2. Name it:  janniti
3. Choose Public (or Private).
4. Do NOT tick "Add a README" / .gitignore / license. Leave it empty.
5. Click "Create repository".
6. Leave that page open — you'll need the URL, which looks like:
       https://github.com/YOUR-USERNAME/janniti.git

---------------------------------------------------------------------------
## STEP 3 — Push your project to GitHub
---------------------------------------------------------------------------
Open a NEW terminal (not one running a server) and run these ONE AT A TIME.
Replace YOUR-USERNAME with your real GitHub username.

    cd "C:\Users\SUMI AIMS\Downloads\JanNiti-clean-with-UI"

    git init
    git add .
    git commit -m "JanNiti: initial commit"
    git branch -M main
    git remote add origin https://github.com/YOUR-USERNAME/janniti.git
    git push -u origin main

A browser window may pop up asking you to sign in to GitHub — do it.

SANITY CHECK: refresh your GitHub repo page. You should see backend/ and
frontend/ folders. Click into backend/ — you should see data/kb/ with 18 .md
files, and you should NOT see a .env file. If you see .env, stop and tell me.

---------------------------------------------------------------------------
## STEP 4 — Deploy the BACKEND on Render
---------------------------------------------------------------------------
1. Go to render.com -> Sign up with GitHub -> authorise it.
2. Click "New +" -> "Web Service".
3. Connect your "janniti" repo.
4. Fill in these settings EXACTLY:
       Name:            janniti-backend
       Root Directory:  backend
       Runtime:         Python 3
       Build Command:   pip install -r requirements-lite.txt
       Start Command:   uvicorn main:app --host 0.0.0.0 --port $PORT
       Instance Type:   Free
5. Scroll to "Environment Variables" and add these (click Add for each):
       DISABLE_RAG            = 1
       AUTO_INGEST_ON_START   = 0
       LLM_PROVIDER           = anthropic
       ANTHROPIC_MODEL        = claude-haiku-4-5-20251001
       ANTHROPIC_API_KEY      = (paste your NEW key from Step 0)
       CORS_ORIGINS           = *
       PYTHON_VERSION         = 3.11.9
6. Click "Create Web Service". Wait ~5-10 minutes for the first build.
7. When it says "Live", copy your backend URL. It looks like:
       https://janniti-backend.onrender.com
8. TEST IT: open  https://janniti-backend.onrender.com/health  in a browser.
   You should see JSON with "status": "healthy". (rag_available will be false —
   that's correct in lite mode.)

NOTE: on the free tier the backend SLEEPS after ~15 min of no traffic. The next
request takes ~50 seconds to wake it. That's normal for free hosting.

---------------------------------------------------------------------------
## STEP 5 — Deploy the FRONTEND on Vercel
---------------------------------------------------------------------------
1. Go to vercel.com -> Sign up with GitHub -> authorise.
2. Click "Add New..." -> "Project" -> import your "janniti" repo.
3. IMPORTANT settings:
       Framework Preset: Next.js  (auto-detected)
       Root Directory:   frontend      <- click "Edit" and set this!
4. Expand "Environment Variables" and add ONE:
       Name:  NEXT_PUBLIC_API_URL
       Value: https://janniti-backend.onrender.com     <- your Render URL, no trailing slash
5. Click "Deploy". Wait ~2-3 minutes.
6. You get a live link like:  https://janniti.vercel.app

---------------------------------------------------------------------------
## STEP 6 — Lock down CORS (recommended, after it works)
---------------------------------------------------------------------------
Back in Render -> your service -> Environment -> change:
       CORS_ORIGINS = https://janniti.vercel.app
Then "Manual Deploy" -> "Deploy latest commit". This stops other sites from
using your backend (and your API credits).

---------------------------------------------------------------------------
## TROUBLESHOOTING
---------------------------------------------------------------------------
* Render build fails with "out of memory"
    -> You forgot DISABLE_RAG=1, or the Build Command isn't
       requirements-lite.txt. Fix both, then Manual Deploy.

* Frontend loads but says "Failed to fetch explanation"
    -> NEXT_PUBLIC_API_URL is wrong/missing on Vercel, or the backend is
       asleep (wait 50s and retry), or CORS_ORIGINS doesn't include your
       Vercel URL.

* Backend logs: "No LLM key configured"
    -> ANTHROPIC_API_KEY not set in Render's Environment Variables.

* "ModuleNotFoundError: No module named 'chromadb'"
    -> That is FINE in lite mode; the code falls back automatically. If the
       app still crashes, confirm DISABLE_RAG=1 is set.

* Explainer is slow on the live site
    -> Make sure backend/data/translations/ got committed to GitHub (that's
       your speed cache). Check on GitHub: backend/data/translations should
       have files. If it's missing, it was gitignored — tell me.

---------------------------------------------------------------------------
## WHAT GOT ADDED FOR DEPLOYMENT (files in this pack)
---------------------------------------------------------------------------
  backend/services/rag_stub.py        NEW - no-op RAG for lite mode
  backend/services/rag_service.py     safe imports + lite-mode fallback
  backend/services/data_service.py    safe import of heavy pdf/langchain deps
  backend/requirements-lite.txt       NEW - small dependency list
  render.yaml                         NEW - Render config (optional convenience)

Your app behaves identically; it just no longer *requires* the heavy ML stack.
Locally you can still run the full version (RAG on) — lite mode only activates
when DISABLE_RAG=1 or when those packages aren't installed.
