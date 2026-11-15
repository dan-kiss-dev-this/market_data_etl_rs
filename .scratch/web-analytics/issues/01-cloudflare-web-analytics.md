# 01: Cloudflare Web Analytics

**What to build:** Render's free-plan dashboard only shows request counts, not visitors, pages, referrers or countries. Load the Cloudflare Web Analytics beacon on the site so those show in Cloudflare → Web Analytics. Load it only in production builds (`import.meta.env.PROD`) so local dev isn't counted. The beacon token is public by design (every visitor's browser downloads it), so it's committed in `frontend/src/analytics.ts`.

**Blocked by:** None (can start immediately)

**Status:** ready-for-agent

- [x] Failing test written first (`frontend/src/analytics.test.ts`)
- [x] Production builds add the beacon `<script>` with the site token to `<head>`
- [x] Dev builds add no beacon
- [x] README Deployment section says where visitor stats live
- [x] `npm test` and `npm run build` pass
- [ ] After deploy, visits show in Cloudflare → Web Analytics

## Comments
