"""
Question bank + admin bootstrap, shared by:
- seed_data.py (CLI, for local dev)
- app/admin.py's one-time /admin/seed route (for seeding a live database
  where there's no shell access, e.g. Railway)

run_seed() only adds questions whose (module_slug, prompt) isn't already in
the database, so this file can keep growing over time and re-running the
seed route is always safe — it never duplicates or overwrites anything.
Keep expanding the real question bank here, or via the admin UI.

All explanations are written from scratch, not copied from TfL's Handbook
or any other source — see the project's research doc for the regulatory
facts these are based on.
"""
from app.extensions import db
from app.models import Question, Choice, User, RouteMap, RouteScenario
from app.route_maps_data import ROUTE_MAPS

SEED_QUESTIONS = {
    "elr": [
        {
            "topic": "Reading comprehension",
            "prompt": "A passenger says: 'Could you drop me a bit further down, just past the lights?' What does the passenger want?",
            "choices": [
                ("To stop before the traffic lights", False),
                ("To stop a short distance after the traffic lights", True),
                ("To turn around at the lights", False),
                ("To wait at the lights", False),
            ],
            "explanation": "'Further down, just past the lights' means a short distance beyond the lights, in the direction of travel.",
        },
        {
            "topic": "Writing",
            "prompt": "Which sentence is grammatically correct?",
            "choices": [
                ("I have drove this route many times.", False),
                ("I have driven this route many times.", True),
                ("I has driven this route many times.", False),
                ("I driving this route many times.", False),
            ],
            "explanation": "'Driven' is the correct past participle of 'drive', used with 'have'.",
        },
        {
            "topic": "Reading comprehension",
            "prompt": "A passenger texts: 'Running 5 mins late, can you wait by the side entrance, not the main one?' What should the driver do?",
            "choices": [
                ("Leave immediately since the passenger is late", False),
                ("Wait near the side entrance, not the main entrance", True),
                ("Wait at the main entrance as originally planned", False),
                ("Cancel the booking", False),
            ],
            "explanation": "The passenger has specifically asked to be collected at the side entrance instead of the main one, and has asked for a short wait.",
        },
        {
            "topic": "Reading comprehension",
            "prompt": "A booking note reads: 'Please do not use the postcode — enter via the service road behind the supermarket.' What does this tell the driver?",
            "choices": [
                ("The postcode is wrong and should be reported", False),
                ("Sat-nav directions based on the postcode may not lead to the correct entrance; use the service road instead", True),
                ("The pickup has been cancelled", False),
                ("The passenger will meet the driver at the supermarket entrance", False),
            ],
            "explanation": "The note is warning that following the postcode alone could take the driver to the wrong place, and gives a specific alternative route in.",
        },
        {
            "topic": "Vocabulary",
            "prompt": "A passenger asks you to go 'via the back roads' to avoid traffic. 'Via' means:",
            "choices": [
                ("Instead of", False),
                ("By way of / through", True),
                ("Away from", False),
                ("At the same time as", False),
            ],
            "explanation": "'Via' means travelling by way of or through a particular route.",
        },
        {
            "topic": "Vocabulary",
            "prompt": "A passenger says their journey is 'time-critical'. This means:",
            "choices": [
                ("The exact time doesn't matter", False),
                ("Arriving on time is extremely important", True),
                ("The passenger wants to travel slowly", False),
                ("The booking has been cancelled", False),
            ],
            "explanation": "'Time-critical' describes something where meeting a deadline or arrival time matters a great deal.",
        },
        {
            "topic": "Writing",
            "prompt": "Which sentence correctly uses an apostrophe?",
            "choices": [
                ("The passengers' luggage is in the boot.", True),
                ("The passenger's luggage are in the boot.", False),
                ("The passengers luggage is in the boot.", False),
                ("The passenger's luggage's in the boot.", False),
            ],
            "explanation": "'Passengers'' (apostrophe after the s) correctly shows possession belonging to more than one passenger.",
        },
        {
            "topic": "Writing",
            "prompt": "Choose the correctly spelled word to complete the sentence: 'Please confirm your ___ before I set off.'",
            "choices": [
                ("adress", False),
                ("address", True),
                ("addres", False),
                ("adddress", False),
            ],
            "explanation": "'Address' has a double 'd' and a double 's'.",
        },
        {
            "topic": "Reading comprehension",
            "prompt": "A message from an operator reads: 'Job amended — new pickup time 14:30, previous booking cancelled.' What should the driver do?",
            "choices": [
                ("Arrive at the original time, since the job wasn't really cancelled", False),
                ("Ignore the message as it contradicts itself", False),
                ("Treat the earlier booking as void and plan to arrive at 14:30 instead", True),
                ("Contact the passenger to ask if the message is genuine", False),
            ],
            "explanation": "The message is clear: the earlier booking no longer applies, and the new pickup time of 14:30 is what the driver should work to.",
        },
        {
            "topic": "Listening and responding",
            "prompt": "A passenger asks, 'Would you mind popping the boot? I've got a case.' The most appropriate response is to:",
            "choices": [
                ("Say 'No' and drive off", False),
                ("Open the boot for the passenger's case", True),
                ("Ask the passenger to carry the case on their lap", False),
                ("Ignore the request", False),
            ],
            "explanation": "'Would you mind popping the boot?' is a polite way of asking the driver to open the boot, in this case for a suitcase.",
        },
        {
            "topic": "Vocabulary",
            "prompt": "A control room message says a job has been 'reassigned'. This means the job has been:",
            "choices": [
                ("Cancelled completely", False),
                ("Given to a different driver", True),
                ("Delayed by an hour", False),
                ("Upgraded to a larger vehicle", False),
            ],
            "explanation": "'Reassigned' means the booking has been passed to another driver rather than the original one.",
        },
        {
            "topic": "Writing",
            "prompt": "Which of these is the correct way to end a polite message to a passenger confirming you are on your way?",
            "choices": [
                ("on my way now c u soon", False),
                ("On my way now, see you shortly.", True),
                ("ON MY WAY NOW!!!", False),
                ("on way", False),
            ],
            "explanation": "Clear, properly punctuated, and professionally toned messages are expected — avoid text-speak, excessive capitals, and overly abbreviated messages.",
        },
        {
            "topic": "Reading comprehension",
            "prompt": "A sign at a pickup point reads: 'No stopping except for active loading.' A private hire driver waiting empty for a passenger should:",
            "choices": [
                ("Stop and wait, since picking up a passenger counts as loading", False),
                ("Not stop here while waiting, since this isn't active loading of goods or passengers in progress", True),
                ("Park here as long as the engine is running", False),
                ("Ignore the sign if no traffic warden is visible", False),
            ],
            "explanation": "'No stopping except for active loading' means stopping is only permitted while goods or passengers are actually being loaded or unloaded at that moment, not while waiting.",
        },
    ],
    "seru": [
        {
            "topic": "Safeguarding",
            "prompt": "A passenger appears to be a lone child under 16 travelling without an adult late at night. What should you do?",
            "choices": [
                ("Carry the journey as normal and say nothing", False),
                ("Refuse the booking outright with no explanation", False),
                ("Follow your operator's safeguarding procedure and raise any concerns appropriately", True),
                ("Ask the child for personal details to post online", False),
            ],
            "explanation": "Drivers are expected to be alert to safeguarding concerns and to follow their operator's procedure, in line with TfL's safeguarding awareness training.",
        },
        {
            "topic": "Equality",
            "prompt": "A passenger asks you to carry their guide dog. Under the Equality Act 2010, you must:",
            "choices": [
                ("Refuse if you have a personal allergy", False),
                ("Carry the passenger and their guide dog unless you hold a valid medical exemption certificate", True),
                ("Charge an extra fee for the dog", False),
                ("Ask the passenger to leave the dog behind", False),
            ],
            "explanation": "Private hire drivers must carry assistance dogs at no extra charge unless they hold a valid, displayed medical exemption certificate.",
        },
        {
            "topic": "Licensing requirements",
            "prompt": "As a London private hire driver, you may only accept bookings that:",
            "choices": [
                ("Are pre-booked through a licensed operator", True),
                ("You pick up by being hailed in the street", False),
                ("Come from any unlicensed app", False),
                ("Are agreed verbally with no booking record", False),
            ],
            "explanation": "Private hire vehicles cannot ply for hire — every journey must be pre-booked through a licensed operator.",
        },
        {
            "topic": "Safeguarding",
            "prompt": "During a journey, a passenger discloses that they feel unsafe at home. What is the most appropriate response?",
            "choices": [
                ("Change the subject and say nothing further", False),
                ("Listen without judgement, avoid promising confidentiality you can't guarantee, and report the concern through your operator's safeguarding process", True),
                ("Tell the passenger to call the police themselves and do nothing else", False),
                ("Post about it on social media to raise awareness", False),
            ],
            "explanation": "Drivers should listen supportively, not promise total confidentiality, and pass safeguarding concerns on through the proper channel rather than deciding not to act or handling it informally.",
        },
        {
            "topic": "Safeguarding",
            "prompt": "Which of these best describes a driver's safeguarding responsibility towards children and vulnerable adults?",
            "choices": [
                ("It only applies if the driver has had formal police training", False),
                ("Being alert to signs of harm or risk, and knowing how to raise a concern through the proper channel, even without being a safeguarding expert", True),
                ("It is solely the operator's responsibility and drivers need not be aware of it", False),
                ("It only applies to passengers travelling alone at night", False),
            ],
            "explanation": "All licensed drivers are expected to complete safeguarding awareness training and stay alert to possible signs of harm, exploitation, or risk, reporting concerns appropriately — this isn't limited to any one scenario.",
        },
        {
            "topic": "Safeguarding",
            "prompt": "A driver suspects a passenger may be a victim of exploitation (for example, signs of being controlled by someone else during the journey). The driver should:",
            "choices": [
                ("Confront the suspected exploiter directly", False),
                ("Do nothing unless the passenger asks for help directly", False),
                ("Note what was observed and report the concern via the operator's safeguarding procedure as soon as safely possible", True),
                ("Refuse to complete the journey and leave the passenger stranded", False),
            ],
            "explanation": "Drivers are not expected to intervene directly or confront anyone, but should note concerns and report them through the proper safeguarding channel.",
        },
        {
            "topic": "Equality",
            "prompt": "Under the Equality Act 2010, which of these is a form of unlawful discrimination a private hire driver could commit against a passenger?",
            "choices": [
                ("Charging a higher fare because the meter/pre-agreed price has gone up", False),
                ("Refusing to take a passenger because of their race, religion, disability or another protected characteristic", True),
                ("Declining a booking because the vehicle is already in use", False),
                ("Ending a shift at the scheduled time", False),
            ],
            "explanation": "The Equality Act 2010 makes it unlawful to refuse service, or provide a worse service, because of protected characteristics such as race, religion, disability, sex, or age.",
        },
        {
            "topic": "Equality",
            "prompt": "A wheelchair user books a journey. The driver's vehicle is not wheelchair-accessible. What should the driver do?",
            "choices": [
                ("Cancel without explanation and move on to the next job", False),
                ("Explain the situation and, where possible, support the booking being reassigned to an accessible vehicle through the operator", True),
                ("Ask the passenger to leave the wheelchair behind", False),
                ("Charge an additional fee for the inconvenience", False),
            ],
            "explanation": "Drivers should be honest about what their vehicle can accommodate and help the booking get reassigned appropriately, rather than simply refusing with no explanation or support.",
        },
        {
            "topic": "Equality",
            "prompt": "Why might a private hire driver hold a valid medical exemption certificate relating to assistance dogs?",
            "choices": [
                ("To avoid ever having to carry any passenger with a dog", False),
                ("Because a genuine medical condition (such as a severe allergy or asthma) makes carrying an assistance dog a risk to the driver's own health", True),
                ("To charge extra for carrying assistance dogs", False),
                ("Because the vehicle is too small for any dog", False),
            ],
            "explanation": "A medical exemption certificate is only granted for a genuine medical reason, and even then must be displayed; it is not a general opt-out from the duty to carry assistance dogs.",
        },
        {
            "topic": "Equality",
            "prompt": "A passenger with a hearing impairment communicates by writing notes on their phone. The most appropriate approach is to:",
            "choices": [
                ("Refuse the booking as communication will be too difficult", False),
                ("Speak more loudly instead of adapting", False),
                ("Be patient, read what they write, and communicate clearly, adapting as needed", True),
                ("Ignore their messages and drive without confirming details", False),
            ],
            "explanation": "Reasonable, patient adaptation to how a passenger communicates is part of providing an accessible, non-discriminatory service.",
        },
        {
            "topic": "Licensing requirements",
            "prompt": "A private hire driver's licence badge should be:",
            "choices": [
                ("Kept at home and shown only if asked by the passenger", False),
                ("Displayed in the vehicle as required by TfL so it is visible to the passenger", True),
                ("Optional once the driver has passed all three assessments", False),
                ("Only needed for the first year of licensing", False),
            ],
            "explanation": "Licensed private hire drivers must display their licence badge in the vehicle so passengers can confirm who is driving them.",
        },
        {
            "topic": "Licensing requirements",
            "prompt": "Why does TfL require private hire drivers to undergo an enhanced criminal record (DBS) check?",
            "choices": [
                ("It is only a formality with no real purpose", False),
                ("To help ensure passenger safety by checking a driver's suitability to work with the public, including vulnerable people", True),
                ("It is required only for drivers under 25", False),
                ("It replaces the need for a driving test", False),
            ],
            "explanation": "Enhanced DBS checks are a core part of TfL's passenger safety and safeguarding framework for licensing private hire drivers.",
        },
        {
            "topic": "Licensing requirements",
            "prompt": "A private hire vehicle's insurance must specifically cover:",
            "choices": [
                ("Social, domestic and pleasure use only", False),
                ("Hire and reward (carrying fare-paying passengers), not just private use", True),
                ("Only the vehicle, not any passengers", False),
                ("Nothing extra beyond standard third-party cover", False),
            ],
            "explanation": "Ordinary private car insurance doesn't cover carrying passengers for payment — a private hire vehicle needs hire-and-reward insurance.",
        },
        {
            "topic": "Professional conduct",
            "prompt": "A passenger disputes the fare at the end of a journey, insisting it should be lower. The driver should:",
            "choices": [
                ("Refuse to let the passenger out of the vehicle until they pay in full", False),
                ("Remain calm, explain how the fare was calculated, and involve the operator/control room if the dispute can't be resolved", True),
                ("Agree to accept whatever the passenger offers to avoid conflict", False),
                ("Raise their voice to assert authority", False),
            ],
            "explanation": "Fare disputes should be handled calmly and professionally, with the operator brought in to help resolve things if needed — not through confrontation or intimidation.",
        },
        {
            "topic": "Professional conduct",
            "prompt": "A passenger leaves a bag behind in the vehicle after their journey ends. The driver should:",
            "choices": [
                ("Keep it, since the passenger should have been more careful", False),
                ("Report it to the operator as lost property so it can be returned to the passenger", True),
                ("Leave it on the street where the passenger got out", False),
                ("Only return it if the passenger offers a reward", False),
            ],
            "explanation": "Lost property should be reported to the operator (or handed in appropriately) so it can be reunited with its owner, not kept or discarded.",
        },
        {
            "topic": "Professional conduct",
            "prompt": "Which of the following would be considered unprofessional conduct by a private hire driver?",
            "choices": [
                ("Confirming the destination with the passenger before setting off", False),
                ("Taking a longer route than necessary to increase the fare", True),
                ("Helping a passenger with heavy luggage where reasonably able to", False),
                ("Driving calmly and courteously", False),
            ],
            "explanation": "Deliberately taking a longer route to inflate the fare is dishonest and breaches the standards of professional conduct expected of licensed drivers.",
        },
        {
            "topic": "Road safety",
            "prompt": "Using a hand-held mobile phone to make a call while driving is:",
            "choices": [
                ("Allowed if stopped at traffic lights", False),
                ("Illegal in almost all circumstances while driving, including when stationary in traffic with the engine running", True),
                ("Allowed for private hire drivers taking job bookings", False),
                ("Only illegal on motorways", False),
            ],
            "explanation": "UK law prohibits hand-held mobile phone use while driving in almost all circumstances, including when temporarily stopped in traffic, with very limited exceptions (such as a genuine emergency call where it's unsafe to stop).",
        },
        {
            "topic": "Road safety",
            "prompt": "A driver should never operate a private hire vehicle:",
            "choices": [
                ("In light rain", False),
                ("While under the influence of alcohol or drugs", True),
                ("During rush hour", False),
                ("With the radio on", False),
            ],
            "explanation": "Driving under the influence of alcohol or drugs is both illegal and an extremely serious breach of passenger safety and licensing standards.",
        },
        {
            "topic": "Road safety",
            "prompt": "Seatbelts in a private hire vehicle:",
            "choices": [
                ("Only need to be worn by the driver", False),
                ("Should be worn by the driver and passengers, in line with seatbelt law and good safety practice, with passengers advised accordingly", True),
                ("Are optional on short journeys", False),
                ("Are not required in any licensed vehicle", False),
            ],
            "explanation": "Seatbelt use is a basic road safety requirement, and drivers should encourage passengers to wear them where fitted.",
        },
        {
            "topic": "Road safety",
            "prompt": "If a vehicle develops a fault (for example, a warning light appears) during a journey, the driver should:",
            "choices": [
                ("Ignore it unless the vehicle stops working completely", False),
                ("Assess whether it's safe to continue, and get the fault checked/repaired promptly rather than running an unsafe vehicle", True),
                ("Only report faults at the next annual inspection", False),
                ("Keep driving the vehicle until it breaks down completely", False),
            ],
            "explanation": "Licensed drivers are responsible for keeping their vehicle roadworthy, and a safety-related fault should be addressed promptly, not ignored.",
        },
        {
            "topic": "Safeguarding",
            "prompt": "Why does TfL require drivers to complete safeguarding awareness training before taking the SERU assessment?",
            "choices": [
                ("It is a historical formality with no bearing on the test content", False),
                ("Because safeguarding, including recognising signs of child exploitation and abuse, is a core part of what SERU assesses", True),
                ("It is only relevant to drivers who work school-run routes", False),
                ("It replaces the need for an enhanced DBS check", False),
            ],
            "explanation": "The safeguarding awareness training directly feeds into the SERU assessment, which tests understanding of safeguarding responsibilities among other regulatory topics.",
        },

        # --- Fill-in-the-blank / sentence completion ---
        # The real SERU paper includes sentence-completion items alongside
        # multiple-choice. These have no Choice rows — they're graded against
        # accepted_answers (case-insensitive, trimmed).
        {
            "topic": "Safeguarding",
            "question_type": "fill_blank",
            "prompt": "A driver who suspects a child passenger is at risk of harm should report their concern to the ____ as soon as possible.",
            "accepted_answers": ["relevant authorities", "authorities", "police", "safeguarding authorities"],
            "explanation": "Suspected harm to a child should be reported promptly to the relevant authorities (such as the police or a safeguarding body) — a driver should never investigate or confront the situation themselves.",
        },
        {
            "topic": "Equality",
            "question_type": "fill_blank",
            "prompt": "Under the Equality Act 2010, refusing to carry a passenger's guide dog is a form of ____ against a disabled person.",
            "accepted_answers": ["discrimination", "disability discrimination", "unlawful discrimination"],
            "explanation": "Refusing an assistance dog without a valid medical exemption is unlawful discrimination under the Equality Act 2010.",
        },
        {
            "topic": "Licensing",
            "question_type": "fill_blank",
            "prompt": "A private hire driver must hold a valid ____ licence issued by TfL before accepting any private hire bookings.",
            "accepted_answers": ["private hire driver", "pco", "private hire driver's"],
            "explanation": "Driving for private hire without a valid licence issued by TfL is illegal, regardless of insurance or vehicle condition.",
        },
        {
            "topic": "Licensing",
            "question_type": "fill_blank",
            "prompt": "Private hire vehicles can only legally be booked in advance through a licensed private hire ____.",
            "accepted_answers": ["operator", "private hire operator"],
            "explanation": "Unlike licensed taxis, private hire vehicles cannot be hailed in the street or hired directly — all bookings must go through a licensed operator.",
        },
        {
            "topic": "Professional conduct",
            "question_type": "fill_blank",
            "prompt": "A driver should never ____ a journey without good reason once a booking has been accepted, as this can leave a passenger stranded.",
            "accepted_answers": ["cancel", "abandon"],
            "explanation": "Cancelling an accepted booking without good reason is poor professional conduct and can leave a passenger, particularly a vulnerable one, stranded.",
        },
        {
            "topic": "Professional conduct",
            "question_type": "fill_blank",
            "prompt": "Drivers must treat all passengers with courtesy and ____, regardless of their background or appearance.",
            "accepted_answers": ["respect"],
            "explanation": "Professional conduct standards require drivers to treat every passenger with courtesy and respect, without exception.",
        },
        {
            "topic": "Road safety",
            "question_type": "fill_blank",
            "prompt": "Using a hand-held mobile phone while driving is illegal because it is a form of ____ driving.",
            "accepted_answers": ["distracted"],
            "explanation": "Hand-held phone use while driving is a specific, serious form of distracted driving and is prohibited by law.",
        },
        {
            "topic": "Road safety",
            "question_type": "fill_blank",
            "prompt": "A driver who feels too tired to drive safely should stop and ____ rather than continue the journey.",
            "accepted_answers": ["rest", "take a break"],
            "explanation": "Fatigue significantly increases accident risk — the only safe response to feeling too tired to drive is to stop and rest.",
        },
        {
            "topic": "Safeguarding",
            "question_type": "fill_blank",
            "prompt": "Drivers carrying unaccompanied children should be especially alert to signs of ____, as part of their safeguarding responsibility.",
            "accepted_answers": ["exploitation", "abuse", "harm", "child exploitation"],
            "explanation": "Unaccompanied children are a recognised higher-risk group, and drivers are expected to be alert to signs of exploitation or abuse as part of their safeguarding duty.",
        },
        {
            "topic": "Equality",
            "question_type": "fill_blank",
            "prompt": "A driver should make reasonable ____ for a passenger with a disability, such as allowing extra time to board.",
            "accepted_answers": ["adjustments", "accommodations"],
            "explanation": "Making reasonable adjustments for disabled passengers, such as allowing extra time, is both good practice and a legal expectation.",
        },
        {
            "topic": "Licensing",
            "question_type": "fill_blank",
            "prompt": "Failing to report a change of address to TfL within the required time can put a driver's ____ at risk.",
            "accepted_answers": ["licence", "license"],
            "explanation": "Licence conditions require drivers to keep TfL informed of changes such as address, and failing to do so can jeopardise the licence.",
        },
        {
            "topic": "Professional conduct",
            "question_type": "fill_blank",
            "prompt": "A driver should keep their vehicle clean and well presented, as this reflects on their ____ as a licensed driver.",
            "accepted_answers": ["professionalism", "professional standards", "reputation"],
            "explanation": "Vehicle presentation is part of the professional standard expected of a licensed private hire driver.",
        },
        {
            "topic": "Road safety",
            "question_type": "fill_blank",
            "prompt": "Drivers must ensure all passengers, including those in the rear seats, wear a seat ____ where required by law.",
            "accepted_answers": ["belt"],
            "explanation": "Seatbelt requirements apply to rear-seat passengers too, and the driver has a responsibility to ensure compliance where required.",
        },
        {
            "topic": "Safeguarding",
            "question_type": "fill_blank",
            "prompt": "If a passenger discloses that they are being harmed, a driver's first responsibility is to listen and take the disclosure ____, not to investigate it themselves.",
            "accepted_answers": ["seriously"],
            "explanation": "A driver is not trained to investigate safeguarding disclosures — their role is to listen, take it seriously, and pass it on to the appropriate authority.",
        },
        {
            "topic": "Equality",
            "question_type": "fill_blank",
            "prompt": "Charging a disabled passenger more than other passengers for the same journey because of their disability is a form of unlawful ____.",
            "accepted_answers": ["discrimination"],
            "explanation": "Charging a disabled passenger more for the same service because of their disability breaches the Equality Act 2010.",
        },
        {
            "topic": "Licensing",
            "question_type": "fill_blank",
            "prompt": "A private hire vehicle must display a valid TfL licence ____ as required by the licensing conditions.",
            "accepted_answers": ["plate", "disc", "licence plate"],
            "explanation": "Licensed private hire vehicles must display the correct TfL licence plate/disc as a licensing condition.",
        },
        {
            "topic": "Professional conduct",
            "question_type": "fill_blank",
            "prompt": "A driver who receives a complaint from a passenger should handle it ____ and professionally, rather than becoming defensive.",
            "accepted_answers": ["calmly", "professionally"],
            "explanation": "Professional conduct expectations include handling complaints calmly and constructively rather than reacting defensively.",
        },

        # --- Reading & understanding passages ---
        # The real SERU paper includes short passages followed by a question.
        # These use question_type "reading" and are graded like mcq (Choice
        # rows), but the template shows the shared passage text above them.
        {
            "topic": "Reading & understanding",
            "question_type": "reading",
            "passage": (
                "A private hire operator receives a booking from a regular customer who asks for "
                "the 'usual driver.' The operator explains that all bookings must be allocated "
                "through the licensed operator's booking system, and that a passenger cannot "
                "request or be guaranteed a specific driver, even a regular one. The operator "
                "allocates the job to whichever licensed driver is available and suitable for "
                "the journey."
            ),
            "prompt": "According to the passage, why can't the customer be guaranteed their 'usual driver'?",
            "choices": [
                ("Because the usual driver has retired", False),
                ("Because all bookings must go through the operator's system and be allocated to any available licensed driver, not a specific one", True),
                ("Because the usual driver is not properly licensed", False),
                ("Because the customer has not paid in advance", False),
            ],
            "explanation": "The passage states that bookings are allocated through the operator's system to whichever licensed driver is available and suitable — passengers can't request or be guaranteed a specific driver.",
        },
        {
            "topic": "Reading & understanding",
            "question_type": "reading",
            "passage": (
                "A driver notices that a passenger seems distressed during a journey and mentions "
                "that they do not feel safe at home. The driver does not ask probing questions or "
                "try to resolve the situation personally. Instead, once the journey is safely "
                "complete, the driver passes on what was said to their operator, who has a "
                "process for escalating safeguarding concerns raised by drivers."
            ),
            "prompt": "According to the passage, what did the driver do correctly after hearing the passenger's disclosure?",
            "choices": [
                ("Investigated the situation personally before continuing the journey", False),
                ("Ignored the comment since it wasn't the driver's business", False),
                ("Completed the journey safely and then passed the concern on to the operator's escalation process", True),
                ("Confronted the passenger about their home situation", False),
            ],
            "explanation": "The passage describes exactly the expected response: don't investigate or probe personally, complete the journey safely, and escalate the concern through the proper channel (here, the operator's process).",
        },
    ],
    "topographical": [
        {
            "topic": "Compass directions",
            "prompt": "If you are travelling north and need to turn to face east, which way do you turn?",
            "choices": [
                ("Left", False),
                ("Right", True),
                ("Continue straight", False),
                ("U-turn", False),
            ],
            "explanation": "Facing north, east is a 90-degree turn to the right.",
        },
        {
            "topic": "Map symbols",
            "prompt": "On a standard London street atlas, a one-way street is typically shown by:",
            "choices": [
                ("A dotted line", False),
                ("An arrow along the road showing the direction of travel", True),
                ("A red circle", False),
                ("A green triangle", False),
            ],
            "explanation": "One-way streets are marked with directional arrows showing the only legal direction of travel.",
        },
        {
            "topic": "Route planning",
            "prompt": "When planning the most direct legal route between two points, you should prioritise:",
            "choices": [
                ("The shortest distance regardless of road restrictions", False),
                ("The route that is both direct and complies with road signs and restrictions", True),
                ("Whichever route avoids all traffic lights", False),
                ("The route your satnav suggests, without checking it", False),
            ],
            "explanation": "The assessment tests your ability to plan a route that is both direct and legally compliant, not simply the shortest on a map.",
        },
        {
            "topic": "Compass directions",
            "prompt": "You are facing south. Which direction is directly behind you?",
            "choices": [
                ("East", False),
                ("West", False),
                ("North", True),
                ("South", False),
            ],
            "explanation": "North is the exact opposite (180 degrees) of south.",
        },
        {
            "topic": "Compass directions",
            "prompt": "Which compass direction lies exactly between north and east?",
            "choices": [
                ("North-west", False),
                ("South-east", False),
                ("North-east", True),
                ("South-west", False),
            ],
            "explanation": "North-east is the midpoint, at 45 degrees, between north and east.",
        },
        {
            "topic": "Compass directions",
            "prompt": "If you are heading west and turn 90 degrees to your right, which direction are you now facing?",
            "choices": [
                ("South", False),
                ("North", True),
                ("East", False),
                ("West", False),
            ],
            "explanation": "Facing west, a 90-degree turn to the right (clockwise) points you north.",
        },
        {
            "topic": "Map symbols",
            "prompt": "On a typical London street atlas, which of these is usually shown as a solid blue line or shaded area?",
            "choices": [
                ("A railway line", False),
                ("A river or other body of water", True),
                ("A one-way street", False),
                ("A pedestrian zone", False),
            ],
            "explanation": "Rivers, canals and other water features are conventionally shown in blue on street atlases and maps.",
        },
        {
            "topic": "Map symbols",
            "prompt": "A railway line on a standard street atlas is most commonly shown as:",
            "choices": [
                ("A thick red line", False),
                ("A line with regular cross-hatching or 'tick' marks along it", True),
                ("A dotted green line", False),
                ("A solid blue line", False),
            ],
            "explanation": "Railway lines are typically drawn with a distinctive cross-hatched or 'ladder' pattern to distinguish them from roads.",
        },
        {
            "topic": "Map symbols",
            "prompt": "On many street atlases, a small 'P' inside a circle or square usually indicates:",
            "choices": [
                ("A police station", False),
                ("A public car park", True),
                ("A pedestrian crossing", False),
                ("A post office", False),
            ],
            "explanation": "A circled or boxed 'P' is a widely used symbol for a public car park.",
        },
        {
            "topic": "Grid references",
            "prompt": "A street atlas index lists a location as being in grid square '42'. What does this tell you?",
            "choices": [
                ("The exact street number of the address", False),
                ("Which numbered square on the map page the location falls within, to help you find it quickly", True),
                ("The distance in miles from central London", False),
                ("The postcode area", False),
            ],
            "explanation": "Grid references point you to a specific numbered square on a map page, narrowing down where to look rather than giving an exact pinpoint.",
        },
        {
            "topic": "Grid references",
            "prompt": "When a map is divided into a numbered grid, grid squares are generally read:",
            "choices": [
                ("From bottom to top, then right to left", False),
                ("Across the top row first, then down to the next row, left to right within each row", True),
                ("Randomly, with no consistent order", False),
                ("Only in a spiral from the centre outward", False),
            ],
            "explanation": "Most UK street atlases number grid squares in reading order: left to right along each row, moving down row by row.",
        },
        {
            "topic": "Road rules and restrictions",
            "prompt": "A road sign shows a white arrow pointing straight ahead on a blue circular background, with no other markings. This means:",
            "choices": [
                ("Vehicles must turn left here", False),
                ("Vehicles must proceed straight ahead only — no turning", True),
                ("The road ahead is closed", False),
                ("This is a pedestrian-only zone", False),
            ],
            "explanation": "A blue circular sign with a white arrow is a mandatory direction sign — in this case, instructing traffic to continue straight ahead only.",
        },
        {
            "topic": "Road rules and restrictions",
            "prompt": "A road marked with a 'no entry' sign (a white horizontal bar on a red circle) means:",
            "choices": [
                ("No vehicles may enter the road from that direction", True),
                ("Only buses may enter", False),
                ("Entry is allowed outside rush hour", False),
                ("Parking is prohibited but driving through is fine", False),
            ],
            "explanation": "The red circle with a white bar is a 'no entry' sign — no vehicle may proceed into the road from that point.",
        },
        {
            "topic": "Road rules and restrictions",
            "prompt": "A bus lane is marked with a sign showing its hours of operation, e.g. '7am-7pm Mon-Fri'. Outside these hours, a private hire vehicle:",
            "choices": [
                ("May never use the bus lane, under any circumstances", False),
                ("May generally use that section of road like a normal lane, since the restriction only applies during the stated hours", True),
                ("Must always treat it as a bus lane regardless of the sign", False),
                ("Should ignore signs and check only for a bus physically present", False),
            ],
            "explanation": "Bus lane restrictions typically only apply during their signed operating hours — outside those hours, the lane is generally usable like an ordinary traffic lane unless other restrictions apply.",
        },
        {
            "topic": "Route planning",
            "prompt": "A planned route includes a road currently closed for roadworks, shown by a sign and barrier. The driver should:",
            "choices": [
                ("Drive through the barrier since the map shows the road as open", False),
                ("Plan an alternative legal route around the closure", True),
                ("Wait at the barrier until it is removed", False),
                ("Reverse the entire journey back to the start", False),
            ],
            "explanation": "Maps can't reflect every temporary closure — drivers need to read the road conditions in front of them and adapt their route accordingly.",
        },
        {
            "topic": "Route planning",
            "prompt": "Two possible routes exist between the same start and end point. Route A is shorter in distance but passes through several box junctions and a pedestrianised high street during restricted hours. Route B is slightly longer but has no such restrictions. The most appropriate choice is usually:",
            "choices": [
                ("Route A, because shortest distance always wins", False),
                ("Route B, because it is direct and complies with the restrictions in place, even though it's marginally longer", True),
                ("Whichever route has less traffic right now, regardless of restrictions", False),
                ("Route A, and simply ignore the pedestrianised section", False),
            ],
            "explanation": "A legally compliant, deliverable route takes priority over a route that is marginally shorter on paper but breaches restrictions.",
        },
        {
            "topic": "London geography",
            "prompt": "Which of these is a commonly used way to describe broad areas of London for orientation purposes?",
            "choices": [
                ("Compass-based zones such as North London, South London, East London, and West London, often divided further by the River Thames", True),
                ("Postcodes based solely on alphabetical order with no geographic meaning", False),
                ("Numbered districts identical to the London Underground zones", False),
                ("Random naming with no consistent system", False),
            ],
            "explanation": "London is commonly discussed in broad compass-based areas (north, south, east, west, and central), with the Thames often used as a key reference line, particularly for north/south orientation.",
        },
    ],
}


