# Options Scenario Lab, hosted version

`index.html` is the whole app (one file). Put it on any static host.

## One-time setup
1. **Host it.** Easiest: put `index.html` in a GitHub repository, then connect the repository to Netlify, Vercel, Cloudflare Pages or GitHub Pages (all free). Each push then redeploys in about a minute. No repository? Drag the file into Netlify's "deploy manually" page.
2. **Tell Supabase the site address** (needed for the sign-up confirmation email). In the Supabase dashboard for the project: Authentication, URL Configuration. Set "Site URL" to the hosted address and add it under "Redirect URLs".
3. Open the site, create an account, paste an Alpha Vantage key into the Account box. Each person uses their own key and sees only their own saved data.

## Updating
Update the artifact source, then run `python3 build_hosted.py leap-lab.artifact-source.html index.html` and redeploy `index.html`.

## What was set up in Supabase
Project "alanfoosh's Project", new table `options_lab_user_data` (one row per user: key, saved tickers, watch list, cost basis) with row-level security so each person can read and write only their own row. The project's other tables are untouched.

## Known limits
- Each person's Alpha Vantage key is stored in their row (only they can read it) and in their browser.
- Not yet verified against the live Alpha Vantage web API from a hosted address: the options call with an `expiration` filter. The page filters by expiry itself if Alpha Vantage returns every expiry.
- A free Alpha Vantage key cannot read historical options or adjusted prices.
