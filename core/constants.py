from enum import Enum


class SessionTypeEnum(Enum):
    EXAM_PREPARATION_GUIDE = "Exam Preparation Guide"
    TECHNICAL_MANUAL_INTERPRETER = "Technical Manual Interpreter"
    LEGAL_DOCUMENT_ANALYSIS = "Legal Document Analysis"
    NUTRITIONAL_LABEL_INTERPRETER = "Nutritional Label Interpreter"
    FINANCIAL_REPORT_ANALYSIS = "Financial Report Analysis"
    CONTRACT_REVIEW_ASSISTANT = "Contract Review Assistant"

    @classmethod
    def choices(cls):
        return [(member.name.lower(), member.value) for member in cls]

    @classmethod
    def as_dict(cls):
        return {
            member.name.lower(): member.value for member in cls
        }

PREDEFINED_QUESTIONS_MAP = {
    "exam_preparation_guide": {
        "summarize": "Summarize the key concepts in this study material.",
        "keywords": "Extract important terms and definitions.",
        "details": "Provide a detailed explanation of the topics covered.",
        "practice": "Generate sample questions to test my understanding.",
        "study_tips": "Suggest effective study techniques for this material.",
        "explain_difficult_topics": "Break down the most challenging parts in simple terms.",
    },
    "technical_manual_interpreter": {
        "summarize": "Summarize the main points of this technical manual.",
        "keywords": "Extract key technical terms and instructions.",
        "details": "Provide a detailed explanation of the procedures and guidelines.",
        "quick_summary": "Offer a brief summary of the manual's content.",
        "step_by_step": "Guide me through the process detailed in the instructions.",
        "highlight_warnings": "Identify any critical warnings or cautions mentioned.",
    },
    "Legal Document Analysis": {
        "summarize": "Summarize the key clauses and terms in this legal document.",
        "keywords": "Extract important legal terms and conditions.",
        "details": "Analyze the implications of specific clauses.",
        "identify_risks": "Point out potential legal risks or loopholes.",
        "compare_with_standard": "Compare this document with standard legal agreements.",
        "explain_legal_jargon": "Define and explain any complex legal language.",
    },
    "nutritional_label_interpreter": {
        "summarize": "Summarize the nutritional information in this label.",
        "keywords": "Extract key ingredients and allergens.",
        "details": "Provide a detailed analysis of the nutritional content.",
        "compare_nutrition": "Compare the nutritional value with recommended daily values.",
        "ingredient_health": "Explain the health benefits or risks of the listed ingredients.",
        "dietary_recommendations": "Suggest dietary adjustments based on this label.",
    },
    "financial_report_analysis": {
        "summarize": "Summarize the key financial metrics in this report.",
        "keywords": "Extract important financial terms and figures.",
        "details": "Provide a detailed analysis of the financial data.",
        "analyze_trends": "Identify recent trends and forecast future performance.",
        "risk_evaluation": "Assess potential financial risks in the report.",
        "investment_opportunities": "Highlight promising investment opportunities from the data.",
    },
    "contract_review_assistant": {
        "summarize": "Summarize the main points of this contract.",
        "keywords": "Extract key terms and obligations.",
        "details": "Analyze the implications of specific contract clauses.",
        "red_flags": "Identify any red flags or unusual clauses within the contract.",
        "negotiation_tips": "Offer advice to negotiate problematic terms.",
        "constraint_identification": "Point out any constraints or limitations imposed by the contract.",  # noqa: E501
    },
}

IDENTITY_KEYWORDS = ["who are you", "what are you", "your name", "your identity"]
MODEL_KEYWORDS = ["which model are you", "what model are you", "powered by", "based on"]
