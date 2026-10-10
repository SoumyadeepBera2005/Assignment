"""
Home Credit AI Voice Agent - Conversational Orchestrator Engine
Combines State Management, Pattern/NLP Extraction, RAG Engine, Eligibility Rules, and Prompt Execution.
"""

import re
from typing import Dict, Any, List, Optional, Tuple

from agent.state import CustomerState
from agent.eligibility import evaluate_eligibility, MAX_LOAN_AMOUNT_INR
from rag.rag_engine import get_rag_context
from prompts.system_prompt import build_system_prompt

class ConversationalAgent:
    def __init__(self, customer_name: str = "Valued Customer", agent_name: str = "Priya", agent_gender: str = "Female"):
        self.agent_name = agent_name
        self.agent_gender = agent_gender
        self.customer_name = customer_name
        self.company_name = "Home Credit"
        self.language = "English"

        self.state = CustomerState(customer_name=customer_name)
        self.history: List[Dict[str, str]] = []

    def reset(self):
        """Reset state for a new session."""
        self.state = CustomerState(customer_name=self.customer_name)
        self.history.clear()

    def _extract_amounts_with_context(self, text: str) -> List[Tuple[float, str]]:
        """
        Extracts all numeric monetary amounts from text along with their keyword context.
        Returns list of (amount_in_inr, context_type) where context_type is 'market_value', 'loan_amount', or 'unknown'.
        """
        text_lower = text.lower()
        results = []

        # Find phrases like "market value is 1 crore", "worth around 80 lakh", "need 50 lakh loan"
        # Split utterance into clauses by comma or period or 'and'
        clauses = re.split(r'[,.\b]\s*(?:and\s*)?', text_lower)
        for clause in clauses:
            if not clause.strip():
                continue

            # Determine amount in this clause
            amt = None
            crore_match = re.findall(r'(\d+(?:\.\d+)?)\s*(?:cr|crore|crores)', clause)
            if crore_match:
                amt = float(crore_match[-1]) * 10000000
            else:
                lakh_match = re.findall(r'(\d+(?:\.\d+)?)\s*(?:lakh|lac|lakhs|lacs)', clause)
                if lakh_match:
                    amt = float(lakh_match[-1]) * 100000
                else:
                    k_match = re.findall(r'(\d+(?:\.\d+)?)\s*(?:k|thousand)', clause)
                    if k_match:
                        amt = float(k_match[-1]) * 1000
                    else:
                        raw_match = re.findall(r'(?:rs\.?|₹|\b)\s*(\d{5,8})\b', clause)
                        if raw_match:
                            amt = float(raw_match[-1])

            if amt is not None:
                context_type = "unknown"
                if any(kw in clause for kw in ["worth", "market value", "valued at", "value of", "value is"]):
                    context_type = "market_value"
                elif any(kw in clause for kw in ["need", "want", "require", "loan of", "apply for", "borrow"]):
                    context_type = "loan_amount"

                results.append((amt, context_type))

        return results

    def _parse_tenure(self, text: str) -> Optional[int]:
        """Extract tenure in years from utterance."""
        text_lower = text.lower()
        tenure_match = re.findall(r'(\d+)\s*(?:year|years|yr|yrs)', text_lower)
        if tenure_match:
            return int(tenure_match[-1])
        return None

    def extract_entities_and_intents(self, utterance: str) -> Dict[str, Any]:
        """
        Parses utterance for multi-entities, corrections, and intents.
        Follows rule: latest clear answer overwrites previous.
        """
        text_lower = utterance.lower()
        updates = {}

        # 1. Busy check
        if any(w in text_lower for w in ["busy", "call back", "call me later", "in a meeting", "driving", "not right now", "call later"]):
            updates["is_busy"] = True
            time_match = re.findall(r'(?:tomorrow|at \d+|in the evening|after \d+|pm|am|\d+ o\'clock|\d+ pm|\d+ am)', text_lower)
            if time_match:
                updates["callback_time"] = " ".join(time_match)
            else:
                updates["callback_time"] = "convenient time"

        # 2. Existing Loan / EMI Reduction
        if any(w in text_lower for w in ["existing loan", "already have a loan", "already taken a loan", "running loan", "loan on this property"]):
            updates["existing_loan"] = True

        if any(w in text_lower for w in ["emi reduction", "balance transfer", "less emi", "lower emi"]) or ("emi" in text_lower and any(w in text_lower for w in ["reduce", "lower", "less", "cut"])):
            updates["emi_reduction"] = True

        # 3. Property Type (Handles correction: takes latest mentioned)
        prop_matches = []
        for word in text_lower.split():
            clean_w = re.sub(r'[^\w]', '', word)
            if clean_w in ["residential", "commercial", "industrial", "agricultural", "agri", "farm", "farmland"]:
                prop_matches.append(clean_w)
        
        if "agricultural" in text_lower or "farmland" in text_lower or "agri property" in text_lower:
            prop_matches.append("agricultural")
        elif "commercial" in text_lower:
            prop_matches.append("commercial")
        elif "industrial" in text_lower:
            prop_matches.append("industrial")
        elif "residential" in text_lower or "house" in text_lower or "flat" in text_lower:
            if not any(x in text_lower for x in ["agricultural", "commercial", "industrial"]):
                prop_matches.append("residential")

        if prop_matches:
            latest_prop = prop_matches[-1]
            if latest_prop in ["agri", "farm", "farmland"]:
                latest_prop = "agricultural"
            updates["property_type"] = latest_prop.capitalize()

        # 4. Ownership
        if any(w in text_lower for w in ["joint", "jointly", "co-owned", "wife and me", "husband and me", "shared"]):
            updates["ownership"] = "Joint"
        elif any(w in text_lower for w in ["sole", "my own", "myself", "single owner", "only me", "standalone"]):
            updates["ownership"] = "Sole"

        # 5. Original Documents
        if any(phrase in text_lower for phrase in ["probably somewhere", "maybe", "not sure", "need to check", "have to find"]):
            updates["documents_ambiguous"] = True
        elif any(w in text_lower for w in ["yes i have original", "original documents are available", "yes available", "i have original", "original papers available", "original documents available", "documents available", "yes i have them", "yes, original"]):
            updates["documents"] = True
        elif "no original" in text_lower or "don't have original" in text_lower or "documents lost" in text_lower or "documents missing" in text_lower or "no documents" in text_lower or "don't have" in text_lower:
            updates["documents"] = False
        elif "original" in text_lower and any(w in text_lower for w in ["yes", "available", "have"]):
            updates["documents"] = True
        elif "original" in text_lower and any(w in text_lower for w in ["no", "unavailable", "don't"]):
            updates["documents"] = False

        # 6. Occupation & Income Mode
        if any(w in text_lower for w in ["business", "self-employed", "self employed", "shop", "trader", "run a business"]):
            updates["occupation"] = "Self-employed"
        elif any(w in text_lower for w in ["salaried", "job", "company", "employee", "working"]):
            updates["occupation"] = "Salaried"

        if "cash" in text_lower or "in cash" in text_lower or "hand cash" in text_lower:
            updates["income_mode"] = "Cash"
        elif any(w in text_lower for w in ["bank", "salary account", "cheque", "online", "direct deposit", "bank account"]):
            updates["income_mode"] = "Bank"

        # 7. Market Value vs Loan Amount Extraction
        amounts = self._extract_amounts_with_context(utterance)
        for amt, ctx in amounts:
            if ctx == "market_value":
                updates["market_value"] = amt
            elif ctx == "loan_amount":
                updates["loan_amount"] = amt
            else:
                # Context fallback
                if amt > 7500000 and "market_value" not in updates and self.state.market_value is None:
                    updates["market_value"] = amt
                elif "loan_amount" not in updates and self.state.loan_amount is None:
                    updates["loan_amount"] = amt
                elif "market_value" not in updates and self.state.market_value is None:
                    updates["market_value"] = amt

        # 8. Tenure
        tenure_found = self._parse_tenure(text_lower)
        if tenure_found is not None:
            updates["tenure"] = tenure_found

        return updates

    def process_utterance(self, customer_utterance: str) -> Dict[str, Any]:
        """
        Main pipeline function for processing each turn.
        """

        self.history.append({"role": "user", "content": customer_utterance})

        # Handle > 75 Lakh limit negotiation response if waiting
        if self.state.loan_amount_exceeded and self.state.loan_amount and self.state.loan_amount > MAX_LOAN_AMOUNT_INR:
            text_low = customer_utterance.lower()
            if any(w in text_low for w in ["yes", "sure", "ok", "okay", "fine", "proceed", "75 lakh is fine", "75 lakh works"]):
                self.state.loan_amount = float(MAX_LOAN_AMOUNT_INR)
                self.state.loan_amount_exceeded = False
            elif any(w in text_low for w in ["no", "not enough", "cancel", "need more"]):
                self.state.disqualified = True
                self.state.disqualification_reason = "Customer requires loan amount exceeding the maximum pre-approved limit of ₹75 Lakh."

        # Step 1: Extract entities and updates
        extracted = self.extract_entities_and_intents(customer_utterance)

        # Apply extracted fields to state
        for k, v in extracted.items():
            if k == "documents_ambiguous":
                continue
            self.state.update_field(k, v)

        # Step 2: Evaluate eligibility engine rules
        is_eligible_so_far, status_reason = evaluate_eligibility(self.state)

        # Check product questions for RAG retrieval
        rag_context = ""
        if any(kw in customer_utterance.lower() for kw in ["interest rate", "rate of interest", "roi", "processing fee", "documents needed", "document required", "prepayment", "pre-closure", "charges"]):
            rag_context = get_rag_context(customer_utterance)

        # Build System Prompt (for record / LLM)
        history_str = "\n".join([f"{h['role'].upper()}: {h['content']}" for h in self.history[-6:]])
        system_prompt_text = build_system_prompt(
            company_name=self.company_name,
            customer_name=self.customer_name,
            agent_name=self.agent_name,
            agent_gender=self.agent_gender,
            language_to_speak=self.language,
            additional_context_from_rag=rag_context,
            customer_state=self.state.to_dict(),
            conversation_history=history_str,
            customer_utterance=customer_utterance
        )

        # Step 3: Determine Action & Spoken Response
        agent_response = ""
        action = "CONTINUE"

        # Case A: Busy customer
        if self.state.is_busy:
            action = "CALLBACK"
            time_str = self.state.callback_time if self.state.callback_time else "a convenient time"
            agent_response = f"Certainly, I understand you are busy. I have scheduled a callback for {time_str}. Thank you for your time with {self.company_name}, have a great day!"

        # Case B: Disqualified customer
        elif self.state.disqualified:
            action = "DISQUALIFIED"
            reason = self.state.disqualification_reason or "you do not meet our current preliminary eligibility criteria."
            agent_response = f"Thank you for sharing the details, {self.customer_name}. Unfortunately, {reason} Therefore, we cannot proceed with this offer at this time. Have a wonderful day!"

        # Case C: Transfer to Loan Transfer Specialist
        elif self.state.transfer_required:
            action = "TRANSFER"
            agent_response = f"Thank you for letting me know. Since you are looking for balance transfer or EMI reduction on an existing property loan, I will arrange for our Loan Transfer Specialist to call you directly with customized rates. Have a great day!"

        # Case D: Ambiguous documents answer
        elif extracted.get("documents_ambiguous"):
            agent_response = "Just to clarify, do you have the physical original property title deeds and documents available right now for verification?"

        # Case E: Loan amount exceeded limit negotiation
        elif self.state.loan_amount_exceeded and self.state.loan_amount and self.state.loan_amount > MAX_LOAN_AMOUNT_INR:
            amt_lakhs = int(self.state.loan_amount / 100000)
            agent_response = f"Our current pre-approved Loan Against Property offer has a maximum cap of ₹75 Lakh, whereas you requested ₹{amt_lakhs} Lakh. Would you like to proceed with the maximum limit of ₹75 Lakh?"

        # Case F: All 7 Eligibility Questions Answered -> FINAL HANDOFF GATE
        elif self.state.is_all_eligibility_answered() and is_eligible_so_far:
            self.state.handover_completed = True
            action = "HANDOFF"
            agent_response = "Thank you. You have completed the preliminary eligibility check. A senior loan expert will contact you shortly to discuss the next steps and exact interest rates."

        # Case G: In progress - Ask next missing question in priority order
        else:
            action = "CONTINUE"
            missing = self.state.get_unanswered_fields()
            next_q = missing[0] if missing else None

            prefix = ""
            if rag_context:
                if "interest rate" in customer_utterance.lower():
                    prefix = "The exact interest rate will be provided by our senior loan expert after technical evaluation. "
                else:
                    prefix = "Thank you for asking. Details regarding that are covered under our standard Home Credit LAP policy. "

            if next_q == "property_type":
                agent_response = prefix + "To get started, what type of property do you own—is it residential, commercial, or industrial?"
            elif next_q == "ownership":
                agent_response = prefix + "Is the property solely owned by you, or is it under joint ownership?"
            elif next_q == "documents":
                agent_response = prefix + "Do you have the original property registration and title documents available for verification?"
            elif next_q == "loan_amount":
                agent_response = prefix + "How much loan amount are you looking to borrow against your property?"
            elif next_q == "occupation_and_income":
                agent_response = prefix + "Could you tell me your occupation, and whether your income is received through a bank account or in cash?"
            elif next_q == "market_value":
                agent_response = prefix + "What is the approximate current market value of your property?"
            elif next_q == "tenure":
                agent_response = prefix + "Over how many years would you prefer to repay the loan? (We offer tenures between 3 and 15 years)."
            else:
                agent_response = prefix + "Could you please provide the remaining property details to complete your pre-approval?"

        # Record agent turn in history
        self.history.append({"role": "assistant", "content": agent_response})

        return {
            "agent_response": agent_response,
            "action": action,
            "state": self.state.to_dict(),
            "rag_context_used": rag_context,
            "system_prompt_used": system_prompt_text
        }
