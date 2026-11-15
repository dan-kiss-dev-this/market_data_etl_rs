// Public by design: the beacon ships this token to every visitor's browser
const CF_BEACON_TOKEN = 'd0ed2b6d93aa44bf934180e1480e87de'

// Cloudflare Web Analytics; production builds only so local dev isn't counted
export function loadAnalytics(isProd: boolean) {
  if (!isProd) return
  const script = document.createElement('script')
  script.defer = true
  script.src = 'https://static.cloudflareinsights.com/beacon.min.js'
  script.dataset.cfBeacon = JSON.stringify({ token: CF_BEACON_TOKEN })
  document.head.appendChild(script)
}
