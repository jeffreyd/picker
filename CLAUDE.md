# Picker — Claude Code Guide

## Project Overview

Django 6 inventory management app for trash picking and electronics resale work. Tracks items from acquisition through repair, parts harvesting, eBay auctions, and sales.

Single Django app: `inventory`. No SPA frameworks — Django templates only. HTMX is acceptable for interactivity enhancements.

## Environment

- Python 3.14.2 via **pyenv**, virtualenv named `picker`
- **Always prefix bash commands** with pyenv init when running management commands or tests:
  ```
  export PYENV_ROOT="$HOME/.pyenv" && export PATH="$PYENV_ROOT/bin:$PYENV_ROOT/shims:$PATH" && eval "$(pyenv init -)"
  ```
- Database: SQLite (`db.sqlite3`, gitignored)
- Run dev server: `python manage.py runserver`
- Run migrations: `python manage.py migrate`

## Running Tests

```bash
export PYENV_ROOT="$HOME/.pyenv" && export PATH="$PYENV_ROOT/bin:$PYENV_ROOT/shims:$PATH" && eval "$(pyenv init -)" && coverage run manage.py test inventory && coverage report --include="inventory/*"
```

Target: **≥85% coverage**. Current baseline: 99% (238 tests).

## Dependencies

See `requirements.txt`. Key packages:
- `django==6.0.3`
- `django-crispy-forms` + `crispy-bootstrap5` — all forms use `FormHelper`
- `whitenoise` — static file serving
- HTMX 2.0.4 and Bootstrap 5 (dark theme) loaded via CDN in `base.html`

## Project Structure

```
picker/          # Django project config (settings, urls, wsgi)
inventory/       # Main app
  models.py      # All data models
  views.py       # All CRUD views + special endpoints
  urls.py        # URL patterns (app_name='inventory')
  forms.py       # ModelForms with crispy FormHelper
  admin.py       # All models registered
  templatetags/
    inventory_tags.py   # get_item (dict filter), currency (formatter)
  templates/inventory/
    base.html            # Nav + Bootstrap/HTMX CDN includes
    dashboard.html       # Summary cards, status breakdown, live auctions
    items/               # list, detail, form, partials
    parts/               # list, detail, form, partials
    orders/              # list, detail, form, partials
    sales/               # list, detail, form, partials
    auctions/            # list, detail, form, convert, partials
    model_notes/         # list, detail, form, partials
    categories/          # list, form
    confirm_delete.html  # Shared delete confirmation
  test_fixtures.py   # InventoryFixtures mixin — use this in all new tests
  test_models.py
  test_forms.py
  test_tags.py
  test_views.py
```

## Data Models

- **Category** — item categories (name)
- **Item** — core tracked item with status lifecycle: `acquired → testing → repairing → parting_out → listed → sold → donated → disposed`
- **Part** — harvested from an Item, optionally used in another Item
- **PartOrder** — ordered parts (eBay, Amazon, AliExpress, other); auto-sets `received_date` on status change to received
- **Sale** — sale record linked to Item or Part; net_amount = sale_price - fees
- **Auction** — eBay auction linked to Item or Part; `auction_convert` view creates a Sale and marks auction `ended_sold`
- **ModelNote** — reference notes for a specific make+model (unique together)

Item properties: `display_name`, `total_parts_cost`, `total_revenue`, `profit`
Auction properties: `is_active`, `ebay_url`
PartOrder property: `supplier_display`

## Key Conventions

### Forms
All forms use `django-crispy-forms` with `crispy-bootstrap5`. Every form must have a `FormHelper` set in `__init__`. Check existing forms in `forms.py` before adding new ones.

### Views
- List views support HTMX live search: check `request.headers.get('HX-Request')` and return `_table.html` partial
- HTMX status update endpoints return a rendered badge partial (no redirect)
- Standard CRUD pattern: list, detail, create, update, delete (confirm_delete.html)

### Templates
- All templates extend `inventory/base.html`
- Partial templates are prefixed with `_` (e.g., `_table.html`, `_status_badge.html`)
- Bootstrap 5 dark theme throughout

### Tests
- Use `InventoryFixtures` mixin from `test_fixtures.py` — call `self.make_fixtures()` in setUp
- HTMX requests: pass `HTTP_HX_REQUEST='true'` to the test client
- Test files are flat in `inventory/` (not in a subdirectory) — do NOT create an `inventory/tests/` package, it conflicts with `inventory/tests.py`

### Migrations
- Run `python manage.py makemigrations` after any model changes
- Migration files go in `inventory/migrations/`

## Adding New Features

1. Add/update models in `models.py`, run `makemigrations`
2. Add form in `forms.py` with crispy `FormHelper`
3. Add views in `views.py` following existing CRUD pattern
4. Wire URLs in `urls.py`
5. Create templates under `inventory/templates/inventory/<resource>/`
6. Register model in `admin.py`
7. Add tests in a new `inventory/test_<feature>.py` file or extend existing test files
8. Verify coverage stays ≥85%