def run_seed():
    """Must be called with an app context already active (CLI pushes one
    itself via `with app.app_context()`; the admin route runs inside a
    normal Flask request, which already has one)."""
    summary = []
    for module_slug, questions in SEED_QUESTIONS.items():
        added = 0
        for item in questions:
            existing = Question.query.filter_by(
                module_slug=module_slug, prompt=item["prompt"]
            ).first()
            if existing:
                continue
            question = Question(
                module_slug=module_slug,
                topic=item["topic"],
                prompt=item["prompt"],
                explanation=item["explanation"],
                question_type=item.get("question_type", "mcq"),
                accepted_answers=item.get("accepted_answers"),
                passage=item.get("passage"),
            )
            db.session.add(question)
            for text, is_correct in item.get("choices", []):
                db.session.add(Choice(question=question, text=text, is_correct=is_correct))
            added += 1
        summary.append(f"{module_slug}: {added} new question(s) added")
    db.session.commit()

    maps_added, scenarios_added = 0, 0
    for map_item in ROUTE_MAPS:
        route_map = RouteMap.query.filter_by(slug=map_item["slug"]).first()
        if not route_map:
            route_map = RouteMap(slug=map_item["slug"], name=map_item["name"], data=map_item["data"])
            db.session.add(route_map)
            db.session.flush()  # need route_map.id for the scenarios below
            maps_added += 1
        for sc in map_item["scenarios"]:
            existing = RouteScenario.query.filter_by(
                map_id=route_map.id, start_node=sc["start"], end_node=sc["end"]
            ).first()
            if existing:
                continue
            db.session.add(
                RouteScenario(
                    map_id=route_map.id,
                    module_slug="topographical",
                    topic="Route planning",
                    start_node=sc["start"],
                    end_node=sc["end"],
                    prompt=sc["prompt"],
                )
            )
            scenarios_added += 1
    db.session.commit()
    summary.append(f"route maps: {maps_added} new map(s), {scenarios_added} new scenario(s) added")

    admin_email = "admin@example.com"
    admin_created = False
    if not User.query.filter_by(email=admin_email).first():
        admin = User(email=admin_email, full_name="Admin", is_admin=True)
        admin.set_password("change-this-password")
        db.session.add(admin)
        db.session.commit()
        admin_created = True

    return summary, admin_created
