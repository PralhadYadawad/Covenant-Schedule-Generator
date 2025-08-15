"""
Comprehensive Test Suite for Covenant Schedule Generator
"""

import pytest
import random
from schedule_generator import ScheduleGenerator
from datetime import date

# --- Test Data Factories ---
def make_transaction(start, end):
    # Factory function to create a mock transaction dictionary for use in tests.
    """Create a transaction dict for testing."""
    return {
        "transaction_id": "TXN-TEST",
        "name": "Test Transaction",
        "start_date": start,
        "end_date": end
    }

def make_covenant(freq, cid="COV-TEST"):
    # Factory function to create a mock covenant dictionary for use in tests.
    """Create a covenant dict for testing."""
    return {
        "covenant_id": cid,
        "transaction_id": "TXN-TEST",
        "description": f"{freq.title()} Covenant",
        "frequency": freq,
        "owner_email": "test@company.com"
    }

# =============================
# Core Business Logic Tests
# =============================

def test_multiple_frequencies_same_transaction():
    """
    Test that multiple covenants with different frequencies for the same transaction
    generate non-overlapping, correct schedules.
    """
    sg = ScheduleGenerator()
    transaction = make_transaction("2025-01-01", "2025-06-01")
    covenants = [make_covenant("monthly", "COV-MONTH"), make_covenant("weekly", "COV-WEEK")]
    schedules = sg.generate_schedules(transaction, covenants)
    ids = [s['schedule_id'] for s in schedules]
    assert len(ids) == len(set(ids))
    assert any("COV-MONTH" in i for i in ids)
    assert any("COV-WEEK" in i for i in ids)

def test_multiple_covenants_same_frequency():
    """
    Test that multiple covenants with the same frequency for the same transaction
    each get their own unique schedule.
    """
    sg = ScheduleGenerator()
    transaction = make_transaction("2025-01-01", "2025-04-01")
    covenants = [make_covenant("monthly", "COV-1"), make_covenant("monthly", "COV-2")]
    schedules = sg.generate_schedules(transaction, covenants)
    ids_1 = [s for s in schedules if s['covenant_id'] == "COV-1"]
    ids_2 = [s for s in schedules if s['covenant_id'] == "COV-2"]
    assert len(ids_1) == len(ids_2)
    assert all(s1['schedule_id'] != s2['schedule_id'] for s1, s2 in zip(ids_1, ids_2))

def test_transaction_start_end_on_weekend_or_holiday():
    """
    Test that transactions starting/ending on weekends or holidays are handled correctly.
    """
    sg = ScheduleGenerator(holidays=["2025-01-04", "2025-01-05"])
    transaction = make_transaction("2025-01-04", "2025-01-05")
    covenants = [make_covenant("daily")]
    schedules = sg.generate_schedules(transaction, covenants)
    assert all(date.fromisoformat(s['due_date']).weekday() < 5 for s in schedules)

def test_schedule_regeneration_no_duplicates():
    """
    Test that regenerating schedules for the same transaction/covenant does not produce duplicate schedule_ids.
    """
    sg = ScheduleGenerator()
    transaction = make_transaction("2025-01-01", "2025-04-01")
    covenants = [make_covenant("monthly")]
    schedules1 = sg.generate_schedules(transaction, covenants)
    schedules2 = sg.generate_schedules(transaction, covenants)
    ids1 = set(s['schedule_id'] for s in schedules1)
    ids2 = set(s['schedule_id'] for s in schedules2)
    assert ids1 == ids2

def test_very_short_transaction():
    """
    Test that a transaction too short for the frequency produces no schedules.
    """
    sg = ScheduleGenerator()
    transaction = make_transaction("2025-01-01", "2025-01-02")
    covenants = [make_covenant("monthly")]
    schedules = sg.generate_schedules(transaction, covenants)
    assert len(schedules) == 0

def test_all_days_are_holidays():
    """
    Test that if all days in the range are holidays, no schedules are generated and the generator does not hang.
    """
    holidays = [f"2025-01-{str(i).zfill(2)}" for i in range(1, 32)]
    sg = ScheduleGenerator(holidays=holidays)
    transaction = make_transaction("2025-01-01", "2025-01-31")
    covenants = [make_covenant("daily")]
    schedules = sg.generate_schedules(transaction, covenants)
    assert len(schedules) == 0

