# RotorHazard Web App (plugin)

The new RotorHazard web interface — a fast, mobile-friendly single-page app built
with [Nuxt UI](https://ui.nuxt.com) — packaged as an ordinary RotorHazard plugin.
It runs on a **stock, unmodified RotorHazard** (RHAPI 1.9, current `main`): no core
files are changed, and the classic interface stays exactly as it is, one tap away.

- Opens at the timer's address (`/` → `/app/`); the classic pages keep their URLs
  (`/run`, `/marshal`, `/format`, `/settings`, ...).
- Uses the same Socket.IO events as the classic pages, so every timer feature and
  every plugin works: plugin panels appear on the matching app page, plugin pages
  (`blueprint_add`) open inside the app, plugin status bars (e.g. Sensor Top Bar)
  run on every page.
- Translated into all nine languages RotorHazard ships.
- Works offline (everything is bundled; no CDN), no Node.js needed on the timer.

The source of the app is in [`src/ui`](../src/ui) on this branch
([`webapp-plugin`](https://github.com/bob9/RotorHazard/tree/webapp-plugin)).

## Install

Any of these; then **restart the server**.

1. **Plugin manager, from a file** — download `rh_webapp.zip` (from a release, or
   build it with `plugin/package-plugin.sh`), then in RotorHazard open
   *Plugins › Install from file* and choose the zip.
2. **Copy the folder** — copy `plugin/rh_webapp` from this repository into the
   timer's data directory as `plugins/rh_webapp` (usually `~/rh-data/plugins/rh_webapp`):
   ```bash
   git clone -b webapp-plugin https://github.com/bob9/RotorHazard.git rh-webapp
   cp -r rh-webapp/plugin/rh_webapp ~/rh-data/plugins/
   ```
   The built app is committed inside the folder (`rh_webapp/webapp`), so a plain
   checkout or zip works without Node.js.
3. **Community plugin list** — once listed, install *RotorHazard Web App* from the
   Plugins page like any other plugin (the release asset is `rh_webapp.zip`).

To remove it, delete the plugin in *Plugins* (or remove the folder) and restart:
the timer is back to stock, nothing else to undo.

## Using it

| | |
|---|---|
| `/` | Opens the web app (or its first-run welcome on a new timer), unless set otherwise below |
| `/app/` | The web app |
| `/classic` | The classic home page (and remembers "classic" for this device) |
| `/interface/app?to=…`, `/interface/classic?to=…` | Switch this device to the other interface, opening the matching page |
| Classic menu (⋮) › **New interface** | Added to every classic page by the plugin |
| App: account menu or search (Ctrl+K) › **Classic interface** | Back to the classic page that matches the app page |

Each device remembers its own choice (cookie `rh_interface`). Devices that have not
chosen get the timer's default.

### Settings

- **Default interface** — *Settings › General › Default Interface* in the app, or
  *Settings › Web App › "Open the classic interface at this address"* on the classic
  Settings page. Stored in `config.json` as `UI.classicInterface` (the same item the
  core-integrated branch uses). Default: the new interface.

## What differs from the core-integrated branch (`webapp-redesign`)

The `webapp-redesign` branch builds the app into RotorHazard itself. As a plugin on a
stock server, each feature that needed a core change is handled like this:

| Feature | In the plugin |
|---|---|
| Serving the app at `/app/`, SPA fallback, long-lived caching of hashed assets | Reimplemented (plugin blueprint) |
| `/app-info`, `/app-auth`, `/app-first-run-done`, `/app-docs`, `/app-node-firmware`, `/app-database` | Reimplemented with the same names and answers, using RHAPI; the few facts RHAPI lacks (first-run status, restart flag, cluster, firmware updater, IMDTabler) are read in one guarded module, `compat.py`, which hides a feature rather than failing if RotorHazard changes |
| `/` opens the app | Reimplemented: a request hook redirects exactly `/` (GET/HEAD) to `/app/` unless the device chose classic or the timer's default is classic |
| Interface switch routes with open-redirect protection | Reimplemented unchanged (`/interface/app`, `/interface/classic`); targets are limited to known app pages, known classic pages and listed plugin pages |
| "New Interface" link in the classic menu | Reimplemented: the plugin adds a small script (`static/classic.js`) to classic-layout HTML responses, which adds the menu item and points the timer name at `/classic`. It does nothing inside the app |
| Plugin pages in the app's sidebar (`register_nav_link`, page discovery) | Reimplemented: discovered from the Flask URL map (parameterless GET routes of plugin blueprints that render HTML). Plugins can name or publish a page with `plugins.rh_webapp.register_nav_link(name, label, url, admin_only=False, order=0)` (import it inside a `try`); links registered with core's `rhapi.ui.register_nav_link` on servers that have it are used too |
| Plugin pages shown without the classic header/footer inside the app | Moved app-side: the app styles the (same-origin) frame itself |
| Site-wide plugin scripts (status bars) listed in `/app-info` | Reimplemented |
| Live updates of the event name and of settings on other devices | Reimplemented from RotorHazard's `OPTION_SET`/`CONFIG_SET` events (UI, TIMING and GENERAL settings only; never SECRETS, never secondary-timer passwords). One difference: the device that made the change also receives it back (the same value, so nothing changes) |
| Translations of the app's ~690 new strings in 9 languages | Shipped in `translations.json`, served at `/app-strings?lang=` and merged under RotorHazard's own table (RotorHazard's translation wins where both have a string) |
| Firmware facts on Update Nodes (`upd_file_info`) | Degrades: the app shows the server's own text description instead of the fact table |
| "Removed · restart to finish" badge for a plugin deleted since start-up | Reimplemented (`removed_plugins` in `/app-info`) |
| Classic pages accept the app's admin sign-in (no second login) | **Dropped.** It needs a change to RotorHazard's own authentication check (and its Socket.IO handshake check), which a plugin cannot make without patching core code. Switching to the classic pages as an admin shows the browser's login prompt once per browser session |
| `Settings › Default Interface` stored as core config | Kept, via a plugin setting stored in the same config item (`UI.classicInterface`) |

### Core fixes left for upstream

The core-integrated branch also fixes a few things in RotorHazard itself. They are not
needed by the plugin and are not part of this branch; they can be proposed upstream on
their own:

- Editing a race format other than the current one no longer replaces the current
  race's format (`on_alter_race_format`), and its message names the edited format.
- The "Race times adjusted" message names the heat as the interfaces show it.
- `config_update` never sends stored credentials (see below), and `set_config`
  broadcasts the change to other open displays (except SECRETS).
- `set_option` broadcasts event name/description changes.
- `check_bpillfw_file` also sends the firmware facts as data (`upd_file_info`).
- `rhapi.ui.register_nav_link` and a `removed` flag in the plugin list.
- The session cookie is `SameSite=Lax` and `HttpOnly`.
- Broken in-page anchors in `doc/RHAPI.md`, `doc/Event Setup Guide.md` and
  `doc/Tuning Parameters.md`.

### Security notes

- The app never needs, shows or stores the admin password beyond what stock RotorHazard
  does: it keeps the admin's credentials in the browser's local storage (like the classic
  pages' Basic Auth keeps them in the browser) and sends them as a Basic Authorization
  header to the admin endpoints and with the socket handshake.
- Admin endpoints (`/app-database`, `/app-node-firmware`, `/app-first-run-done`) use
  RotorHazard's own admin check and answer 401 without a `WWW-Authenticate` header.
  Like RotorHazard, the timer is open while no admin credentials are set or before first-run
  setup.
- Upstream behaviour to be aware of: on stock RotorHazard, `load_data` with
  `{type: 'config'}` returns any config item that is asked for — including
  `SECRETS.ADMIN_PASSWORD` — to any client. The app asks only for `SECRETS.ADMIN_USERNAME`;
  the core-integrated branch filters SECRETS out of `config_update`, which the plugin cannot
  do. The database viewer leaves out options whose name looks like a credential.

## Known limitations

- Admins switching to the classic pages get the browser's own login prompt (see above).
- Classic pages that don't use the classic layout (stream overlays, some plugin pages)
  don't get the "New interface" link.
- The Update Nodes page shows the server's text description of a firmware file rather
  than a fact table.
- `/app-strings` covers the app's own strings; strings that come from the server
  (messages, plugin labels) are translated by RotorHazard as usual.
- Requires RHAPI 1.9 (current RotorHazard `main`); older releases are not supported.

## Development

```bash
cd src/ui
npm install
npm run dev            # http://localhost:3000/app/ (proxies to a timer on :5000 that has the plugin installed)
npm run build          # builds into plugin/rh_webapp/webapp
npm run package-plugin # builds and zips: plugin/dist/rh_webapp.zip
```

`plugin/package-plugin.sh [output dir]` does the same from anywhere (`SKIP_BUILD=1` zips
the committed build). Commit `plugin/rh_webapp/webapp` together with app source changes.

Tests (stock server + plugin; run in their own process):

```bash
python -m pytest plugin/tests          # the plugin: endpoints, auth, '/' redirect, switching, SPA, packaging
cd src/tests && python -m pytest       # RotorHazard's own suite, unchanged
```

### Layout

```
plugin/
  rh_webapp/            the plugin (folder name = domain)
    manifest.json
    __init__.py         initialize(rhapi): blueprint, routes, settings, live updates
    pages.py            plugin page discovery, site scripts, interface switch targets
    compat.py           the guarded reads of server internals RHAPI doesn't offer
    translations.json   the app's own strings in RotorHazard's 9 languages
    static/classic.js   "New interface" link on classic pages
    webapp/             the built app (generated by `npm run build`)
  tests/                pytest
  package-plugin.sh     build + zip for release
```
