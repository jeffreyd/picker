# Picker

A Django 6 web app for managing your trash picking and electronics resale workflow. Track items from the curb to the sale, including parts harvesting, repair orders, and model-specific notes.

## Setup

```bash
# Install dependencies (pyenv virtualenv "picker" is already configured)
pip install -r requirements.txt

# Run database migrations
python manage.py migrate

# Start the dev server
python manage.py runserver
```

Open http://127.0.0.1:8000/ in your browser.

### Optional: create an admin account

If you want access to the Django admin at `/admin/`:

```bash
python manage.py createsuperuser
```

---

## How it works

### Items

An **Item** is anything you pull from the trash — a computer, a TV, a monitor, etc.

| Field | Notes |
|---|---|
| Name | Short label (e.g. "Desktop tower" or use Make+Model) |
| Make / Model | e.g. "Dell" / "Dimension 8200" |
| Category | Computer, TV, Monitor, Phone… (you define these) |
| Acquired | Date you found it |
| Source | Where you found it — address, dumpster, curb, etc. |
| Condition | Unknown / Working / Working with Issues / Not Working / Parts Only |
| Status | Tracks lifecycle (see below) |
| Cost Basis | Usually $0; enter a dollar amount if you paid something |
| Notes | Free-form notes |

#### Item Lifecycle Statuses

```
Acquired → Testing → Repairing ─┐
                                 ├→ Listed → Sold
                    Parting Out ─┘
                    Donated
                    Disposed
```

You can change an item's status directly from the item detail page without leaving the page (HTMX-powered inline update).

#### Item Detail Page

The item detail page is your central hub for a piece of gear. From here you can:

- See a **profit summary** (revenue − cost basis − parts ordered)
- Add **harvested parts** (components you pulled from this item)
- Add **repair parts** (components you used to fix this item)
- Add **parts orders** (things you bought to repair it)
- Track **eBay auctions** for this item and convert them to sales
- Record **sales** (when you sell it or parts from it)
- Jump to **model notes** for that make/model

---

### Parts

A **Part** is any component, whether pulled from an item or ordered separately.

- **Source Item** — the item it was pulled from (if harvested)
- **Used In Item** — the item it was installed into (if used for a repair)
- A part can have neither (e.g., a bare component you have in stock) or both

Parts have their own lifecycle: **Available → Used in Repair / Sold / Discarded**

When you record a sale and link it to a part, the part's status is automatically set to Sold.

---

### Orders

An **Order** represents a purchase you made to get parts for a repair (eBay, Amazon, AliExpress, etc.).

- Link an order to a specific **Item** so costs roll up into that item's profit calculation
- Orders with status **Received** are included in the item's cost basis for profit math
- Mark as Received — the received date is set automatically on status change

Orders have statuses: **Ordered → Shipped → Received** (or Returned / Cancelled)

---

### Sales

A **Sale** records money you received. You can link it to:

- An **Item** (sold the whole thing)
- A **Part** (sold a component)
- Or just enter a free-form **Description** (for miscellaneous sales)

Enter the **sale price** and any **fees** (eBay fees, shipping, etc.) separately — the app tracks net (price − fees) and rolls it into item profit calculations.

When you save a sale linked to an item or part, that item/part status is automatically set to **Sold**.

#### Supported Platforms
eBay · Facebook Marketplace · Craigslist · OfferUp · Local/Cash · Other

---

### Auctions

An **Auction** tracks an active eBay listing so you can monitor it and convert it to a sale record when it closes.

| Field | Notes |
|---|---|
| Title | Your eBay listing title |
| Item / Part | What you're selling (links to existing inventory) |
| eBay Item ID | The listing number — generates a clickable link to the live listing |
| Starting Bid | Your opening bid price |
| Buy It Now | BIN price, if set |
| Start / End Date | Listing dates |
| Final Price | The winning bid — fill in when the auction ends |
| Status | Active / Ended (Sold or Unsold) / Cancelled |

#### Auction Workflow

```
1. Create auction → link to an Item or Part
2. Auction runs on eBay
3. It sells → click "Convert to Sale"
4. Sale form opens pre-filled (title, item/part, eBay platform, final price)
5. Adjust sale price + add fees → Save
6. Auction marked "Ended — Sold", linked to the new Sale record
   Item/Part status automatically flipped to Sold
```

The **dashboard** shows a Live Auctions panel with a Convert button for each active auction. Each **Item detail page** also lists that item's auctions and has an Add Auction shortcut.

If an auction ends without selling, just edit it and set the status to **Ended — Unsold** — no sale record is created.

---

### Model Notes

Model Notes are your personal reference library — one note per make/model. Use them to record:

- RAM type and max capacity (e.g., "Dell Dimension 8200 uses PC800 RDRAM, max 2GB")
- Common failure modes
- Which screws/tools you need
- Compatible replacement parts / part numbers
- Upgrade options
- Service manual tips

When you're viewing an item, there's a link to search model notes for that make/model, and a quick link to create a note for it if one doesn't exist yet.

On the model note detail page, any items in your inventory that match that make/model are listed for quick cross-reference.

---

### Categories

Categories are simple labels (Computer, TV, Monitor, Phone, Printer, etc.) used to organize items and model notes. Manage them via **Add → Categories** in the nav.

---

## Navigation

The top navbar has:

- **Items** — your full inventory list
- **Parts** — all harvested and repair parts
- **Orders** — all parts orders
- **Sales** — all sales with running totals
- **Auctions** — all eBay auctions, active and past
- **Model Notes** — your reference library
- **Add ▾** — quick dropdown to create anything, including Categories

All list pages support **live search** (results update as you type, no page reload needed) and **status/platform filters**.

---

## Profit Calculation

For each item, the app shows:

```
Revenue (net)  = sum of (sale_price − fees) for all linked sales
Cost Basis     = what you paid for the item (usually $0)
Parts Cost     = sum of received orders linked to the item
─────────────────────────────────────────────────────────────
Profit         = Revenue − Cost Basis − Parts Cost
```

The dashboard shows your total net revenue across all sales.

---

## Django Admin

The Django admin at `/admin/` gives you a more powerful table-style interface for bulk editing and searching. You'll need a superuser account to access it (see Setup above).

---

## Tech Stack

- **Django 6** + SQLite
- **Bootstrap 5** (dark theme)
- **HTMX** for live search and inline status updates
- **django-crispy-forms** + **crispy-bootstrap5** for form rendering
- **WhiteNoise** for static file serving
