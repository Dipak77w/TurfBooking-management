# ⚽ MiniTurf Arena - Commercial Turf Booking & Management Platform

A modern, responsive, commercial-grade **Turf Booking and Facility Management Web Application** built with **Python Django 6.1**, **SQLite**, and **Bootstrap 5.3**. Designed specifically for sports arenas, players, and turf operators across **Chhatrapati Sambhajinagar, Maharashtra**.

---

## 🌟 Key System Features

### 1. Two Separate Login Portals (Role-Based Authentication)
- **Player / Customer Portal (`/accounts/customer/login/`)**:
  - Customer registration with full name, email, phone, and password.
  - Interactive player dashboard with upcoming matches, completed history, and cancelled bookings.
  - Printable match receipts and invoices.
  - Post-match review and 1–5 star ratings.
  - 30-minute cancellation window with instant slot release.
- **Turf Owner / Admin Portal (`/accounts/owner/login/`)**:
  - Owner registration with arena business details and custom UPI settings.
  - Real-time KPI statistics: Total Turfs, Today's Matches, Pending Verifications, Verified Revenue.
  - Interactive **Chart.js** analytics: Daily Bookings (7-Day Trend), Monthly Revenue, and Status Distribution.
  - Full Turf CRUD: Add, edit, delete turfs, manage opening/closing hours, slot duration, and prices.
  - Multi-photo gallery uploader.
  - Slot Blocking: Block full days or specific hours for maintenance or tournaments.
  - Payment Verification: Inspect UPI UTR reference IDs and payment screenshots to approve or reject bookings.
  - Review moderation: Show/hide or delete player reviews.
  - Strict role isolation: Customers cannot access admin routes; owners manage only their own turfs.

### 2. High-Contrast Light Theme UI Architecture
- **Strictly Light Theme**: Clean `#F5F8F6` background, crisp `#FFFFFF` cards, dark navy `#102A43` headings, and primary sports green `#168447`.
- **Zero Dark-on-Dark or White-on-White issues**: High WCAG contrast ratios on all text, inputs, buttons, badges, tables, and dropdowns.
- Fully responsive across desktop, tablets, and mobile smartphones.