def test_bulk_insert_with_invalid_data():
    """
    Test that the database layer rejects invalid schedule data (e.g., missing required fields).
    """
    from database import Database
    sg = ScheduleGenerator()
    transaction = make_transaction("2025-01-01", "2025-04-01")
    covenants = [make_covenant("monthly")]
    schedules = sg.generate_schedules(transaction, covenants)
    schedules[0]['due_date'] = None
    with Database(':memory:') as db:
        db.save_transaction(transaction)
        db.save_covenants(covenants)
        with pytest.raises(Exception):
            db.save_schedules(schedules)

def test_anniversary_on_feb_29():
    """
    Test that annual schedules starting on Feb 29 are handled correctly in leap and non-leap years.
    """
    sg = ScheduleGenerator()
    transaction = make_transaction("2024-02-29", "2027-03-01")
    covenants = [make_covenant("annually")]
    schedules = sg.generate_schedules(transaction, covenants)
    assert any(s['due_date'].endswith('-02-28') or s['due_date'].endswith('-03-01') for s in schedules)

def test_large_number_of_covenants():
    """
    Test that the generator can handle a large number of covenants efficiently and correctly.
    """
    sg = ScheduleGenerator()
    transaction = make_transaction("2025-01-01", "2025-02-01")
    covenants = [make_covenant("daily", f"COV-{i:03d}") for i in range(200)]
    schedules = sg.generate_schedules(transaction, covenants)
    # Assert that schedules are generated for all covenants, even with a large number
    assert len(schedules) > 0
    # Ensure that each covenant_id is represented in the generated schedules (no missing or duplicate handling errors)
    unique_covs = set(s['covenant_id'] for s in schedules)
    assert len(unique_covs) == 200

def test_monthly_schedule_generation():
    """
    Test that monthly schedules are generated correctly for a multi-year transaction.
    - Verifies the correct number of schedules (one per month, inclusive of start/end year).
    - Checks that the first and last due dates are properly adjusted to the next business day if they fall on a weekend or holiday.
    """
    sg = ScheduleGenerator()
    transaction = make_transaction("2025-01-15", "2027-01-15")
    covenants = [make_covenant("monthly")]
    schedules = sg.generate_schedules(transaction, covenants)
    # There should be 24 monthly schedules between Jan 2025 and Jan 2027 (inclusive of start/end month)
    assert len(schedules) == 24

    # The first due date should be the next business day after 2025-02-15 if it is a weekend/holiday
    sg2 = ScheduleGenerator()
    expected_due = '2025-02-15'
    d = date.fromisoformat(expected_due)
    if not sg2._is_business_day(d):
        d = sg2._adjust_to_business_day(d)
    assert schedules[0]['due_date'] == d.strftime('%Y-%m-%d')

    # The last due date should be the next business day after 2027-01-15 if it is a weekend/holiday
    expected_due = '2027-01-15'
    d = date.fromisoformat(expected_due)
    if not sg2._is_business_day(d):
        d = sg2._adjust_to_business_day(d)
    assert schedules[-1]['due_date'] == d.strftime('%Y-%m-%d')

def test_quarter_end_dates():
    """
    Test that quarterly schedules handle February end dates correctly, including business day adjustment for non-leap years.
    """
    sg = ScheduleGenerator()
    transaction = make_transaction("2025-03-31", "2026-03-31")
    covenants = [make_covenant("quarterly")]
    schedules = sg.generate_schedules(transaction, covenants)
    found = False
    valid_feb_days = ['2026-02-28']  # Only check valid Feb days for 2026 (not a leap year)
    for s in schedules:
        for feb_day in valid_feb_days:
            d = date.fromisoformat(feb_day)
            sg2 = ScheduleGenerator()
            if not sg2._is_business_day(d):
                d = sg2._adjust_to_business_day(d)
            if s['due_date'] == d.strftime('%Y-%m-%d'):
                found = True
    assert found

