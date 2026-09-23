# MasjidMediaBrand

Full dark Masjid Media theme for the FreeScout agent dashboard, login page,
and outgoing customer-reply emails. Ships as hooks and CSS only — it never
edits a core file.

## Install

```
php artisan module:enable MasjidMediaBrand
php artisan freescout:module-install masjidmediabrand
php artisan freescout:clear-cache
```

## How it works

Everything is registered in `hooks()` (`Providers/MasjidMediaBrandServiceProvider.php`) via FreeScout's Eventy hooks: logo, favicon, theme-color, login banner, the Fraunces/Outfit `<link>` (`layout.head`), and two stylesheets appended to the `stylesheets` array:

- `Public/css/theme-base.css` — **generated, do not edit.** `Tools/build_theme_base.py` walks every rule in FreeScout's core CSS (bootstrap, style.css, select2, summernote, flatpickr, datatables, ...), keeps the colour declarations, maps each colour onto the Masjid Media palette, and re-emits them scoped under `body.mm-theme`. This is what keeps every screen dark without hand-picking selectors.
- `Public/css/theme.css` — the hand-tuned layer on top: typography, the navbar matching the website header, headings, buttons, and the light "paper" card that email bodies (`.thread-content`) and the editor sit on, since customer emails carry inline colours written for a white page.

Both files are scoped under `body.mm-theme` (added via the `body.class` action), so disabling the module is an instant, full revert:

```
php artisan module:disable MasjidMediaBrand
php artisan freescout:clear-cache
```

Optional `.env`: `BRAND_SOURCE_URL=` — public repo of this module; the footer "Source" link is hidden until set.

## After a FreeScout upgrade

Regenerate the base layer from the new core CSS, then walk the checklist below:

```
pip install tinycss2
python Modules/MasjidMediaBrand/Tools/build_theme_base.py
php artisan freescout:clear-cache
```

## Known gap

`reply_email.header` / `reply_email.footer` only render in the agent-reply
template (`emails/customer/reply_fancy.blade.php`). FreeScout's automatic
auto-reply email uses a separate template
(`emails/customer/auto_reply.blade.php`) that does not call these hooks, so
the auto-reply stays unbranded. Branding it would mean overriding that core
view, which is out of scope for this module.

## Upgrade checklist

After regenerating, walk through:

- Dashboard, a mailbox conversation list, and a conversation containing an
  HTML-heavy email (confirm the message body still renders on the light
  "paper" card, not black-on-black or white-on-white)
- New conversation / reply editor (Summernote toolbar and frame)
- Settings, Users, System Status and Tools pages
- A dropdown menu, a modal, and the Select2 and flatpickr widgets
- The login page and its banner

If something looks broken, disable the module first
(`php artisan module:disable MasjidMediaBrand`) to confirm it's this theme
and not something else, then fix the relevant selector in `theme.css`.

## License

AGPL-3.0, the same licence as FreeScout. See [LICENSE](LICENSE).

The Masjid Media name and logo (`Public/img/`) are not covered by that licence and may not be used to brand other products or services.