### 3. Dynamic Slot Booking & Concurrency Protection
- Slots are generated dynamically based on turf operating hours (e.g. 06:00 AM to 11:00 PM).
- Slots in the past (for today's date) are automatically locked.
- **Zero Double-Bookings**: Atomic database transactions (`transaction.atomic()`) with row-level locks (`select_for_update`) ensure two users can never confirm the same slot simultaneously.

### 4. 30-Minute Cancellation Policy Engine
- Players can cancel bookings only **before 30 minutes** of the scheduled start time.
- If less than 30 minutes remain, the cancellation button is disabled with a clear explanatory policy badge.
- When cancelled, the slot is immediately released for other players to book.

### 5. Manual UPI QR Code Payment System
- No fake automated payments.
- Turf owners configure their real **UPI ID** (e.g. `citysports@okhdfcbank`) and upload their **UPI QR scanner image**.
- Checkout page shows the QR code, accepted UPI apps (GPay, PhonePe, Paytm, BHIM), and total price.
- Customer scans, pays, enters the 12-digit UPI UTR reference number, and optionally uploads a payment screenshot.
- Payment is placed in **Pending Verification** until the turf owner verifies it in their dashboard.

---

## 🏟️ 3 Realistic Demonstration Turfs (Chhatrapati Sambhajinagar)

| Venue Name | Locality & City | Sports | Hourly Rate | Operating Hours |
|---|---|---|---|---|
| **City Sports Arena** | CIDCO Cannaught Place, Chhatrapati Sambhajinagar | Football, Box Cricket, Cricket, Badminton | ₹900 / hr | 06:00 AM – 11:00 PM |
| **Champion Box Cricket Turf** | Beed Bypass Road, Chhatrapati Sambhajinagar | Box Cricket, Cricket | ₹750 / hr | 06:00 AM – 11:30 PM |
| **Greenfield Football Turf** | Seven Hills, Jalna Road, Chhatrapati Sambhajinagar | 7v7 & 5v5 Football | ₹1,100 / hr | 05:30 AM – 11:00 PM |

*Note: All three venues are marked with a "Demonstration Listing" badge for college mini-project review.*

---

## 🔑 Demonstration Login Credentials

| Role | Username | Password | Purpose |
|---|---|---|---|
| **Customer (Player)** | `customer` | `cust1234` | Browse turfs, pick slots, submit UPI UTR, cancel, view receipts |
| **Turf Owner (Admin)** | `owner` | `owner1234` | Turf dashboard, verify payments, block slots, view charts |
| **Superuser** | `admin` | `admin1234` | Full Django Administration (`/admin/`) |

---

## 🚀 Quick Setup & Local Execution Guide

### 1. Requirements
- Python 3.10+ (Tested on Python 3.14)
- Pip

### 2. Navigate to Project Directory
```powershell
cd c:\Users\dell\OneDrive\Desktop\MINITURF
```

### 3. Install Dependencies
```powershell
python -m pip install -r requirements.txt
```

### 4. Run Database Migrations
```powershell
python manage.py migrate
```

### 5. Seed Demonstration Data (Turfs, Accounts & Media)
```powershell
python manage.py seed_demo_data
```
*This command automatically populates the 3 demonstration turfs, sample bookings, payments, reviews, and generates high-res turf pitch graphics and UPI QR codes.*

### 6. Run the Development Server
```powershell
python manage.py runserver
```
Open your browser and navigate to: **`http://127.0.0.1:8000/`**

---

## 🧪 Running Automated Test Suite
To verify booking concurrency, role-based authentication, 30-minute cancellation locks, and UPI verification:
```powershell
python manage.py test
```
All 10 unit and integration tests will execute and report `OK`.

---

## ⚙️ How to Upload / Replace UPI QR Code
1. Log in with Turf Owner credentials (`owner` / `owner1234`).
2. Go to **UPI & Settings** (`/accounts/owner/settings/`).
3. Under **UPI QR Code Payment Configuration**:
   - Update your **UPI ID** (e.g. `yourname@okhdfcbank`).
   - Select your custom QR scanner image file (PNG, JPG, or JPEG) and click **Save All Settings**.
4. The new QR code will now appear dynamically on checkout for all customers booking your turfs.

---

## 📁 Project Directory Structure
```
MINITURF/
│   manage.py
│   requirements.txt
│   README.md
│   db.sqlite3
│
├───turfbooking/            # Core Project Settings
│       settings.py
│       urls.py
│       wsgi.py
│       asgi.py
│
├───accounts/               # Role-based Auth (Customer & Owner)
│       models.py           # UserProfile (role, phone, business, upi_id, upi_qr_image)
│       forms.py            # Customer & Owner registration/profile forms
│       decorators.py       # @customer_required, @owner_required
│       views.py            # Login, registration, profile & UPI settings
│       urls.py
│       tests.py
│
├───turfs/                  # Turf Venue Management & Dynamic Slots
│       models.py           # Turf, TurfImage, BlockedSlot, Review
│       forms.py            # TurfForm, TurfImageForm, BlockedSlotForm, ReviewForm
│       slot_utils.py       # Dynamic hourly slot generator with past/blocked checks
│       views.py            # Turf list, detail, slots API, CRUD, photo/slot manager
│       urls.py
│       tests.py
│
├───bookings/               # Booking Engine, Payment & Cancellation
│       models.py           # Booking, Payment
│       forms.py            # BookingForm, PaymentSubmissionForm
│       views.py            # Atomic reservation, UPI checkout, cancellation, receipt, owner dashboard
│       urls.py
│       tests.py
│
├───core/                   # Homepage, About, Contact & Demo Commands
│       views.py            # Home, about, contact views
│       context_processors.py # Global site context (badges, pending counts)
│       urls.py
│       management/commands/seed_demo_data.py # Seed demo command with Pillow graphic generator
│
├───static/
│   ├───css/
│   │       style.css       # High-contrast light theme CSS & responsive rules
│   └───js/
│           main.js         # AJAX dynamic slot selector, copy UPI ID helper
│
├───templates/              # Responsive Bootstrap 5 HTML Templates
│   │   base.html
│   ├───accounts/           # Customer & Owner login/register/profile templates
│   ├───turfs/              # Turf list, detail, CRUD, photo & blocked slot templates
│   ├───bookings/           # Checkout, customer dashboard, owner dashboard, receipt, cancel confirm
│   └───core/               # Home, about, contact templates
│
└───media/                  # Uploaded Turf photos, UPI QR codes, Payment proofs
    ├───turf_images/
    ├───upi_qr/
    └───payment_proofs/
```

---

## 🎓 Academic Mini-Project Note
Developed as an engineering capstone mini-project showcasing:
- Model-View-Template (MVT) architecture.
- Relational database normalization with Django ORM.
- Concurrency control via database transactions (`select_for_update`).
- Manual payment verification workflows.
- Professional UI/UX with zero dark-theme text visibility flaws.