def test_weekend_adjustment():
    """
    Test that all due dates are adjusted to business days, even when holidays are present.
    """
    sg = ScheduleGenerator(holidays=["2025-01-18"])
    transaction = make_transaction("2025-01-10", "2025-02-10")
    covenants = [make_covenant("weekly")]
    schedules = sg.generate_schedules(transaction, covenants)
    for s in schedules:
        d = date.fromisoformat(s['due_date'])
        assert d.weekday() < 5  # Must be a weekday
        assert s['due_date'] not in sg.holidays  # Must not be a holiday

def test_transaction_end_cutoff():
    """
    Test that no due date is after the next business day after the transaction end date.
    """
    sg = ScheduleGenerator()
    transaction = make_transaction("2025-01-01", "2025-03-01")
    covenants = [make_covenant("monthly")]
    schedules = sg.generate_schedules(transaction, covenants)
    sg2 = ScheduleGenerator()
    end = date.fromisoformat(transaction['end_date'])
    if not sg2._is_business_day(end):
        end = sg2._adjust_to_business_day(end)
    for s in schedules:
        assert s['due_date'] <= end.strftime('%Y-%m-%d')

def test_daily_schedule_generation():
    """
    Test that daily schedules are only generated for business days.
    """
    sg = ScheduleGenerator()
    transaction = make_transaction("2025-01-01", "2025-01-10")
    covenants = [make_covenant("daily")]
    schedules = sg.generate_schedules(transaction, covenants)
    for s in schedules:
        d = date.fromisoformat(s['due_date'])
        assert d.weekday() < 5

def test_annual_schedule_generation():
    """
    Test that annual schedules are generated for the correct number of years and due dates are adjusted to business days.
    - Verifies that the number of annual schedules matches the number of years in the transaction period.
    - Ensures that due dates are adjusted to the next business day if they fall on a weekend or holiday.
    """
    sg = ScheduleGenerator()
    transaction = make_transaction("2025-01-31", "2027-01-31")
    covenants = [make_covenant("annually")]
    schedules = sg.generate_schedules(transaction, covenants)
    # There should be 2 annual schedules between Jan 2025 and Jan 2027
    assert len(schedules) == 2
    # The due date for the first schedule should be the next business day after 2026-01-31 if it is a weekend/holiday
    expected_due = '2026-01-31'
    d = date.fromisoformat(expected_due)
    sg2 = ScheduleGenerator()
    if not sg2._is_business_day(d):
        d = sg2._adjust_to_business_day(d)
    assert schedules[0]['due_date'] == d.strftime('%Y-%m-%d')


def test_bulk_insert_and_retrieval():
    """
    Test that bulk insert and retrieval of schedules via the database layer works as expected.
    - Saves a transaction, covenants, and generated schedules to an in-memory database.
    - Retrieves the schedules and verifies that all inserted schedules are present.
    """
    from database import Database
    sg = ScheduleGenerator()
    transaction = make_transaction("2025-01-01", "2025-04-01")
    covenants = [make_covenant("monthly", "COV-001"), make_covenant("quarterly", "COV-002")]
    schedules = sg.generate_schedules(transaction, covenants)
    with Database(':memory:') as db:
        db.save_transaction(transaction)
        db.save_covenants(covenants)
        db.save_schedules(schedules)
        loaded = db.get_schedules()
        # Assert that all schedules saved are retrieved
        assert len(loaded) == len(schedules)

# --- Additional Edge Case Tests ---
def test_month_end_to_february():
    """
    Test that monthly schedules handle transitions from month-end (e.g., Jan 31) to February correctly.
    - Ensures that due dates for February are set to Feb 28 or Feb 29 as appropriate.
    """
    sg = ScheduleGenerator()
    transaction = make_transaction("2025-01-31", "2025-03-31")
    covenants = [make_covenant("monthly")]
    schedules = sg.generate_schedules(transaction, covenants)
    # Should handle Jan 31 -> Feb 28/29
    feb_due = any(s['due_date'].endswith('-02-28') or s['due_date'].endswith('-02-29') for s in schedules)
    assert feb_due

