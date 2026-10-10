"""
Home Credit AI Voice Agent - Comprehensive Test Suite
Executes all 12 Standard Test Matrix scenarios + 4 Adversarial scenarios.
"""

import unittest
from agent.conversational_agent import ConversationalAgent

class TestHomeCreditVoiceAgent(unittest.TestCase):

    def setUp(self):
        self.agent = ConversationalAgent(customer_name="Rajesh Sharma")

    def test_01_fully_eligible_customer(self):
        """Test 1: Fully eligible customer workflow reaching Senior Expert Handoff."""
        agent = ConversationalAgent()
        
        # Turn 1
        res1 = agent.process_utterance("Hi, I own a residential house.")
        self.assertEqual(agent.state.property_type, "Residential")
        self.assertEqual(res1["action"], "CONTINUE")

        # Turn 2
        res2 = agent.process_utterance("It is jointly owned with my wife.")
        self.assertEqual(agent.state.ownership, "Joint")
        
        # Turn 3
        res3 = agent.process_utterance("Yes, I have original property documents available.")
        self.assertEqual(agent.state.documents, True)

        # Turn 4
        res4 = agent.process_utterance("I need a loan of ₹40 lakh.")
        self.assertEqual(agent.state.loan_amount, 4000000)

        # Turn 5
        res5 = agent.process_utterance("I am salaried and my income comes in my bank account.")
        self.assertEqual(agent.state.occupation, "Salaried")
        self.assertEqual(agent.state.income_mode, "Bank")

        # Turn 6
        res6 = agent.process_utterance("The market value is around 80 lakh.")
        self.assertEqual(agent.state.market_value, 8000000)

        # Turn 7
        res7 = agent.process_utterance("I want a 10 years tenure.")
        self.assertEqual(agent.state.tenure, 10)

        # Assert Final Gate Handoff
        self.assertEqual(res7["action"], "HANDOFF")
        self.assertTrue(agent.state.handover_completed)
        self.assertIn("senior loan expert will contact you shortly", res7["agent_response"].lower())

    def test_02_agricultural_property(self):
        """Test 2: Agricultural property -> Immediate Disqualification."""
        agent = ConversationalAgent()
        res = agent.process_utterance("I want a loan against my agricultural farmland.")
        self.assertEqual(res["action"], "DISQUALIFIED")
        self.assertTrue(agent.state.disqualified)
        self.assertEqual(agent.state.property_type, "Agricultural")

    def test_03_cash_income(self):
        """Test 3: Cash income -> Immediate Disqualification."""
        agent = ConversationalAgent()
        res = agent.process_utterance("I run a business and get all income in cash.")
        self.assertEqual(res["action"], "DISQUALIFIED")
        self.assertTrue(agent.state.disqualified)
        self.assertEqual(agent.state.income_mode, "Cash")

    def test_04_no_original_documents(self):
        """Test 4: No original documents -> Immediate Disqualification."""
        agent = ConversationalAgent()
        res = agent.process_utterance("I don't have original documents, only photocopies.")
        self.assertEqual(res["action"], "DISQUALIFIED")
        self.assertTrue(agent.state.disqualified)
        self.assertEqual(agent.state.documents, False)

    def test_05_tenure_too_short(self):
        """Test 5: Tenure = 2 years -> Disqualification (< 3 years)."""
        agent = ConversationalAgent()
        res = agent.process_utterance("I need a loan for 2 years tenure.")
        self.assertEqual(res["action"], "DISQUALIFIED")
        self.assertTrue(agent.state.disqualified)
        self.assertEqual(agent.state.tenure, 2)

    def test_06_tenure_too_long(self):
        """Test 6: Tenure = 20 years -> Disqualification (> 15 years)."""
        agent = ConversationalAgent()
        res = agent.process_utterance("I want to repay over 20 years.")
        self.assertEqual(res["action"], "DISQUALIFIED")
        self.assertTrue(agent.state.disqualified)
        self.assertEqual(agent.state.tenure, 20)

    def test_07_loan_amount_exceeded(self):
        """Test 7: Loan amount ₹90 Lakh -> Maximum ₹75 Lakh negotiation."""
        agent = ConversationalAgent()
        res = agent.process_utterance("I need ₹90 lakh loan.")
        self.assertTrue(agent.state.loan_amount_exceeded)
        self.assertIn("75 lakh", res["agent_response"].lower())

        # Customer agrees to ₹75 Lakh
        res2 = agent.process_utterance("Yes, I can proceed with ₹75 lakh.")
        self.assertEqual(agent.state.loan_amount, 7500000)
        self.assertFalse(agent.state.loan_amount_exceeded)

    def test_08_joint_ownership(self):
        """Test 8: Joint ownership -> Eligible to proceed."""
        agent = ConversationalAgent()
        res = agent.process_utterance("The property is under joint ownership.")
        self.assertEqual(agent.state.ownership, "Joint")
        self.assertFalse(agent.state.disqualified)

    def test_09_existing_property_loan(self):
        """Test 9: Existing property loan -> Balance Transfer Specialist."""
        agent = ConversationalAgent()
        res = agent.process_utterance("I already have a loan on this property.")
        self.assertEqual(res["action"], "TRANSFER")
        self.assertTrue(agent.state.transfer_required)

    def test_10_emi_reduction_request(self):
        """Test 10: EMI reduction request -> Balance Transfer Specialist."""
        agent = ConversationalAgent()
        res = agent.process_utterance("I want to reduce my current EMI.")
        self.assertEqual(res["action"], "TRANSFER")
        self.assertTrue(agent.state.transfer_required)

    def test_11_customer_busy(self):
        """Test 11: Busy customer -> Callback flow."""
        agent = ConversationalAgent()
        res = agent.process_utterance("I am busy right now, call me tomorrow at 5 PM.")
        self.assertEqual(res["action"], "CALLBACK")
        self.assertTrue(agent.state.is_busy)
        self.assertIn("tomorrow", agent.state.callback_time.lower())

    def test_12_out_of_order_information(self):
        """Test 12: Information given out of order."""
        agent = ConversationalAgent()
        res = agent.process_utterance("My house market value is 1 crore, I need 50 lakh for 12 years tenure.")
        self.assertEqual(agent.state.market_value, 10000000)
        self.assertEqual(agent.state.loan_amount, 5000000)
        self.assertEqual(agent.state.tenure, 12)
        # Should not ask for market_value, loan_amount, or tenure next!

    def test_13_adversarial_contradiction(self):
        """Test 13 Adversarial: Contradiction takes latest valid answer (Residential -> Agricultural -> Disqualify)."""
        agent = ConversationalAgent()
        res = agent.process_utterance("It is residential... actually no, it is agricultural.")
        self.assertEqual(agent.state.property_type, "Agricultural")
        self.assertEqual(res["action"], "DISQUALIFIED")

    def test_14_adversarial_multiple_answers(self):
        """Test 14 Adversarial: Multiple answers in one single sentence."""
        agent = ConversationalAgent()
        res = agent.process_utterance("It is my own residential property, original documents are available, I need ₹40 lakh and I want 10 years.")
        self.assertEqual(agent.state.property_type, "Residential")
        self.assertEqual(agent.state.ownership, "Sole")
        self.assertEqual(agent.state.documents, True)
        self.assertEqual(agent.state.loan_amount, 4000000)
        self.assertEqual(agent.state.tenure, 10)

    def test_15_adversarial_interruption_rag(self):
        """Test 15 Adversarial: Product query interruption handled with RAG context."""
        agent = ConversationalAgent()
        res = agent.process_utterance("What is the exact interest rate?")
        self.assertIn("exact interest rate will be provided by our senior loan expert", res["agent_response"].lower())
        self.assertTrue(len(res["rag_context_used"]) > 0)

    def test_16_adversarial_ambiguous_documents(self):
        """Test 16 Adversarial: Ambiguous document answer prompts clarification."""
        agent = ConversationalAgent()
        res = agent.process_utterance("The papers are probably somewhere.")
        self.assertIsNone(agent.state.documents)
        self.assertIn("clarify", res["agent_response"].lower())


def run_all_tests():
    """Runs all 16 test cases and returns summary dict."""
    suite = unittest.TestLoader().loadTestsFromTestCase(TestHomeCreditVoiceAgent)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return {
        "total": result.testsRun,
        "failures": len(result.failures),
        "errors": len(result.errors),
        "passed": result.testsRun - len(result.failures) - len(result.errors),
        "successful": result.wasSuccessful()
    }

if __name__ == "__main__":
    unittest.main()
