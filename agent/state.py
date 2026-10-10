"""
Home Credit AI Voice Agent - State Management Module
"""

from typing import Optional, Dict, Any, List

class CustomerState:
    """
    Maintains internal customer state for Home Credit LAP qualification flow.
    Tracks the 7 eligibility fields, special conditions, and workflow flags.
    """

    def __init__(self, customer_name: str = "Valued Customer"):
        self.customer_name: str = customer_name
        
        # 7 Mandatory Eligibility Fields
        self.property_type: Optional[str] = None          # Residential, Commercial, Industrial, Agricultural
        self.ownership: Optional[str] = None              # Sole, Joint
        self.documents: Optional[bool] = None             # True (Available), False (Unavailable), None (Unasked/Ambiguous)
        self.loan_amount: Optional[float] = None          # Amount requested in INR (Max 7500000 = 75 Lakh)
        self.occupation: Optional[str] = None             # Salaried, Self-employed, Cash-earner
        self.income_mode: Optional[str] = None            # Bank, Cash
        self.market_value: Optional[float] = None         # Market value of property in INR
        self.tenure: Optional[int] = None                 # Tenure in years (3 to 15 years allowed)

        # Special Flow / Intent Flags
        self.existing_loan: bool = False                  # Has existing loan on property
        self.emi_reduction: bool = False                  # Wants EMI reduction on existing loan
        self.is_busy: bool = False                        # Customer is busy right now
        self.callback_time: Optional[str] = None          # Captured callback time
        self.loan_amount_exceeded: bool = False           # Asked > 75 Lakhs and needs confirmation to cap at 75 Lakhs

        # Terminal & Workflow Flags
        self.disqualified: bool = False                   # Immediate disqualification flag
        self.disqualification_reason: Optional[str] = None
        self.transfer_required: bool = False              # Needs transfer to Loan Transfer Specialist
        self.transfer_reason: Optional[str] = None
        self.handover_completed: bool = False             # Passed all 7 criteria -> Senior Expert Handoff

    def update_field(self, field_name: str, value: Any) -> None:
        """Dynamically update state fields with validation awareness."""
        if hasattr(self, field_name):
            setattr(self, field_name, value)

    def get_unanswered_fields(self) -> List[str]:
        """
        Returns list of unanswered eligibility data points in order:
        1. property_type
        2. ownership
        3. documents
        4. loan_amount
        5. occupation_and_income (occupation & income_mode)
        6. market_value
        7. tenure
        """
        missing = []
        if self.property_type is None:
            missing.append("property_type")
        if self.ownership is None:
            missing.append("ownership")
        if self.documents is None:
            missing.append("documents")
        if self.loan_amount is None:
            missing.append("loan_amount")
        if self.occupation is None or self.income_mode is None:
            missing.append("occupation_and_income")
        if self.market_value is None:
            missing.append("market_value")
        if self.tenure is None:
            missing.append("tenure")
        return missing

    def is_all_eligibility_answered(self) -> bool:
        """Returns True if all 7 eligibility points are populated."""
        return len(self.get_unanswered_fields()) == 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert state to plain dictionary."""
        return {
            "property_type": self.property_type,
            "ownership": self.ownership,
            "documents": self.documents,
            "loan_amount": self.loan_amount,
            "occupation": self.occupation,
            "income_mode": self.income_mode,
            "market_value": self.market_value,
            "tenure": self.tenure,
            "existing_loan": self.existing_loan,
            "emi_reduction": self.emi_reduction,
            "is_busy": self.is_busy,
            "callback_time": self.callback_time,
            "loan_amount_exceeded": self.loan_amount_exceeded,
            "disqualified": self.disqualified,
            "disqualification_reason": self.disqualification_reason,
            "transfer_required": self.transfer_required,
            "transfer_reason": self.transfer_reason,
            "handover_completed": self.handover_completed,
            "unanswered_fields": self.get_unanswered_fields()
        }

    def __repr__(self) -> str:
        return f"<CustomerState disqualified={self.disqualified} transfer={self.transfer_required} missing={len(self.get_unanswered_fields())}>"