def test_leap_year_february():
    """
    Test that annual schedules include Feb 29 in leap years.
    - Ensures that a due date of Feb 29, 2024 is present when the transaction period covers a leap year.
    """
    sg = ScheduleGenerator()
    transaction = make_transaction("2023-02-28", "2024-03-01")
    covenants = [make_covenant("annually")]
    schedules = sg.generate_schedules(transaction, covenants)
    # Should include Feb 29, 2024
    leap_due = any(s['due_date'] == '2024-02-29' for s in schedules)
    assert leap_due

def test_due_date_on_holiday():
    """
    Test that due dates falling on a holiday are adjusted to the next business day.
    - Ensures that no due date matches a known holiday.
    """
    sg = ScheduleGenerator(holidays=["2025-01-15"])
    transaction = make_transaction("2025-01-01", "2025-02-01")
    covenants = [make_covenant("monthly")]
    schedules = sg.generate_schedules(transaction, covenants)
    # Due date should move to next business day if on holiday
    for s in schedules:
        assert s['due_date'] != '2025-01-15'

def test_due_date_on_weekend():
    """
    Test that due dates falling on weekends are adjusted to business days.
    - Ensures that all due dates are weekdays (Monday to Friday).
    """
    sg = ScheduleGenerator()
    transaction = make_transaction("2025-01-03", "2025-01-20")
    covenants = [make_covenant("weekly")]
    schedules = sg.generate_schedules(transaction, covenants)
    # All due dates should be business days
    for s in schedules:
        d = date.fromisoformat(s['due_date'])
        assert d.weekday() < 5

def test_large_dataset_performance():
    """
    Test that the generator can handle large datasets efficiently.
    - Ensures that generating daily schedules for a 10-year period produces a large number of entries without crashing.
    """
    sg = ScheduleGenerator()
    transaction = make_transaction("2020-01-01", "2030-01-01")
    covenants = [make_covenant("daily")]
    schedules = sg.generate_schedules(transaction, covenants)
    # Should not crash and should generate a large number of entries
    assert len(schedules) > 2500

def test_invalid_transaction_missing_field():
    """
    Test that the generator raises a ValueError if the transaction is missing required fields.
    - Covers missing end_date and other required transaction fields.
    """
    sg = ScheduleGenerator()
    transaction = {"transaction_id": "TXN-FAIL", "start_date": "2025-01-01"}  # missing end_date
    covenants = [make_covenant("monthly")]
    with pytest.raises(ValueError):
        sg.generate_schedules(transaction, covenants)

def test_invalid_covenant_missing_field():
    """
    Test that the generator raises a ValueError if a covenant is missing required fields.
    - Covers missing description and other required covenant fields.
    """
    sg = ScheduleGenerator()
    transaction = make_transaction("2025-01-01", "2025-12-31")
    covenants = [{"covenant_id": "COV-FAIL", "transaction_id": "TXN-TEST", "frequency": "monthly", "owner_email": "test@company.com"}]  # missing description
    with pytest.raises(ValueError):
        sg.generate_schedules(transaction, covenants)

def test_unsupported_frequency():
    """
    Test that the generator raises a ValueError for unsupported covenant frequencies.
    - Covers frequencies not recognized by the business logic (e.g., 'fortnightly').
    """
    sg = ScheduleGenerator()
    transaction = make_transaction("2025-01-01", "2025-12-31")
    covenants = [make_covenant("fortnightly")]
    with pytest.raises(ValueError):
        sg.generate_schedules(transaction, covenants)

def test_schedule_id_uniqueness():
    """
    Test that all generated schedule_ids are unique across covenants for the same transaction.
    - Ensures no duplicate schedule_ids are produced.
    """
    sg = ScheduleGenerator()
    transaction = make_transaction("2025-01-01", "2025-04-01")
    covenants = [make_covenant("monthly", "COV-001"), make_covenant("monthly", "COV-002")]
    schedules = sg.generate_schedules(transaction, covenants)
    ids = [s['schedule_id'] for s in schedules]
    assert len(ids) == len(set(ids))

def test_update_and_delete_schedule():
    # Placeholder for future implementation of update/delete schedule tests.
    # If not needed, this test can be removed.
    # TODO: Implement this test or remove if not needed
    pass

