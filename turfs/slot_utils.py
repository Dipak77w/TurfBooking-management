from datetime import datetime, date, time, timedelta
from django.utils import timezone
from .models import Turf, BlockedSlot
from bookings.models import Booking


def generate_turf_slots(turf, target_date):
    """
    Dynamically generates hourly/duration slots between turf.opening_time and turf.closing_time
    for target_date, checking against past times, active bookings, and blocked slots.
    """
    now = timezone.localtime(timezone.now())
    is_today = (target_date == now.date())

    slots = []
    
    # Starting and closing datetimes
    curr_dt = datetime.combine(target_date, turf.opening_time)
    end_dt = datetime.combine(target_date, turf.closing_time)
    
    # Handle overnight turfs if closing_time < opening_time
    if turf.closing_time <= turf.opening_time:
        end_dt += timedelta(days=1)

    duration = timedelta(minutes=turf.slot_duration_minutes)

    # Pre-fetch booked slots for target date
    active_bookings = Booking.objects.filter(
        turf=turf,
        booking_date=target_date,
        status__in=['CONFIRMED', 'PENDING']
    ).values_list('start_time', flat=True)
    booked_start_times = set(active_bookings)

    # Pre-fetch blocked slots for target date
    blocked_slots = BlockedSlot.objects.filter(
        turf=turf,
        block_date=target_date
    )
    is_whole_day_blocked = blocked_slots.filter(start_time__isnull=True).exists()

    while curr_dt + duration <= end_dt:
        slot_start = curr_dt.time()
        slot_end = (curr_dt + duration).time()
        
        # Check if past
        is_past = False
        if is_today:
            # Aware datetime comparison
            slot_aware_dt = timezone.make_aware(curr_dt, timezone.get_current_timezone())
            if slot_aware_dt <= now:
                is_past = True

        # Check if blocked
        is_blocked = is_whole_day_blocked
        if not is_blocked:
            for b in blocked_slots:
                if b.start_time and b.end_time:
                    if not (slot_end <= b.start_time or slot_start >= b.end_time):
                        is_blocked = True
                        break

        # Check if booked
        is_booked = slot_start in booked_start_times

        status = 'available'
        status_label = 'Available'
        if is_past:
            status = 'past'
            status_label = 'Time Passed'
        elif is_blocked:
            status = 'blocked'
            status_label = 'Blocked'
        elif is_booked:
            status = 'booked'
            status_label = 'Booked'

        slots.append({
            'start_time': slot_start.strftime('%H:%M'),
            'end_time': slot_end.strftime('%H:%M'),
            'display_time': f"{slot_start.strftime('%I:%M %p')} - {slot_end.strftime('%I:%M %p')}",
            'status': status,
            'status_label': status_label,
            'is_available': (status == 'available'),
            'price': float(turf.hourly_price)
        })

        curr_dt += duration

    return slots
