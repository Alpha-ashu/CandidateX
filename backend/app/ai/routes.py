"""
AI Assistant routes for conversational AI support.
"""
import logging
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app.models.user import User
from app.auth.dependencies import get_current_user, get_optional_current_user
from app.ai.service import ai_service

# Import Google AI
try:
    import google.generativeai as genai
except ImportError:
    genai = None

logger = logging.getLogger(__name__)

router = APIRouter()

class ChatMessage(BaseModel):
    role: str  # "user" or "assistant"
    content: str
    timestamp: Optional[str] = None

class ChatRequest(BaseModel):
    message: str
    model: str = "grok"  # Default to grok-like behavior
    context: Optional[List[ChatMessage]] = None

class ChatResponse(BaseModel):
    response: str
    model_used: str
    confidence: Optional[float] = None

class QuickAction(BaseModel):
    label: str
    prompt: str
    category: str

@router.post("/chat", response_model=ChatResponse)
async def chat_with_ai(
    request: ChatRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Chat with AI assistant using specified model.
    """
    try:
        # Build context from previous messages
        context = ""
        if request.context:
            # Include last 5 messages for context
            recent_messages = request.context[-5:]
            context = "\n".join([
                f"{msg.role}: {msg.content}"
                for msg in recent_messages
            ])

        # Generate AI response based on selected model
        response = await generate_ai_response(
            message=request.message,
            model=request.model,
            context=context,
            user_role=current_user.role.value
        )

        return ChatResponse(
            response=response["content"],
            model_used=request.model,
            confidence=response.get("confidence", 0.8)
        )

    except Exception as e:
        logger.error(f"AI chat failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="AI service temporarily unavailable"
        )

@router.get("/models")
async def get_available_models(current_user: User = Depends(get_current_user)):
    """
    Get list of available AI models.
    """
    models = [
        {
            "id": "grok",
            "name": "Grok",
            "description": "xAI's Grok - helpful, truthful, and witty AI assistant",
            "capabilities": ["interview_prep", "career_advice", "general_questions"],
            "available": True
        },
        {
            "id": "gemini",
            "name": "Gemini Pro",
            "description": "Google's advanced AI model for comprehensive responses",
            "capabilities": ["interview_prep", "technical_analysis", "general_questions"],
            "available": bool(ai_service.google_client)
        },
        {
            "id": "gpt-4",
            "name": "GPT-4",
            "description": "OpenAI's most advanced language model",
            "capabilities": ["interview_prep", "career_advice", "technical_analysis"],
            "available": bool(ai_service.openai_client)
        },
        {
            "id": "claude",
            "name": "Claude",
            "description": "Anthropic's helpful and safe AI assistant",
            "capabilities": ["interview_prep", "ethical_advice", "general_questions"],
            "available": False  # Not implemented yet
        }
    ]

    return {"models": models}

@router.get("/quick-actions")
async def get_quick_actions(current_user: User = Depends(get_current_user)):
    """
    Get quick action prompts for AI assistant.
    """
    quick_actions = [
        {
            "label": "STAR Method Tips",
            "prompt": "Explain the STAR method for behavioral interview questions with examples",
            "category": "interview_technique"
        },
        {
            "label": "Common Questions",
            "prompt": "What are the 10 most common interview questions and how should I answer them?",
            "category": "interview_prep"
        },
        {
            "label": "Mock Interview",
            "prompt": "Give me a practice interview question for a software engineer position and evaluate my response",
            "category": "practice"
        },
        {
            "label": "Salary Negotiation",
            "prompt": "How should I approach salary negotiation in a job interview?",
            "category": "career_advice"
        },
        {
            "label": "Body Language Tips",
            "prompt": "What body language should I use during video interviews?",
            "category": "interview_technique"
        },
        {
            "label": "Follow-up Questions",
            "prompt": "What smart questions should I ask the interviewer at the end of the interview?",
            "category": "interview_technique"
        },
        {
            "label": "Resume Review",
            "prompt": "How can I improve my resume for tech positions?",
            "category": "career_advice"
        },
        {
            "label": "Technical Interview Prep",
            "prompt": "How should I prepare for technical coding interviews?",
            "category": "interview_prep"
        }
    ]

    return {"quick_actions": quick_actions}

@router.get("/suggested-topics")
async def get_suggested_topics(current_user: User = Depends(get_current_user)):
    """
    Get suggested conversation topics.
    """
    topics = [
        "STAR Method Practice",
        "Technical Interview Prep",
        "Behavioral Questions",
        "Salary Negotiation",
        "Body Language Tips",
        "Follow-up Questions",
        "Resume Optimization",
        "Career Transition Advice",
        "Leadership Interview Questions",
        "Remote Work Interview Tips"
    ]

    return {"topics": topics}

async def generate_ai_response(
    message: str,
    model: str,
    context: str = "",
    user_role: str = "candidate"
) -> Dict[str, Any]:
    """
    Generate AI response based on selected model and user context.
    """
    # Build system prompt based on model
    system_prompts = {
        "grok": """You are Grok, a helpful and maximally truthful AI built by xAI.
You are not based on any other companies and their models. You are witty, helpful,
and have a rebellious streak. You provide clear, direct answers and don't shy away
from difficult topics. You're particularly knowledgeable about technology, science,
and career development.

For interview preparation, you should:
- Be encouraging and supportive
- Provide specific, actionable advice
- Use humor when appropriate but stay professional
- Give examples and scenarios
- Be honest about what works and what doesn't
- Focus on helping the user succeed

Current user is a {user_role} looking for interview/career advice.""",

        "gemini": """You are Gemini, Google's advanced AI assistant.
You are helpful, knowledgeable, and provide comprehensive responses.
You excel at analysis, problem-solving, and giving detailed explanations.

For interview preparation, you should:
- Provide thorough, well-structured answers
- Include examples and best practices
- Be encouraging and professional
- Focus on practical advice
- Use clear, organized responses

Current user is a {user_role} seeking interview assistance.""",

        "gpt-4": """You are GPT-4, OpenAI's advanced language model.
You are knowledgeable, helpful, and provide detailed responses.
You excel at understanding context and giving nuanced advice.

For interview preparation, you should:
- Be comprehensive and detailed
- Provide examples and scenarios
- Be professional and encouraging
- Focus on proven strategies
- Use structured, clear responses

Current user is a {user_role} preparing for interviews.""",

        "claude": """You are Claude, an AI built by Anthropic.
You are helpful, honest, and focused on being maximally truthful.
You provide clear, direct answers and prioritize user safety and success.

For interview preparation, you should:
- Be encouraging and supportive
- Provide ethical, practical advice
- Be clear and direct
- Focus on helping users succeed
- Use structured responses

Current user is a {user_role} seeking career guidance."""
    }

    system_prompt = system_prompts.get(model, system_prompts["grok"]).format(user_role=user_role)

    # Build full prompt
    full_prompt = f"{system_prompt}\n\n"
    if context:
        full_prompt += f"Previous conversation:\n{context}\n\n"
    full_prompt += f"User: {message}\n\nAssistant:"

    try:
        if model == "grok" or model == "gemini":
            # Use Google AI (Gemini)
            if ai_service.google_client:
                response = ai_service.google_client.generate_content(
                    full_prompt,
                    generation_config=genai.types.GenerationConfig(
                        temperature=0.7 if model == "grok" else 0.3,
                        max_output_tokens=2000,
                    )
                )
                content = response.text.strip()
                confidence = 0.85
            else:
                content = generate_fallback_response(message, model)
                confidence = 0.5

        elif model == "gpt-4":
            # Use OpenAI
            if ai_service.openai_client:
                response = ai_service.openai_client.chat.completions.create(
                    model="gpt-4",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": message}
                    ],
                    temperature=0.7,
                    max_tokens=2000
                )
                content = response.choices[0].message.content.strip()
                confidence = 0.9
            else:
                content = generate_fallback_response(message, model)
                confidence = 0.5

        else:
            # Default to grok-like behavior
            content = generate_fallback_response(message, "grok")
            confidence = 0.6

        return {
            "content": content,
            "confidence": confidence,
            "model": model
        }

    except Exception as e:
        logger.error(f"AI response generation failed for model {model}: {e}")
        return {
            "content": generate_fallback_response(message, model),
            "confidence": 0.3,
            "model": model
        }

def generate_fallback_response(message: str, model: str) -> str:
    """
    Generate fallback response when AI services are unavailable.
    """
    model_personalities = {
        "grok": "helpful, witty, and truthful AI assistant",
        "gemini": "comprehensive and analytical AI assistant",
        "gpt-4": "detailed and knowledgeable AI assistant",
        "claude": "helpful and ethical AI assistant"
    }

    personality = model_personalities.get(model, "helpful AI assistant")

    if "star method" in message.lower():
        return """The STAR method is a powerful framework for answering behavioral interview questions:

**S - Situation**: Set the context by describing the situation you were in
**T - Task**: Explain your specific responsibility or challenge
**A - Action**: Detail the steps you took to address the situation
**R - Result**: Share the outcomes and what you learned

Example: "In my previous role (Situation), I was tasked with leading a team project with a tight deadline (Task). I organized daily stand-ups and delegated tasks based on team strengths (Action). We delivered the project on time and received positive feedback from stakeholders (Result)."

This method helps you provide structured, compelling answers that demonstrate your skills effectively."""

    elif "common questions" in message.lower():
        return """Here are 10 of the most common interview questions and tips for answering them:

1. **"Tell me about yourself"** - Keep it professional, focus on career highlights (1-2 minutes)

2. **"What are your strengths?"** - Choose 2-3 relevant strengths with examples

3. **"What are your weaknesses?"** - Pick a real weakness and show how you're improving it

4. **"Why do you want this job?"** - Connect your goals with company values and role requirements

5. **"Where do you see yourself in 5 years?"** - Show ambition but realistic career progression

6. **"Why did you leave your last job?"** - Be positive, focus on growth opportunities

7. **"Tell me about a challenge you faced"** - Use STAR method, show problem-solving skills

8. **"What are your salary expectations?"** - Research market rates, give a range if possible

9. **"Do you have any questions for us?"** - Always prepare 2-3 thoughtful questions

10. **"Why should we hire you?"** - Summarize your unique value proposition

Remember to prepare specific examples and practice your answers out loud!"""

    else:
        return f"""I'm a {personality} here to help with your interview preparation. I can assist with:

• STAR method explanations and practice
• Common interview questions and answers
• Technical interview preparation
• Career advice and salary negotiation
• Resume and LinkedIn optimization
• Body language and virtual interview tips

What specific aspect of interview preparation would you like help with? Feel free to ask me anything - I'm here to help you succeed!"""

# Import here to avoid circular imports
try:
    import google.generativeai as genai
except ImportError:
    genai = None

# Make genai available in the function scope
genai_client = genai
