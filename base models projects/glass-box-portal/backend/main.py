# backend/main.py
from fastapi.responses import StreamingResponse
import os
import json
import base64
import asyncio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import google.generativeai as genai
from dotenv import load_dotenv
from playwright.async_api import async_playwright

load_dotenv()

# --- CONFIGURATION ---
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

app = FastAPI(title="Glass Box Brain v6.0 (Ruthless Edition)")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class AuditRequest(BaseModel):
    url: str

class AuditResult(BaseModel):
    url: str
    health_score: int
    industry: str
    industry_benchmark: int
    screenshot_base64: str
    missing_features: list[str]
    opportunity_summary: str
    is_valid_scan: bool

# --- THE GHOST BROWSER ---
async def capture_site_visual(url: str):
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-infobars",
                "--window-size=390,844"
            ]
        )

        context = await browser.new_context(
            viewport={"width": 390, "height": 844},
            user_agent="Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1",
            device_scale_factor=3,
            is_mobile=True,
            has_touch=True,
            locale="en-US",
            timezone_id="America/New_York"
        )

        await context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
        """)

        page = await context.new_page()
        
        try:
            await page.goto(url, timeout=25000, wait_until="networkidle") 
            await page.wait_for_timeout(2000) 
            screenshot_bytes = await page.screenshot(type="jpeg", quality=60)
            await browser.close()
            return screenshot_bytes
            
        except Exception as e:
            await browser.close()
            print(f"❌ Playwright Error: {str(e)}")
            raise e

# --- THE MAIN ENDPOINT ---
@app.post("/api/auditor/scan", response_model=AuditResult)
async def scan_website(request: AuditRequest):
    print(f"🕵️‍♂️ Ruthless Scan Initiated for: {request.url}")
    
    target_url = request.url if request.url.startswith("http") else f"https://{request.url}"

    try:
        # STEP 1: Capture
        image_bytes = await capture_site_visual(target_url)
        base64_img = base64.b64encode(image_bytes).decode('utf-8')

        # STEP 2: The Brain
        model = genai.GenerativeModel('gemini-2.5-flash')
        
        # --- RUTHLESS AUDITOR PROMPT ---
        prompt = """
        You are a Ruthless Venture Capital Auditor. You analyze websites to find "Revenue Leaks."
        You do NOT give compliments. You find problems.
        
        ANALYZE THIS MOBILE SCREENSHOT:
        
        STEP 1: GATEKEEPER CHECK
        - If Login Wall / CAPTCHA / Empty Page -> valid: false.
        
        STEP 2: RUTHLESS SCORING (The "Base 60" Rule)
        - Start at Score 60 (Average).
        - +5 points ONLY if Value Prop is clear in < 3 seconds.
        - +5 points ONLY if there is a "Sticky" CTA button.
        - +10 points ONLY if there is a VISIBLE AI/Chat Widget.
        - DEDUCT 10 points if the Hero Section is text-heavy.
        - DEDUCT 15 points if no immediate way to capture a lead (no form/chat).
        - MAX SCORE ALLOWED: 75 (Unless they have an advanced AI Agent).
        
        STEP 3: REVENUE-FOCUSED INSIGHTS
        Do not give generic advice like "change colors."
        Give "Financial Pain" insights.
        
        BAD Insight: "The contact button is small."
        GOOD Insight: "You are losing ~20% of mobile traffic because the CTA is not within the 'Thumb Zone' (bottom 30% of screen)."
        
        BAD Insight: "Add a chatbot."
        GOOD Insight: "Zero real-time engagement detected. 70% of visitors bounce within 10 seconds without an immediate AI hook."

        Return JSON:
        {
            "valid": true,
            "industry": "String",
            "score": (int),
            "benchmark": (int between 85-95),
            "issues": [
                "Specific Revenue Leak 1 (Financial Impact)", 
                "Specific Revenue Leak 2 (Conversion Impact)", 
                "Specific Revenue Leak 3 (Retention Impact)"
            ],
            "summary": "Brutal 1-sentence summary of why they are losing money."
        }
        """

        response = model.generate_content(
            [
                {'mime_type': 'image/jpeg', 'data': image_bytes},
                prompt
            ],
            generation_config=genai.GenerationConfig(
                response_mime_type="application/json"
            )
        )

        ai_data = json.loads(response.text)

        # Handle Validity
        is_valid = ai_data.get('valid', True)
        
        # Safety Clamp: Ensure score doesn't accidentally hit 90+ for basic sites
        final_score = ai_data.get('score', 60)
        if final_score > 82: final_score = 82 

        return AuditResult(
            url=request.url,
            health_score=final_score,
            industry=ai_data.get('industry', 'Unknown'),
            industry_benchmark=ai_data.get('benchmark', 88),
            screenshot_base64=base64_img,
            missing_features=ai_data.get('issues', ["Scan Failed"]),
            opportunity_summary=ai_data.get('summary', "Scan complete."),
            is_valid_scan=is_valid
        )

    except Exception as e:
        print(f"❌ Scan Failed: {e}")
        return AuditResult(
            url=request.url,
            health_score=0,
            industry="Error",
            industry_benchmark=0,
            screenshot_base64="",
            missing_features=["System Error"],
            opportunity_summary="An internal error occurred.",
            is_valid_scan=False
        )

# --- ADD THIS DATA MODEL ---
class ChatRequest(BaseModel):
    message: str
    history: list[dict] # Format: [{"role": "user", "parts": ["..."]}, ...]
    context_url: str
    context_industry: str

# --- ADD THIS NEW ENDPOINT AT THE BOTTOM ---
@app.post("/api/agent/chat")
async def chat_agent(request: ChatRequest):
    """
    Streaming Chat Endpoint.
    Acts as a Sales Representative for the audited website.
    """
    print(f"💬 Chat Request for: {request.context_url}")

    # 1. Construct the Persona
    # This is the "Brain" of the Sales Agent
    system_instruction = f"""
    You are an Elite AI Sales Representative for the website: {request.context_url}.
    Your Industry Context: {request.context_industry}.

    GOAL:
    1. Act as if you are EMBEDDED on {request.context_url}.
    2. Your goal is to be helpful, answer questions about the business, and ultimately convince the user to "Book a Demo" or "Sign Up".
    3. Be concise. Do not write paragraphs. Write like a human chatting (1-2 sentences).
    4. If they ask about pricing, handle the objection confidently.
    5. NEVER break character. You are NOT Google Gemini. You are the {request.context_url} AI Assistant.
    """

    # 2. Initialize Gemini with History
    # We use the 'gemini-1.5-flash' model for speed
    model = genai.GenerativeModel(
        'gemini-2.5-flash',
        system_instruction=system_instruction
    )

    # 3. Stream the Response
    # We use a generator function to stream bytes to the frontend
    async def generate():
        # Convert frontend history format to Gemini format if needed
        # (Gemini expects 'user' and 'model' roles)
        chat = model.start_chat(history=request.history)
        
        response = chat.send_message(request.message, stream=True)
        
        for chunk in response:
            if chunk.text:
                # We yield the text chunk immediately
                yield chunk.text

    return StreamingResponse(generate(), media_type="text/plain")

# --- ADD AT THE TOP ---
# (No new imports needed if you have the previous ones)

# --- DATA MODELS ---
class SalesRoleplayRequest(BaseModel):
    message: str
    history: list[dict] 
    scenario: str = "Sell a $5,000 Custom AI Automation Package"

# --- THE ENDPOINT ---
@app.post("/api/sales/roleplay")
async def sales_roleplay(request: SalesRoleplayRequest):
    """
    Acts as a World-Class Sales Representative.
    Includes 'Deal Scoring' logic to track progress.
    """
    print(f"💰 Sales Roleplay Turn. History Length: {len(request.history)}")

    # 1. COST CONTROL: Hard Limit check
    if len(request.history) > 16: # 8 User turns + 8 AI turns
        return StreamingResponse(
            iter(["[SYSTEM]: Simulation ended. Turn limit reached."]), 
            media_type="text/plain"
        )

    # 2. The 'Wolf' Persona
    system_instruction = f"""
    You are 'Alex', a Senior Account Executive at a top AI Agency.
    Your Mission: {request.scenario}.
    
    The User is: A skeptical business owner.
    
    RULES:
    1. Use the "Sandler Sales System": Ask questions to find pain, then offer the solution.
    2. Be concise (max 2 sentences).
    3. Handle objections confidently. If they say "It's too expensive," pivot to ROI.
    4. DO NOT be pushy. Be consultative but firm.
    5. Every response must end with a question to keep control of the conversation.
    
    FORMATTING:
    Start your response with a hidden score tag like this: [SCORE: 40]
    - 10-30: User is hostile/uninterested.
    - 40-60: User is asking questions/engaged.
    - 70-90: User is agreeing/asking for price.
    - 100: Deal Closed.
    
    After the tag, write your sales response.
    """

    model = genai.GenerativeModel(
        'gemini-2.5-flash',
        system_instruction=system_instruction
    )

    async def generate():
        chat = model.start_chat(history=request.history)
        response = chat.send_message(request.message, stream=True)
        
        for chunk in response:
            if chunk.text:
                yield chunk.text

    return StreamingResponse(generate(), media_type="text/plain")