# --- Robustness and Real-World Edge Case Tests ---
def test_invalid_data_types():
    """
    Test that the generator raises errors for invalid data types in input.
    - Covers integer transaction_id, string instead of list for covenants, and None for required fields.
    """
    sg = ScheduleGenerator()
    # Integer instead of string for transaction_id
    transaction = {"transaction_id": 123, "name": 456, "start_date": 20250101, "end_date": 20250131}
    covenants = [make_covenant("monthly")]
    with pytest.raises(ValueError):
        sg.generate_schedules(transaction, covenants)
    # String instead of list for covenants
    transaction = make_transaction("2025-01-01", "2025-01-31")
    with pytest.raises(Exception):
        sg.generate_schedules(transaction, "not-a-list")
    # None for required fields
    transaction = {"transaction_id": None, "name": None, "start_date": None, "end_date": None}
    with pytest.raises(ValueError):
        sg.generate_schedules(transaction, covenants)

def test_malformed_dates():
    """
    Test that the generator raises ValueError for malformed or invalid date strings in transaction fields.
    - Covers various invalid date formats and impossible dates.
    """
    sg = ScheduleGenerator()
    # Invalid date formats
    bad_dates = ["2025/01/01", "01-01-2025", "2025-13-01", "2025-00-10", "2025-02-30", "not-a-date"]
    for bad in bad_dates:
        transaction = make_transaction(bad, "2025-01-31")
        covenants = [make_covenant("monthly")]
        with pytest.raises(ValueError):
            sg.generate_schedules(transaction, covenants)
        transaction = make_transaction("2025-01-01", bad)
        with pytest.raises(ValueError):
            sg.generate_schedules(transaction, covenants)

def test_boundary_and_edge_cases():
    """
    Test various boundary and edge cases for transaction and covenant input.
    - Start and end on same day, end before start, empty string fields, and extra/unexpected fields.
    """
    sg = ScheduleGenerator()
    # Start and end on same day
    transaction = make_transaction("2025-01-01", "2025-01-01")
    covenants = [make_covenant("monthly")]
    schedules = sg.generate_schedules(transaction, covenants)
    assert len(schedules) == 0
    # End before start
    transaction = make_transaction("2025-01-10", "2025-01-01")
    with pytest.raises(ValueError):
        sg.generate_schedules(transaction, covenants)
    # Empty string fields
    transaction = {"transaction_id": "", "name": "", "start_date": "", "end_date": ""}
    with pytest.raises(ValueError):
        sg.generate_schedules(transaction, covenants)
    # Extra, unexpected fields
    transaction = make_transaction("2025-01-01", "2025-01-31")
    transaction["extra_field"] = "extra"
    schedules = sg.generate_schedules(transaction, covenants)
    assert isinstance(schedules, list)

def test_extreme_and_large_inputs():
    """
    Test generator robustness with extreme and large input sizes.
    - Very large number of covenants, very long/short transaction periods.
    """
    sg = ScheduleGenerator()
    # Very large number of covenants
    transaction = make_transaction("2025-01-01", "2025-01-10")
    covenants = [make_covenant("daily", f"COV-{i:05d}") for i in range(1000)]
    schedules = sg.generate_schedules(transaction, covenants)
    assert len(schedules) > 0
    # Very long transaction period
    transaction = make_transaction("2000-01-01", "2050-01-01")
    covenants = [make_covenant("annually")]
    schedules = sg.generate_schedules(transaction, covenants)
    assert len(schedules) > 40
    # Very short transaction period
    transaction = make_transaction("2025-01-01", "2025-01-01")
    schedules = sg.generate_schedules(transaction, covenants)
    assert len(schedules) == 0

def test_all_due_dates_on_holidays():
    """
    Test that no schedules are generated if all days are holidays, and that invalid holidays are handled gracefully.
    - Covers both all-holiday and invalid-holiday-list scenarios.
    """
    # All days are holidays, so no schedules should be generated
    holidays = [f"2025-01-{str(i).zfill(2)}" for i in range(1, 32)]
    sg = ScheduleGenerator(holidays=holidays)
    transaction = make_transaction("2025-01-01", "2025-01-31")
    covenants = [make_covenant("daily")]
    schedules = sg.generate_schedules(transaction, covenants)
    assert len(schedules) == 0
    # Holidays list includes invalid dates
    sg = ScheduleGenerator(holidays=["not-a-date", 123, None])
    transaction = make_transaction("2025-01-01", "2025-01-10")
    covenants = [make_covenant("daily")]
    schedules = sg.generate_schedules(transaction, covenants)
    assert isinstance(schedules, list)

