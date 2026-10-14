# AsistLine AI: Slide-by-Slide Speaker Notes
## Simple, Effective & Conversational Presenter Script (12 Slides)

---

### Slide 1: Title & Description
**What to Say:**  
> "Hello everyone, thank you for joining today. I am presenting **AsistLine AI**—a real-time AI voice platform built for customer support and contact centers. In simple terms, our AI voice agents answer customer calls instantly on the first ring, speak only verified company facts without making anything up, and cut call center costs by 75% to 85%."

---

### Slide 2: The Problem (Why Call Centers Are Struggling)
**What to Say:**  
> "Let’s look at why call centers are under so much pressure today.  
> First, employee turnover is huge—around 30% to 45% of call center workers quit every single year. Companies are constantly spending money on hiring and retraining.  
> Second, in places like California, call center reps cost $35 to $50 an hour when you include taxes and benefits. Because agents spend time waiting for calls, taking breaks, and typing notes, businesses end up paying **$1.00 to $1.70 for every single minute an agent is actually talking to a customer**.  
> On top of that, customers hate waiting on hold for simple questions like 'Where is my order?'. And if you just plug a regular AI bot into the phone, it risks hallucinating fake refund policies or wrong prices, which creates legal headaches."

---

### Slide 3: The Solution (What AsistLine AI Does)
**What to Say:**  
> "AsistLine AI solves these problems completely.  
> First, it answers on the very first ring, 24 hours a day, 7 days a week—with zero wait time.  
> Second, it has **zero fake answers**. The AI is strictly locked to your company's official documents and database. If an answer isn't in your files, it politely tells the caller: 'I don't have that information, let me connect you to a team member.'  
> Third, the conversation feels natural and fast—the AI responds in under 1.5 seconds. If the customer interrupts while the AI is speaking, the AI stops talking immediately in less than 300 milliseconds.  
> And finally, if a human is needed, the AI transfers the call in under two seconds with the full call summary already on the agent's screen."

---

### Slide 4: Cost Breakdown of an AI Voice Call
**What to Say:**  
> "Here is how the cost works. An AI voice call costs between **8 cents and 25 cents per active minute**—and you only pay when someone is actually talking.  
> This cost covers the entire pipeline:  
> 1. Hearing—using speech-to-text to turn voice into text.  
> 2. Thinking—using fast AI models like Gemini Flash to understand the caller.  
> 3. Speaking—using realistic voice tools like ElevenLabs to speak back naturally.  
> 4. Audio transport—connecting the call over WebRTC or phone lines.  
> 5. Our platform—which handles safety checks, conversation rules, and CRM logging.  
> When you add all five layers together, you get an all-in cost of around 8 to 25 cents per minute, which is 75% to 85% cheaper than human agents."

---

### Slide 5: How AI Tokens Work During a Phone Call
**What to Say:**  
> "Let's explain how AI pricing works during a phone call.  
> Most people speak around 150 words per minute. On a phone call, every time the customer speaks, the AI re-reads the earlier conversation plus your company guidelines so it never loses context.  
> Over a 3-minute call, the AI reads around 6,000 to 10,000 input tokens, while keeping its own spoken answers short and clear—around 50 words per reply.  
> By using fast, lightweight models like Gemini 2.5 Flash, the AI thinking cost stays extremely low—less than 1 cent per minute for routine support, appointments, and order lookups."

---

### Slide 6: Human Agent vs. AI Voice Agent (California Cost Comparison)
**What to Say:**  
> "This slide shows the direct dollar savings.  
> In California, human agents cost $35 to $50 an hour loaded. Because agents only spend 50% to 60% of their shift on active calls, their effective speaking cost is $1.00 to $1.70 per minute.  
> AsistLine AI costs only 8 to 25 cents per minute, meaning you save between **92 cents and $1.45 every single minute**.  
> - A quick 1.5-minute call that costs over $2.00 with a human costs just 20 cents with AI—saving $2.00 per call.  
> - A standard 3.5-minute call drops from around $4.50 to 45 cents—saving $4.00 per call.  
> - A 7-minute call saves around $8.00. That is an immediate 75% to 85% net savings across the board."

