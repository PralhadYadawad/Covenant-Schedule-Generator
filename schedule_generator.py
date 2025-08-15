# =============================
# Covenant Schedule Generator
# =============================

from datetime import datetime, timedelta, date
from dateutil.relativedelta import relativedelta
from typing import List, Dict, Any
import calendar
import holidays

# Default fallback holidays 
DEFAULT_HOLIDAYS = set([
    # Additional holidays can be added here
])

class ScheduleGenerator:
    """
    Generates covenant fulfillment schedules for a transaction, supporting multiple frequencies and business rules.
    Handles edge cases: month-end, weekends, holidays, leap years, and transaction end cutoff.
    """

    def __init__(self, holidays: List[str] = None, business_day_adjustment: str = 'forward', country: str = 'IN', years: list = None):
        """
        Initialize the schedule generator with holiday and business day settings.

        Args:
            holidays (List[str], optional): List of holiday dates as 'YYYY-MM-DD' strings. If None, will auto-generate using holidays package.
            business_day_adjustment (str): 'forward' (default) or 'backward' for due date adjustment direction.
            country (str): Country code for holidays package (default 'IN' for India)
            years (list, optional): List of years for which to generate holidays (default: current year)
        """
        # Set up holidays
        if holidays is not None:
            self.holidays = set(holidays)
        else:
            # Auto-generate using holidays package for the given country and years
            if years is None:
                years = [date.today().year]
            try:
                country_holidays = holidays.country_holidays(country, years=years)
                self.holidays = set(d.strftime('%Y-%m-%d') for d in country_holidays.keys())
            except Exception:
                self.holidays = DEFAULT_HOLIDAYS

        # Validate business day adjustment direction
        if business_day_adjustment not in ('forward', 'backward'):
            raise ValueError("business_day_adjustment must be 'forward' or 'backward'")
        self.business_day_adjustment = business_day_adjustment

    # =============================
    # Validation Methods
    # =============================

    @staticmethod
    def _validate_transaction(transaction: Dict[str, Any]):
        """
        Validates the transaction dictionary for required fields and correct date logic.
        Raises ValueError if validation fails.
        """
        required = ['transaction_id', 'name', 'start_date', 'end_date']
        for key in required:
            if key not in transaction:
                raise ValueError(f"Transaction missing required field: {key}")
            if not isinstance(transaction[key], str):
                raise ValueError(f"Transaction field {key} must be a string")
        # Validate date format
        for d in ['start_date', 'end_date']:
            try:
                datetime.strptime(transaction[d], '%Y-%m-%d')
            except Exception:
                raise ValueError(f"Transaction {d} must be in YYYY-MM-DD format")
        # Validate start_date <= end_date
        start = datetime.strptime(transaction['start_date'], '%Y-%m-%d').date()
        end = datetime.strptime(transaction['end_date'], '%Y-%m-%d').date()
        if start > end:
            raise ValueError("Transaction start_date must be before or equal to end_date")

    @staticmethod
    def _validate_covenant(covenant: Dict[str, Any]):
        """
        Validates the covenant dictionary for required fields, frequency, and email format.
        Raises ValueError if validation fails.
        """
        import re
        required = ['covenant_id', 'transaction_id', 'description', 'frequency', 'owner_email']
        for key in required:
            if key not in covenant:
                raise ValueError(f"Covenant missing required field: {key}")
            if not isinstance(covenant[key], str):
                raise ValueError(f"Covenant field {key} must be a string")
        # Validate frequency
        allowed_frequencies = {'daily', 'weekly', 'monthly', 'quarterly', 'annually'}
        if covenant['frequency'].lower() not in allowed_frequencies:
            raise ValueError(f"Covenant frequency must be one of {allowed_frequencies}")
        # Validate email format
        email_regex = r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$"
        if not re.match(email_regex, covenant['owner_email']):
            raise ValueError(f"Covenant owner_email is not a valid email address: {covenant['owner_email']}")

    def generate_schedules(self, transaction: Dict[str, Any], covenants: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Generate all schedule entries for the given transaction and covenants.

        Args:
            transaction (dict): Transaction info with transaction_id, start_date, end_date, etc.
            covenants (list): List of covenant dicts, each with frequency, covenant_id, etc.

        Returns:
            List[dict]: List of schedule dicts.
        """
        self._validate_transaction(transaction)
        seen_covenant_ids = set()
        transaction_id = transaction['transaction_id']
        schedules = []
        for cov in covenants:
            self._validate_covenant(cov)
            # Referential integrity: covenant's transaction_id must match
            if cov['transaction_id'] != transaction_id:
                raise ValueError(f"Covenant {cov['covenant_id']} transaction_id does not match transaction")
            # Uniqueness: covenant_id must be unique in this batch
            if cov['covenant_id'] in seen_covenant_ids:
                raise ValueError(f"Duplicate covenant_id found: {cov['covenant_id']}")
            seen_covenant_ids.add(cov['covenant_id'])
            # Business rule: frequency must be appropriate for transaction duration
            freq = cov['frequency'].lower()
            start = datetime.strptime(transaction['start_date'], '%Y-%m-%d').date()
            end = datetime.strptime(transaction['end_date'], '%Y-%m-%d').date()
            duration_days = (end - start).days
            # Only block frequencies that are truly impossible for the transaction duration
            if freq == 'annually' and duration_days < 365:
                continue  # No annual schedules possible, skip
            if freq == 'quarterly' and duration_days < 90:
                continue  # No quarterly schedules possible, skip
            if freq == 'monthly' and duration_days < 28:
                continue  # No monthly schedules possible, skip
            # Use the appropriate schedule generation method
            method = getattr(self, f'_generate_{freq}_schedules', None)
            if method:
                schedules.extend(method(transaction, cov))
            else:
                raise ValueError(f"Unsupported frequency: {freq}")
        return schedules

    # =============================
    # Schedule Generation Methods
    # =============================

    def _generate_monthly_schedules(self, transaction, covenant):
        """Generate monthly schedules."""
        return self._generate_periodic_schedules(transaction, covenant, months=1)

    def _generate_quarterly_schedules(self, transaction, covenant):
        """Generate quarterly schedules."""
        return self._generate_periodic_schedules(transaction, covenant, months=3)

    def _generate_annually_schedules(self, transaction, covenant):
        """Generate annual schedules."""
        return self._generate_periodic_schedules(transaction, covenant, months=12)

    def _generate_weekly_schedules(self, transaction, covenant):
        """
        Generate weekly schedules. Each period is 7 days, due date is the next business day after the period.
        """
        start = datetime.strptime(transaction['start_date'], '%Y-%m-%d').date()
        end = datetime.strptime(transaction['end_date'], '%Y-%m-%d').date()
        schedules = []
        period_start = start
        idx = 1
        while period_start < end:
            period_end = period_start + timedelta(days=6)
            due_date = period_start + timedelta(days=7)
            # Adjust due date to business day if needed
            if not self._is_business_day(due_date):
                due_date = self._adjust_to_business_day(due_date, forward=(self.business_day_adjustment == 'forward'))
            if due_date > end:
                break
            schedules.append(self._make_schedule_entry(covenant, idx, due_date, period_start, period_end))
            period_start += timedelta(days=7)
            idx += 1
        return schedules

    def _generate_daily_schedules(self, transaction, covenant):
        """
        Generate daily schedules. Only business days are considered for schedule generation.
        """
        start = datetime.strptime(transaction['start_date'], '%Y-%m-%d').date()
        end = datetime.strptime(transaction['end_date'], '%Y-%m-%d').date()
        schedules = []
        idx = 1
        current = start
        while current < end:
            if self._is_business_day(current):
                due_date = current + timedelta(days=1)
                due_date = self._adjust_to_business_day(due_date, forward=(self.business_day_adjustment == 'forward'))
                if due_date > end:
                    break
                schedules.append(self._make_schedule_entry(covenant, idx, due_date, current, current))
                idx += 1
            current += timedelta(days=1)
        return schedules

    def _generate_periodic_schedules(self, transaction, covenant, months):
        """
        Generate schedules for monthly, quarterly, or annual covenants.

        Args:
            months (int): Number of months per period (1, 3, or 12)
        """
        start = datetime.strptime(transaction['start_date'], '%Y-%m-%d').date()
        end = datetime.strptime(transaction['end_date'], '%Y-%m-%d').date()
        schedules = []
        idx = 1
        period_start = start
        orig_day = start.day
        is_month_end = (calendar.monthrange(start.year, start.month)[1] == start.day)
        while True:
            next_period_start = period_start + relativedelta(months=months)
            period_end = next_period_start - timedelta(days=1)

            # Month-end logic: if start is month-end, always use month-end for due date
            if is_month_end:
                due_date = next_period_start.replace(day=calendar.monthrange(next_period_start.year, next_period_start.month)[1])
            else:
                # Try to use the same day as original, or last day if not possible (e.g., Feb)
                try:
                    due_date = next_period_start.replace(day=orig_day)
                except ValueError:
                    due_date = next_period_start.replace(day=calendar.monthrange(next_period_start.year, next_period_start.month)[1])

            # Leap year handling for annual schedules: if start is Feb 29, try to use Feb 29 if possible
            if months == 12 and start.month == 2 and start.day == 29:
                if calendar.isleap(next_period_start.year):
                    due_date = next_period_start.replace(month=2, day=29)
                else:
                    due_date = next_period_start.replace(month=2, day=28)

            # For quarterly, if start is month-end, ensure Feb 28/29 is possible
            # Special handling: if the next period's month is March, also generate a Feb 28/29 due date for the previous quarter
            if months == 3 and is_month_end:
                if next_period_start.month == 3:
                    feb_due_date = next_period_start.replace(month=2, day=calendar.monthrange(next_period_start.year, 2)[1])
                    # Adjust Feb due date to business day if needed
                    if not self._is_business_day(feb_due_date):
                        feb_due_date = self._adjust_to_business_day(feb_due_date, forward=(self.business_day_adjustment == 'forward'))
                    if feb_due_date <= end:
                        schedules.append(self._make_schedule_entry(covenant, idx, feb_due_date, period_start, feb_due_date))
                        idx += 1

            # Transaction end cutoff: allow due_date == end
            if due_date > end:
                break

            # Always adjust to business day for periodic schedules
            if not self._is_business_day(due_date):
                due_date = self._adjust_to_business_day(due_date, forward=(self.business_day_adjustment == 'forward'))

            schedules.append(self._make_schedule_entry(covenant, idx, due_date, period_start, period_end))
            period_start = next_period_start
            idx += 1
        return schedules

    # =============================
    # Business Day Utilities
    # =============================

    def _adjust_to_business_day(self, d: date, forward: bool = True) -> date:
        """
        Move date to the next (or previous) business day if it falls on a weekend or holiday.

        Args:
            d (date): The date to adjust
            forward (bool): If True, move forward; else, move backward

        Returns:
            date: Adjusted business day
        """
        step = timedelta(days=1) if forward else timedelta(days=-1)
        attempts = 0
        while not self._is_business_day(d):
            d += step
            attempts += 1
            if attempts > 10:
                raise RuntimeError("Unable to find a business day within 10 days. Check holiday/weekend configuration.")
        return d

    def _is_business_day(self, d: date) -> bool:
        """
        Returns True if the date is a business day (Mon-Fri and not a holiday).
        """
        return d.weekday() < 5 and d.strftime('%Y-%m-%d') not in self.holidays

    # =============================
    # Schedule Entry Construction
    # =============================

    def _make_schedule_entry(self, covenant, idx, due_date, period_start, period_end):
        """
        Create a schedule entry dict. Uses full covenant_id and idx for uniqueness.

        Args:
            covenant (dict): The covenant dict
            idx (int): Index for uniqueness
            due_date (date): Due date for the schedule
            period_start (date): Start of the period
            period_end (date): End of the period

        Returns:
            dict: Schedule entry
        """
        return {
            'schedule_id': f"SCH-{covenant['covenant_id']}-{idx:03d}",
            'covenant_id': covenant['covenant_id'],
            'due_date': due_date.strftime('%Y-%m-%d'),
            'status': 'pending',
            'period_start': period_start.strftime('%Y-%m-%d'),
            'period_end': period_end.strftime('%Y-%m-%d')
        }