def test_duplicate_and_referential_integrity():
    """
    Test that duplicate covenant_ids and referential integrity errors are caught.
    - Ensures ValueError is raised for duplicate covenant_ids and mismatched transaction_id.
    """
    sg = ScheduleGenerator()
    transaction = make_transaction("2025-01-01", "2025-01-31")
    # Duplicate covenant_id
    covenants = [make_covenant("monthly", "COV-1"), make_covenant("monthly", "COV-1")]
    with pytest.raises(ValueError):
        sg.generate_schedules(transaction, covenants)
    # Covenant with mismatched transaction_id
    bad_cov = make_covenant("monthly", "COV-2")
    bad_cov["transaction_id"] = "TXN-OTHER"
    with pytest.raises(ValueError):
        sg.generate_schedules(transaction, [bad_cov])

def test_unsupported_frequencies_and_case_sensitivity():
    """
    Test that unsupported frequencies and case sensitivity are handled correctly.
    - Ensures ValueError for unsupported, empty, or None frequency, and that uppercase frequencies are accepted.
    """
    sg = ScheduleGenerator()
    transaction = make_transaction("2025-01-01", "2025-12-31")
    # Unsupported frequency
    covenants = [make_covenant("biweekly")]
    with pytest.raises(ValueError):
        sg.generate_schedules(transaction, covenants)
    # Uppercase frequency
    covenants = [make_covenant("WEEKLY")]
    schedules = sg.generate_schedules(transaction, covenants)
    assert len(schedules) > 0
    # Empty string frequency
    bad_cov = make_covenant("", "COV-EMPTY")
    with pytest.raises(ValueError):
        sg.generate_schedules(transaction, [bad_cov])
    # None frequency
    bad_cov = make_covenant("monthly", "COV-NONE")
    bad_cov["frequency"] = None
    with pytest.raises(ValueError):
        sg.generate_schedules(transaction, [bad_cov])

def test_email_validation():
    """
    Test that invalid, empty, or None email addresses in covenants are rejected.
    - Ensures ValueError is raised for invalid email formats.
    """
    sg = ScheduleGenerator()
    transaction = make_transaction("2025-01-01", "2025-12-31")
    # Invalid email formats
    bad_cov = make_covenant("monthly", "COV-EMAIL1")
    bad_cov["owner_email"] = "not-an-email"
    with pytest.raises(ValueError):
        sg.generate_schedules(transaction, [bad_cov])
    bad_cov = make_covenant("monthly", "COV-EMAIL2")
    bad_cov["owner_email"] = "test@company"
    with pytest.raises(ValueError):
        sg.generate_schedules(transaction, [bad_cov])
    # Empty string email
    bad_cov = make_covenant("monthly", "COV-EMAIL3")
    bad_cov["owner_email"] = ""
    with pytest.raises(ValueError):
        sg.generate_schedules(transaction, [bad_cov])
    # None email
    bad_cov = make_covenant("monthly", "COV-EMAIL4")
    bad_cov["owner_email"] = None
    with pytest.raises(ValueError):
        sg.generate_schedules(transaction, [bad_cov])

def test_business_day_adjustment_backward():
    """
    Test that business day adjustment set to 'backward' still results in business day due dates.
    - Ensures all due dates are weekdays.
    """
    # Test with business_day_adjustment='backward'
    sg = ScheduleGenerator(business_day_adjustment='backward')
    transaction = make_transaction("2025-01-01", "2025-01-31")
    covenants = [make_covenant("monthly")]
    schedules = sg.generate_schedules(transaction, covenants)
    for s in schedules:
        d = date.fromisoformat(s['due_date'])
        assert d.weekday() < 5

