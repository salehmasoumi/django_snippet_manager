# ARCHITECTURE.md — Code Snippet Manager

This document records the architecture decisions made for this project and
maps each one back to `PROJECT_PATTERNS.md`, Mohammad's pattern library
distilled from six prior Django projects.

## Decision table

| Area | Decision | Source |
|---|---|---|
| Settings folder name | `config` | New — preferred name per patterns doc §1 |
| Project skeleton | apps: `accounts`, `snippets`, `favorites`, `dashboard`, `api` | Reuse — §1 app layout |
| `.env` + `python-dotenv`, `DB_ENGINE` switch | Reused verbatim | Reuse directly — §2 |
| `LOGIN_URL` / `LOGIN_REDIRECT_URL` / `LOGOUT_REDIRECT_URL` explicit | Reused | Reuse directly — §2, §13 (`next` bug) |
| WhiteNoise for static files | Reused, but gated to `DEBUG=False` only | Reuse **with fix** — manifest storage broke Django's test runner in dev/test mode |
| Auth model | Pattern B: `AbstractUser` + separate `Profile` (signal + `get_or_create` guard) | Reuse with fix — see bug below |
| Password reset | Manual `PasswordResetTokenGenerator` + `urlsafe_base64_encode/decode`, no Django built-in views | Reuse directly — §3 |
| Views | 100% function-based views | Reuse directly — §4 |
| Ownership-chain helper (`_get_owned_snippet`) | Reused | Reuse directly — §4 |
| `@require_POST` on the favorite toggle | Applied from the start | Reuse with fix — §4, §13 (GET-toggle bug) |
| Filter form with user-scoped queryset set in `__init__` | Reused (`SnippetFilterForm`) | Reuse directly — §5 |
| Slug auto-generation with uniqueness counter | Reused (`Snippet.save()`) | Reuse directly — §6 |
| URL ordering: `edit/`, `delete/` before `<slug>/` | Applied from the start | Reuse with fix — §7, §13 |
| DRF: central `api` app with router only, `serializers.py`/`viewsets.py` in domain apps | Reused | Reuse directly — §8 |
| `get_queryset()` scoped to `request.user` | Reused, extended to public-or-owned logic | Reuse with fix — §8 |
| Dashboard app with no models, aggregates via `annotate`/`Count(filter=Q(...))` | Reused | Reuse directly — §9 |
| CSS design tokens (raw palette → semantic layer, glass-card aggregated selector) | Reused, repainted for a dark "developer" theme | Reuse with fix (palette only) — §11 |
| JS IIFE pattern, guarded per-feature | Reused, repurposed for the Copy Code button | Reuse directly — §12 |
| Tag model + M2M on Snippet | New | Not present in any prior project |
| Private/public visibility + `is_visible_to()` guard | New | Not present in any prior project — see security note below |
| Syntax highlighting: Pygments (server-side) + Prism.js (client-side) | New | Explicit requirement, confirmed with Mohammad |
| Version History app | Deferred | Explicitly scoped out of MVP per requirements |

## Bugs found and fixed proactively

1. **Duplicate-empty-email `UNIQUE` constraint** (new finding, not in the
   original checklist). `EmailField(unique=True, blank=True, null=True)`
   alone is *not* sufficient: Django's `UserManager.create_user()`
   normalizes a missing email to `''`, not `None`, so two users registered
   without email collide on `''`. Fixed by overriding `User.save()` to
   coerce falsy email values to real `NULL` before saving. This is a
   sharper version of the bug already flagged in `PROJECT_PATTERNS.md`
   §13 — the previous fix (`null=True`) was necessary but not sufficient.
2. **GET-based favorite toggle** — prevented from the start with
   `@require_POST`, per the recurring bug documented in §13.
3. **URL ordering** — `snippets/urls.py` and `accounts/urls.py` register
   specific paths (`edit/`, `delete/`, `profile/<username>/`) before the
   generic catch-all `<slug>/` pattern.
4. **Private content leakage** — this is a genuinely new risk class (prior
   projects had no private/public split). `Snippet.is_visible_to(user)` is
   checked in the web view (404 for non-owners), in the favorite-toggle
   view, and in the DRF `get_queryset()`/permission class, so it's enforced
   at three independent layers rather than relying on the UI to just hide
   a button.
5. **WhiteNoise manifest storage breaking local dev/tests** — new finding.
   `CompressedManifestStaticFilesStorage` requires `collectstatic` to have
   run, which broke `manage.py test` and local `runserver` before
   `collectstatic`. Fixed by only using the manifest storage when
   `DEBUG=False`.

## Data model

```
User (AbstractUser)
  └─ Profile (1:1, created via signal + get_or_create guard)

Language (seeded: Python, Django, JavaScript, HTML, CSS, C++, SQL, Bash)
Tag (created ad hoc by users)

Snippet
  - owner        → User (FK)
  - language     → Language (FK, PROTECT)
  - tags         → Tag (M2M)
  - visibility   public | private
  - slug         unique, auto-generated
  - created_at / updated_at

Favorite
  - user    → User (FK)
  - snippet → Snippet (FK)
  - unique_together(user, snippet)
```

## Build phases (as delivered)

1. **MVP** — auth, snippets CRUD, visibility, dashboard, syntax highlighting, Copy Code
2. **Search** — `Q`-based search across title/description/code/language/tag
3. **Favorites** — dedicated app, POST-only toggle
4. **API** — DRF router, ownership-scoped viewsets, matching web permissions
5. **Version History** — deferred; `Snippet` and app boundaries were kept clean
   (no fields baked in that would block adding a `SnippetVersion` model with an
   FK to `Snippet` later, mirroring how `progress_tracking` was isolated in
   the roadmap platform project)

## Testing

21 automated tests in `snippets/tests.py` covering: slug generation/uniqueness,
profile signal, visibility rules (model + view + API, for both anonymous and
authenticated non-owners), ownership enforcement on edit, search/filtering,
favorite toggle (POST-only, login-required, create/remove, blocked on private
snippets), and API permission/ownership scoping including the 403-on-edit and
private-isolation cases.

Run with:
```
python manage.py test
```
