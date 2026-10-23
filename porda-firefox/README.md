# PordaAI for Firefox

Manifest V3 port of the PordaAI browser extension, built for Firefox 140+.

It detects and covers haram/NSFW content in images and videos on any webpage.
Detection runs either inside the extension (ONNX Runtime Web, WebGPU or WASM)
or, when the Porda AI desktop app is running, on the desktop app over a local
connection so the browser stays light.

## Requirements

- Firefox 140 or newer (desktop).
- Optional: the Porda AI desktop app for GPU-backed detection and lower browser load.

## Install (temporary, for development)

1. Open `about:debugging#/runtime/this-firefox`.
2. Click **Load Temporary Add-on...**.
3. Select `manifest.json` inside this folder.

Temporary add-ons are removed when Firefox restarts. Permanent installation goes
through an addons.mozilla.org (AMO) listing.

## Build a package for AMO

```bash
npx web-ext lint --source-dir porda-firefox
npx web-ext build --source-dir porda-firefox --artifacts-dir dist
```

The resulting zip in `dist/` is what gets uploaded to AMO.

## Differences from the Chromium build

| Area | Chromium build | Firefox build |
| --- | --- | --- |
| Background | service worker | background script (event page) |
| Offscreen detection | `chrome.offscreen` document | hidden same-origin `iframe` (`offscreen.html`) created by the background script |
| Manifest | `background.service_worker` | `background.scripts` + `browser_specific_settings.gecko` |

Firefox event pages have DOM access, which is why the hidden iframe replaces the
Chrome-only offscreen API. Everything else (content script, popup, cover styles,
i18n, IndexedDB result cache, PC app bridge) is shared with the Chromium build.

## Desktop app integration

When the desktop app is running, the extension uses it instead of the in-browser
engine:

- `ws://127.0.0.1:56357/ws` - sends frames for detection, receives results.
- `http://127.0.0.1:56357/health` - connection probe for the popup.
- `http://127.0.0.1:56357/api/settings` - pushes detection/cover settings.
- `pordaai://open` - launches the app from the popup.

If the app is not reachable, the extension falls back to the bundled ONNX model
(`offscreen/model/porda.onnx`) so protection keeps working.

## Privacy

- No account, no telemetry, no remote inference.
- Page images are processed locally. Data leaves the page only to the extension's
  own background context, and to `127.0.0.1` when the desktop bridge is connected.
- `data_collection_permissions` in the manifest declares `none`.

## Layout

```
manifest.json         MV3 manifest with gecko settings
background.js         event page: routing, PC app bridge, action/badge state
content.js            page scanning, capture, cover overlays
popup.html/js/css     toolbar UI
offscreen.html/js     ONNX Runtime Web inference (WebGPU, WASM fallback)
offscreen-cache.js    IndexedDB cache of past detections
reload-prompt.js      "reload to protect this tab" prompt after install/update
welcome.html/js/css   first-run and update pages
_locales/             11 locales (en, ar, bn, fa, fr, hi, id, ms, ru, tr, ur)
offscreen/model/      porda.onnx
offscreen/ort/        ONNX Runtime Web runtime files
```

## License

AGPL-3.0, same as the Porda AI desktop app.
