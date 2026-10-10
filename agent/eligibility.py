"""
Home Credit AI Voice Agent - Eligibility Engine
Strictly implements the 7 Home Credit Loan Against Property (LAP) criteria & special flow rules.
"""

from typing import Tuple, Optional
from agent.state import CustomerState

MAX_LOAN_AMOUNT_INR = 7500000  # ₹75 Lakh
MIN_TENURE_YEARS = 3
MAX_TENURE_YEARS = 15

ALLOWED_PROPERTY_TYPES = {"residential", "commercial", "industrial"}
DISQUALIFIED_PROPERTY_TYPES = {"agricultural", "agri", "farm", "farmland"}

ALLOWED_OCCUPATIONS = {"salaried", "self-employed", "business owner", "self employed", "business"}
ALLOWED_INCOME_MODES = {"bank", "bank account", "cheque", "online", "direct deposit", "salary account"}
DISQUALIFIED_INCOME_MODES = {"cash", "in cash", "hand cash"}

def evaluate_eligibility(state: CustomerState) -> Tuple[bool, Optional[str]]:
    """
    Evaluates customer state against Home Credit business rules.
    Updates `state.disqualified`, `state.disqualification_reason`, `state.transfer_required`, `state.transfer_reason`.
    
    Returns:
        Tuple[bool, Optional[str]]: (is_eligible_so_far, disqualification_or_transfer_reason)
    """

    # Rule A: Existing Loan / EMI Reduction -> Transfer to Specialist
    if state.existing_loan or state.emi_reduction:
        state.transfer_required = True
        state.transfer_reason = "Customer requested balance transfer or EMI reduction on existing property loan."
        return False, state.transfer_reason

    # Rule 1: Property Type (Disqualify if Agricultural)
    if state.property_type is not None:
        prop_type_clean = str(state.property_type).strip().lower()
        if prop_type_clean in DISQUALIFIED_PROPERTY_TYPES or "agri" in prop_type_clean:
            state.disqualified = True
            state.disqualification_reason = "Agricultural properties are not eligible for Home Credit LAP."
            return False, state.disqualification_reason
        elif prop_type_clean not in ALLOWED_PROPERTY_TYPES and "resident" not in prop_type_clean and "commerc" not in prop_type_clean and "industr" not in prop_type_clean:
            # Unknown property type, but if explicit agricultural, caught above
            pass

    # Rule 2: Ownership Status (Sole and Joint both allowed)
    # No disqualification for ownership type as long as specified.

    # Rule 3: Original Property Documents (Disqualify if unavailable)
    if state.documents is False:
        state.disqualified = True
        state.disqualification_reason = "Original property documents are mandatory for Home Credit LAP."
        return False, state.disqualification_reason

    # Rule 4: Loan Amount (Max 75 Lakhs limit check)
    if state.loan_amount is not None:
        if state.loan_amount > MAX_LOAN_AMOUNT_INR and not state.loan_amount_exceeded:
            state.loan_amount_exceeded = True
            # Not disqualified immediately, but requires prompt to cap at 75L

    # Rule 5: Occupation + Income Mode (Disqualify if Cash income)
    if state.income_mode is not None:
        income_mode_clean = str(state.income_mode).strip().lower()
        if income_mode_clean in DISQUALIFIED_INCOME_MODES or "cash" in income_mode_clean:
            state.disqualified = True
            state.disqualification_reason = "Income received in cash is not eligible. Bank account income is required."
            return False, state.disqualification_reason

    # Rule 6: Property Market Value (No minimum market value requirement)
    # Value recorded, no disqualification threshold applied.

    # Rule 7: Tenure (Allowed range: 3 to 15 years)
    if state.tenure is not None:
        try:
            tenure_val = int(state.tenure)
            if tenure_val < MIN_TENURE_YEARS:
                state.disqualified = True
                state.disqualification_reason = f"Loan tenure of {tenure_val} years is below the minimum required 3 years."
                return False, state.disqualification_reason
            elif tenure_val > MAX_TENURE_YEARS:
                state.disqualified = True
                state.disqualification_reason = f"Loan tenure of {tenure_val} years exceeds the maximum allowed 15 years."
                return False, state.disqualification_reason
        except (ValueError, TypeError):
            pass

    # If no disqualification or transfer triggered
    return True, None