---

### Slide 7: Human vs. AI Capabilities (Operational Scalability)
**What to Say:**  
> "Cost is only half the story; scalability is the other half.  
> A human agent can only handle one phone call at a time. When calls spike, customers get stuck on hold. AsistLine AI can handle hundreds or thousands of calls simultaneously with zero waiting.  
> It works 24/7 with no overtime or holiday premiums.  
> It eliminates post-call wrap-up errors because it generates clean, structured notes and syncs with your CRM automatically.  
> And while human call centers deal with 30%+ annual turnover, the AI never quits. Any policy update or script change takes effect instantly across all calls."

---

### Slide 8: The Hybrid Model (AI + Human Teamwork)
**What to Say:**  
> "Our goal is not to eliminate human workers—our goal is to make them more effective through a Tiered Hybrid Strategy.  
> - **Tier 1 belongs to the AI**, handling 70% to 80% of routine call volume. It answers common questions, checks order status, collects customer info, and handles 24/7 after-hours calls.  
> - **Tier 2 belongs to Human Specialists**, who handle the remaining 20% to 30%. They focus on difficult problems, upset customers, and VIP sales.  
> If an issue is complex or a caller is frustrated, the AI transfers the call in under two seconds. The human agent sees a pop-up window with the caller's name, problem, and live transcript—so the customer never has to repeat themselves."

---

### Slide 9: How a Call Works (Step-by-Step Workflow)
**What to Say:**  
> "Here is the journey of a call from start to finish:  
> 1. The customer clicks 'Call Support' on a webpage, connecting immediately over WebRTC.  
> 2. The AI greets the customer warmly in English or Hindi.  
> 3. As the customer speaks, our system filters background noise and turns voice to text in real time.  
> 4. The AI checks your verified company files. If the customer asks for account details, it verifies their identity first.  
> 5. The AI speaks back the grounded answer in under 1.5 seconds.  
> 6. If the customer interrupts at any point, the AI immediately stops talking in under 300 milliseconds.  
> 7. And if a human is needed, the transfer happens inside the exact same audio room in under two seconds."

---

### Slide 10: System Architecture & Tech Stack
**What to Say:**  
> "We built AsistLine AI on modern, production-ready technologies:  
> - We use **FastAPI** in Python for a fast, secure backend.  
> - **LiveKit** manages our real-time WebRTC audio room so the caller, the AI, and the human can share the same room.  
> - **Silero VAD** detects speech and makes instant interruption handling possible.  
> - **ElevenLabs** powers our real-time transcription and lifelike voice synthesis.  
> - **Gemini 2.5 Flash** acts as our fast reasoning brain for sub-second responses.  
> - **LangGraph** enforces strict conversation rules so the AI never gets confused or stuck in loops.  
> - **PostgreSQL with pgvector** keeps all company documents, vectors, and call logs in one secure, isolated database.  
> - And modern **React** powers our caller screen, agent softphone, and supervisor dashboard."

---

### Slide 11: Real Results & Business Impact
**What to Say:**  
> "Here are the business results you can expect:  
> - Over 70% of routine calls are fully resolved by the AI without human intervention.  
> - Average call handle times drop by 50%—from 6 minutes down to under 3 minutes.  
> - Average call costs drop from over $4.50 down to less than 75 cents.  
> - And warm transfers happen in under two seconds.  
> Looking at our roadmap: Phase 1 is live right now with browser-based calling and human handoff. Phase 2 will bring direct phone number support through SIP trunking and caller voice verification."

---

### Slide 12: Thank You (Closing Slide)
**What to Say:**  
> "Thank you very much for your time. AsistLine AI is ready to help contact centers reduce costs, eliminate hold times, and deliver better customer experiences. I'd love to answer any questions or show you a live interactive demo now."