def test_schedule_uniqueness_and_consistency():
    """
    Test that schedule generation is consistent and unique for the same input.
    - Ensures no overlap in schedule_ids between covenants and that repeated calls are consistent.
    """
    sg = ScheduleGenerator()
    transaction = make_transaction("2025-01-01", "2025-04-01")
    covenants = [make_covenant("monthly", "COV-001"), make_covenant("monthly", "COV-002")]
    schedules1 = sg.generate_schedules(transaction, covenants)
    schedules2 = sg.generate_schedules(transaction, covenants)
    ids1 = set(s['schedule_id'] for s in schedules1)
    ids2 = set(s['schedule_id'] for s in schedules2)
    assert ids1 == ids2
    # Schedules for different covenants with same frequency do not overlap in schedule_id
    ids_by_cov = {s['covenant_id']: set() for s in schedules1}
    for s in schedules1:
        ids_by_cov[s['covenant_id']].add(s['schedule_id'])
    for cov1 in ids_by_cov:
        for cov2 in ids_by_cov:
            if cov1 != cov2:
                assert ids_by_cov[cov1].isdisjoint(ids_by_cov[cov2])

def test_leap_year_and_month_end_edge_cases():
    """
    Test leap year and month-end edge cases for annual and monthly schedules.
    - Ensures correct handling of Feb 29 and month-end transitions.
    """
    sg = ScheduleGenerator()
    # Feb 29 start, ends on Feb 28 non-leap year
    transaction = make_transaction("2024-02-29", "2025-02-28")
    covenants = [make_covenant("annually")]
    schedules = sg.generate_schedules(transaction, covenants)
    assert any(s['due_date'].endswith('-02-28') for s in schedules)
    # Month-end start and end
    transaction = make_transaction("2025-01-31", "2025-03-31")
    covenants = [make_covenant("monthly")]
    schedules = sg.generate_schedules(transaction, covenants)
    assert any(s['due_date'].endswith('-02-28') or s['due_date'].endswith('-02-29') for s in schedules)

def test_database_integration_invalid():
    """
    Test that the database layer enforces required fields and uniqueness constraints.
    - Ensures exceptions are raised for missing required fields and duplicate schedules.
    """
    from database import Database
    sg = ScheduleGenerator()
    transaction = make_transaction("2025-01-01", "2025-04-01")
    covenants = [make_covenant("monthly")]
    schedules = sg.generate_schedules(transaction, covenants)
    # Remove required field
    schedules[0].pop('due_date', None)
    with Database(':memory:') as db:
        db.save_transaction(transaction)
        db.save_covenants(covenants)
        with pytest.raises(Exception):
            db.save_schedules(schedules)
    # Duplicate schedule
    schedules = sg.generate_schedules(transaction, covenants)
    schedules.append(schedules[0].copy())
    with Database(':memory:') as db:
        db.save_transaction(transaction)
        db.save_covenants(covenants)
        with pytest.raises(Exception):
            db.save_schedules(schedules)

def test_performance_large_dataset():
    """
    Test generator and database performance with very large datasets.
    - Ensures large numbers of schedules can be generated, inserted, updated, and deleted without error.
    """
    sg = ScheduleGenerator()
    transaction = make_transaction("2000-01-01", "2050-01-01")
    covenants = [make_covenant("daily")]
    schedules = sg.generate_schedules(transaction, covenants)
    assert len(schedules) > 10000
    from database import Database
    sg = ScheduleGenerator()
    transaction = make_transaction("2025-01-01", "2025-04-01")
    covenants = [make_covenant("monthly", "COV-001")]
    schedules = sg.generate_schedules(transaction, covenants)
    with Database(':memory:') as db:
        db.save_transaction(transaction)
        db.save_covenants(covenants)
        db.save_schedules(schedules)
        # Update status
        db.update_schedule_status(schedules[0]['schedule_id'], 'completed')
        updated = db.get_schedules(schedules[0]['covenant_id'])[0]
        assert updated['status'] == 'completed'
        # Delete
        db.delete_schedule(schedules[0]['schedule_id'])
        after_delete = db.get_schedules(schedules[0]['covenant_id'])
        assert all(s['schedule_id'] != schedules[0]['schedule_id'] for s in after_delete)
