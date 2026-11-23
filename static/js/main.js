/**
 * MiniTurf Arena - Main JavaScript Interactivity
 */

document.addEventListener('DOMContentLoaded', function () {
    // 1. Auto dismiss alerts after 5 seconds
    const alerts = document.querySelectorAll('.alert-dismissible');
    alerts.forEach(function (alert) {
        setTimeout(function () {
            const bsAlert = bootstrap.Alert.getOrCreateInstance(alert);
            if (bsAlert) {
                bsAlert.close();
            }
        }, 6000);
    });

    // 2. Interactive Turf Slot Booking Engine
    const dateInput = document.getElementById('booking-date-input');
    const slotsContainer = document.getElementById('slots-container');
    const slotSummaryBox = document.getElementById('slot-summary-box');
    const hiddenStartTime = document.getElementById('id_start_time');
    const hiddenEndTime = document.getElementById('id_end_time');
    const selectedSlotText = document.getElementById('selected-slot-text');
    const selectedSlotPrice = document.getElementById('selected-slot-price');
    const submitBookingBtn = document.getElementById('submit-booking-btn');

    if (dateInput && slotsContainer) {
        const turfSlug = dateInput.getAttribute('data-turf-slug');

        function loadSlotsForDate(selectedDate) {
            slotsContainer.innerHTML = `
                <div class="col-12 text-center py-4">
                    <div class="spinner-border text-success" role="status">
                        <span class="visually-hidden">Loading slots...</span>
                    </div>
                    <p class="mt-2 text-muted fw-semibold">Checking slot availability for ${selectedDate}...</p>
                </div>
            `;

            // Reset selection
            if (hiddenStartTime) hiddenStartTime.value = '';
            if (hiddenEndTime) hiddenEndTime.value = '';
            if (submitBookingBtn) submitBookingBtn.disabled = true;
            if (slotSummaryBox) slotSummaryBox.classList.add('d-none');

            fetch(`/turfs/${turfSlug}/slots/?date=${selectedDate}`)
                .then(response => {
                    if (!response.ok) throw new Error('Network error');
                    return response.json();
                })
                .then(data => {
                    renderSlots(data.slots);
                })
                .catch(err => {
                    slotsContainer.innerHTML = `
                        <div class="col-12 alert alert-danger">
                            <i class="bi bi-exclamation-triangle-fill me-2"></i> Failed to fetch slots. Please try another date.
                        </div>
                    `;
                });
        }

        function renderSlots(slots) {
            if (!slots || slots.length === 0) {
                slotsContainer.innerHTML = `
                    <div class="col-12 text-center py-3 text-muted">
                        <i class="bi bi-calendar-x fs-2"></i>
                        <p class="mt-1">No operating slots available on this date.</p>
                    </div>
                `;
                return;
            }

            let html = '';
            slots.forEach(slot => {
                if (slot.is_available) {
                    html += `
                        <button type="button" class="slot-btn" 
                                data-start="${slot.start_time}" 
                                data-end="${slot.end_time}"
                                data-display="${slot.display_time}"
                                data-price="${slot.price}">
                            <i class="bi bi-clock"></i>
                            <span>${slot.display_time}</span>
                            <span class="slot-price-label">₹${slot.price}</span>
                        </button>
                    `;
                } else {
                    let badgeLabel = slot.status_label;
                    let iconClass = 'bi-dash-circle';
                    if (slot.status === 'booked') {
                        iconClass = 'bi-lock-fill';
                    } else if (slot.status === 'blocked') {
                        iconClass = 'bi-tools';
                    }
                    html += `
                        <div class="slot-btn disabled">
                            <i class="bi ${iconClass}"></i>
                            <span>${slot.display_time}</span>
                            <span class="badge bg-secondary" style="font-size: 0.65rem;">${badgeLabel}</span>
                        </div>
                    `;
                }
            });

            slotsContainer.innerHTML = html;

            // Attach click listeners to newly created slot buttons
            const buttons = slotsContainer.querySelectorAll('.slot-btn:not(.disabled)');
            buttons.forEach(btn => {
                btn.addEventListener('click', function () {
                    buttons.forEach(b => b.classList.remove('selected'));
                    this.classList.add('selected');

                    const start = this.getAttribute('data-start');
                    const end = this.getAttribute('data-end');
                    const display = this.getAttribute('data-display');
                    const price = this.getAttribute('data-price');

                    if (hiddenStartTime) hiddenStartTime.value = start;
                    if (hiddenEndTime) hiddenEndTime.value = end;
                    if (selectedSlotText) selectedSlotText.textContent = display;
                    if (selectedSlotPrice) selectedSlotPrice.textContent = `₹${price}`;
                    if (slotSummaryBox) slotSummaryBox.classList.remove('d-none');
                    if (submitBookingBtn) submitBookingBtn.disabled = false;
                });
            });
        }

        // On date input change
        dateInput.addEventListener('change', function () {
            loadSlotsForDate(this.value);
        });

        // Initialize with default date
        loadSlotsForDate(dateInput.value);
    }

    // 3. One-Click Copy UPI ID button
    const copyUpiBtn = document.getElementById('copy-upi-btn');
    if (copyUpiBtn) {
        copyUpiBtn.addEventListener('click', function () {
            const upiId = this.getAttribute('data-upi-id');
            navigator.clipboard.writeText(upiId).then(() => {
                const originalText = this.innerHTML;
                this.innerHTML = '<i class="bi bi-check2-circle"></i> Copied!';
                this.classList.add('btn-success');
                setTimeout(() => {
                    this.innerHTML = originalText;
                    this.classList.remove('btn-success');
                }, 2000);
            });
        });
    }

    // 4. Quick Demo Submit Helper
    const demoFillBtn = document.getElementById('demo-fill-utr-btn');
    if (demoFillBtn) {
        demoFillBtn.addEventListener('click', function () {
            const utrInput = document.getElementById('id_upi_reference_id');
            if (utrInput) {
                const randUTR = '43' + Math.floor(1000000000 + Math.random() * 9000000000);
                utrInput.value = randUTR;
            }
        });
    }
});
