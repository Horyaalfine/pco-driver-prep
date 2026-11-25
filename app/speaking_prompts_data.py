"""
Original speaking-practice content for the real ELR assessment (a live
speaking & listening interview with a human interlocutor, not a written
test). Each prompt is studied, then rehearsed out loud by the learner —
there's no recording/grading here, just a realistic question, a model
answer showing the kind of structure and fluency examiners look for, and
a few concrete tips.

Topics are modelled on the general shape of SELT-style speaking interviews
(personal questions, then scenario/topic-based discussion) applied to the
private hire driving context — not copied from any copyrighted test paper.
"""

SPEAKING_PROMPTS = [
    # --- Personal & background ---
    {
        "topic": "Personal & background",
        "prompt_text": "Tell me about yourself and why you want to become a private hire driver in London.",
        "model_answer": (
            "I've lived in London for several years and I'm looking for work that gives me flexibility "
            "and lets me meet new people every day. I enjoy driving, I know the city reasonably well "
            "already, and I like the idea of being my own boss while still being part of a reliable "
            "service. I've also looked into what's expected of a private hire driver — things like "
            "safety, punctuality and good customer service — and I feel confident I can meet those "
            "standards."
        ),
        "tips": [
            "Keep it to 3-4 sentences — the interviewer wants fluency, not a life story.",
            "Mention something concrete (flexibility, knowing the city, customer service) rather than only 'I need a job.'",
            "Use full sentences with natural linking words (and, because, also) rather than short fragments.",
        ],
    },
    {
        "topic": "Personal & background",
        "prompt_text": "What does a typical working day look like for you?",
        "model_answer": (
            "A typical day usually starts early in the morning. I check my vehicle first — tyres, lights, "
            "fuel — before I start taking any bookings. Then I'll usually work through the morning, take "
            "a short break around midday, and continue into the afternoon depending on demand. I try to "
            "plan my breaks around quieter periods so I'm not losing bookings."
        ),
        "tips": [
            "Use sequencing words — first, then, after that, finally — to show a clear timeline.",
            "Show awareness of real driver responsibilities (vehicle checks) even in a personal question.",
        ],
    },
    {
        "topic": "Personal & background",
        "prompt_text": "Describe a job or situation where you had to deal with the public. What did you learn from it?",
        "model_answer": (
            "In a previous job I worked on a shop counter, so I was dealing with customers all day. I "
            "learned that staying calm and listening properly makes a much bigger difference than people "
            "expect — most complaints get much easier to resolve once the customer feels heard. I also "
            "learned not to take things personally, even when someone was frustrated about something "
            "that wasn't really my fault."
        ),
        "tips": [
            "Give a specific example rather than a general statement — it's easier to speak fluently about something concrete.",
            "End with what you learned, since the question explicitly asks for it.",
        ],
    },
    {
        "topic": "Personal & background",
        "prompt_text": "How would you describe your English speaking and listening skills, and how have you developed them?",
        "model_answer": (
            "I'd say my spoken English is good enough for everyday conversation and for work. I've "
            "developed it mainly through daily use — speaking with colleagues, customers and friends — "
            "and I also try to watch the news or listen to the radio in English, which helps with "
            "understanding different accents and faster speech."
        ),
        "tips": [
            "Be honest and specific — naming how you practise (news, radio, conversation) sounds more convincing than a vague claim.",
            "This is a good moment to naturally demonstrate a wider vocabulary, since it's literally the topic.",
        ],
    },

    # --- Driving & London knowledge ---
    {
        "topic": "Driving & London knowledge",
        "prompt_text": "A passenger asks you to recommend a quick route to avoid traffic. How would you respond?",
        "model_answer": (
            "I'd tell them honestly what I know — for example, that a particular road tends to be busy "
            "at that time of day, and suggest an alternative if I'm confident about it. If I'm not sure, "
            "I'd say so rather than guessing, and explain that I'd rather check the satnav to be accurate "
            "than give them wrong information."
        ),
        "tips": [
            "It's fine — and often better — to say 'I'm not sure, let me check' rather than inventing an answer.",
            "Show honesty and good judgement, not just knowledge — examiners are also assessing how you communicate under realistic pressure.",
        ],
    },
    {
        "topic": "Driving & London knowledge",
        "prompt_text": "Explain how you would give directions to someone on the phone who is trying to find your pickup location.",
        "model_answer": (
            "I'd start by asking what they can see around them — a shop, a street sign, a landmark — "
            "so I understand their exact position. Then I'd give clear, short directions, one step at a "
            "time: for example, 'turn left at the pharmacy, then I'm the second car on the right.' I'd "
            "also stay on the phone until they've confirmed they can see me, to avoid any confusion."
        ),
        "tips": [
            "Use clear sequencing (first, then) and simple, direct sentences — this is exactly how a real interlocutor expects a directions answer to sound.",
            "Mention confirming understanding at the end — it shows good communication, not just driving knowledge.",
        ],
    },
    {
        "topic": "Driving & London knowledge",
        "prompt_text": "What would you do if your satnav stopped working during a journey?",
        "model_answer": (
            "I'd stay calm and pull over safely if I needed to work out an alternative, rather than trying "
            "to fix it while driving. If I knew the area, I'd continue using my own knowledge of the main "
            "roads. If not, I'd be upfront with the passenger that the satnav had failed and that I needed "
            "a moment to find another way, rather than guessing and getting lost."
        ),
        "tips": [
            "Safety first — mention pulling over, not fiddling with a device while driving.",
            "Honesty with the passenger is a theme examiners like to hear — it shows professionalism.",
        ],
    },
    {
        "topic": "Driving & London knowledge",
        "prompt_text": "Describe the difference between a licensed taxi and a private hire vehicle.",
        "model_answer": (
            "A licensed taxi, like a black cab, can be hailed directly in the street or picked up at a "
            "rank, and it has a meter for the fare. A private hire vehicle, which is what I'd be driving, "
            "can only be booked in advance through a licensed operator — it can't be hailed on the street "
            "or accept a direct approach from a passenger."
        ),
        "tips": [
            "This is a factual/explanatory answer — organise it clearly with a contrast structure ('a taxi does X, whereas private hire does Y').",
            "Being accurate here also reflects genuine licensing knowledge, which reassures the examiner.",
        ],
    },

    # --- Customer service scenarios ---
    {
        "topic": "Customer service scenarios",
        "prompt_text": "A passenger is running late and asks you to drive faster than the speed limit. How would you respond?",
        "model_answer": (
            "I'd explain politely that I can't break the speed limit, even if they're in a hurry, because "
            "it's not safe and it's against the law. I'd reassure them that I'll drive efficiently and "
            "choose the most direct legal route, but that their safety — and everyone else's on the road "
            "— comes first."
        ),
        "tips": [
            "This tests judgement as much as language — always put safety/legality first in your answer.",
            "A polite refusal plus a reassurance ('I will still try to help') is a stronger answer than a flat no.",
        ],
    },
    {
        "topic": "Customer service scenarios",
        "prompt_text": "A passenger complains that the car isn't clean enough. How do you handle this?",
        "model_answer": (
            "I'd apologise straight away and take the complaint seriously rather than becoming defensive. "
            "I'd explain that I'll make sure the vehicle is properly cleaned before my next booking, and "
            "thank them for letting me know, since feedback like that helps me keep my standards up."
        ),
        "tips": [
            "Apologise first, explain second — examiners listen for the order, not just the words.",
            "Ending on a positive note ('thank you for telling me') shows professionalism.",
        ],
    },
    {
        "topic": "Customer service scenarios",
        "prompt_text": "How would you handle a situation where two passengers in your car are arguing with each other?",
        "model_answer": (
            "I'd stay calm and focused on driving safely, since that's my main responsibility. If it "
            "started affecting safety — for example, if it became aggressive — I'd politely ask them to "
            "lower their voices or, if needed, pull over in a safe place. I wouldn't take sides in the "
            "argument itself."
        ),
        "tips": [
            "Separate your role (driving safely, staying neutral) from the passengers' behaviour — this structure reads clearly.",
            "Mentioning pulling over safely if things escalate shows good judgement under pressure.",
        ],
    },

    # --- Problem-solving / describing a situation ---
    {
        "topic": "Problem-solving & describing a situation",
        "prompt_text": "Describe what you would do if you realised, part-way through a journey, that a passenger had left a bag in your car from an earlier trip.",
        "model_answer": (
            "I'd keep the bag safe and try to contact the previous passenger through the booking app or "
            "operator as soon as it was safe to do so. If I couldn't reach them straight away, I'd hand "
            "the bag in to my operator so they could arrange its return, rather than leaving it in the car "
            "indefinitely or trying to deliver it myself without proper arrangement."
        ),
        "tips": [
            "This is a 'describe a process' question — sequence your answer clearly (first, then, if not, then).",
            "Show you understand the proper channel (the operator), not an improvised personal solution.",
        ],
    },
    {
        "topic": "Problem-solving & describing a situation",
        "prompt_text": "Explain what you would do if your vehicle broke down with a passenger on board.",
        "model_answer": (
            "First, I'd make sure we were somewhere safe — pulling over out of traffic if possible. I'd "
            "explain calmly to the passenger what had happened and reassure them I was dealing with it. "
            "Then I'd contact my operator to explain the situation and arrange another vehicle for the "
            "passenger, so they weren't left waiting without an update."
        ),
        "tips": [
            "Safety, then communication, then resolution — this three-part structure works for almost any 'what would you do' question.",
            "Don't forget the passenger's experience — reassurance and keeping them informed matters to the examiner.",
        ],
    },
    {
        "topic": "Problem-solving & describing a situation",
        "prompt_text": "Describe a time you had to adapt quickly to an unexpected change of plan.",
        "model_answer": (
            "I can think of a time when a road I was planning to use was suddenly closed. I had to think "
            "quickly and find an alternative route without much notice. I stayed calm, used my knowledge "
            "of the surrounding streets, and got to the destination only a few minutes later than planned. "
            "It taught me the value of always having a backup option in mind."
        ),
        "tips": [
            "Even for a hypothetical driving example, use past tense and a simple story structure: what happened, what you did, what the outcome was.",
            "A short closing reflection ('it taught me...') rounds the answer off naturally.",
        ],
    },
]
