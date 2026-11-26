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
from app.models import Question, Choice, User, RouteMap, RouteScenario, SpeakingPrompt
from app.route_maps_data import ROUTE_MAPS
from app.speaking_prompts_data import SPEAKING_PROMPTS

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

        # --- Additional multiple-choice (content-depth expansion; this content
        # is reading & writing practice in the style SERU uses to assess it —
        # see the ELR module page for why it's labelled that way) ---
        {
            "topic": "Reading comprehension",
            "prompt": "A booking note reads: 'Customer is hard of hearing — please text on arrival rather than calling.' What should the driver do?",
            "choices": [
                ("Call the customer as usual, since texting takes longer", False),
                ("Send a text message to let the customer know of arrival, instead of phoning", True),
                ("Knock on the customer's door loudly instead", False),
                ("Wait without contacting the customer at all", False),
            ],
            "explanation": "The note specifically asks for a text on arrival instead of a phone call, so the driver should follow that instruction rather than defaulting to their usual method.",
        },
        {
            "topic": "Reading comprehension",
            "prompt": "A passenger messages: 'Apologies, running about 10 mins behind — happy to pay for your wait if that's an issue.' What is the passenger offering?",
            "choices": [
                ("To cancel the booking", False),
                ("To pay extra to compensate the driver for the delay, if waiting is a problem", True),
                ("To meet the driver somewhere else instead", False),
                ("To reduce the fare", False),
            ],
            "explanation": "The passenger is proactively offering to compensate for the delay if the wait is inconvenient for the driver — a considerate, clearly worded message.",
        },
        {
            "topic": "Writing",
            "prompt": "Which of these messages to a passenger is clearest and most professional?",
            "choices": [
                ("running a bit l8, traffic bad, sry", False),
                ("Apologies — I'm running a few minutes late due to heavy traffic.", True),
                ("TRAFFIC IS BAD IM LATE", False),
                ("late, traffic", False),
            ],
            "explanation": "A clear, properly punctuated and professionally toned message is expected — avoiding text abbreviations and excessive capitalisation.",
        },
        {
            "topic": "Writing",
            "prompt": "Choose the sentence with correct subject-verb agreement.",
            "choices": [
                ("The passengers was waiting outside.", False),
                ("The passengers were waiting outside.", True),
                ("The passengers is waiting outside.", False),
                ("The passengers waits outside.", False),
            ],
            "explanation": "'Passengers' is plural, so it takes the plural verb form 'were', not the singular 'was' or 'is'.",
        },
        {
            "topic": "Vocabulary",
            "prompt": "In the context of private hire bookings, what does the term 'ETA' mean?",
            "choices": [
                ("Extra Travel Allowance", False),
                ("Estimated Time of Arrival", True),
                ("Exact Travel Address", False),
                ("Emergency Transport Authorisation", False),
            ],
            "explanation": "'ETA' is a widely used abbreviation for 'Estimated Time of Arrival', commonly used in booking and dispatch communication.",
        },
        {
            "topic": "Vocabulary",
            "prompt": "A dispatch message says a booking has been 'allocated.' What does this mean?",
            "choices": [
                ("The booking has been cancelled", False),
                ("The booking has been assigned to a specific driver", True),
                ("The booking has been refunded", False),
                ("The booking is still pending and unassigned", False),
            ],
            "explanation": "'Allocated' means the booking has been assigned — in this context, to a specific driver — rather than left pending or cancelled.",
        },
        {
            "topic": "Reading comprehension",
            "prompt": "An operator's message reads: 'Please note — this booking includes a child seat request. Confirm availability before accepting.' What must the driver do first?",
            "choices": [
                ("Accept the booking, then look for a child seat afterwards", False),
                ("Confirm they have a suitable child seat available before accepting the booking", True),
                ("Decline the booking automatically", False),
                ("Ask the passenger to bring their own seat", False),
            ],
            "explanation": "The message explicitly asks the driver to confirm availability before accepting — accepting first and checking afterwards would go against the instruction.",
        },
        {
            "topic": "Writing",
            "prompt": "Which version of this message uses the correct word?",
            "choices": [
                ("Their waiting for you outside the station.", False),
                ("They're waiting for you outside the station.", True),
                ("There waiting for you outside the station.", False),
                ("Theyre waiting for you outside the station.", False),
            ],
            "explanation": "'They're' is the correct contraction of 'they are' in this context; 'their' shows possession and 'there' indicates place.",
        },
        {
            "topic": "Listening and responding",
            "prompt": "A passenger says over the phone: 'Actually, scrap that — can you come to the back entrance instead?' What should the driver understand?",
            "choices": [
                ("The booking has been cancelled", False),
                ("The passenger is changing the pickup point to the back entrance, replacing the earlier instruction", True),
                ("The passenger wants to be dropped at the back entrance instead of picked up", False),
                ("The driver should ignore the new instruction and use the original pickup point", False),
            ],
            "explanation": "'Scrap that' signals the passenger is replacing their earlier instruction with a new one — the driver should go to the back entrance as now requested.",
        },
        {
            "topic": "Reading comprehension",
            "prompt": "A note says: 'Flight delayed — new landing time 22:40, please adjust pickup accordingly.' What should the driver do?",
            "choices": [
                ("Arrive at the original pickup time regardless", False),
                ("Update their arrival to align with the new 22:40 landing time", True),
                ("Cancel the booking since the flight was delayed", False),
                ("Contact the airline directly for confirmation", False),
            ],
            "explanation": "The note explicitly asks the driver to adjust the pickup time to match the new landing time, rather than keeping the original schedule.",
        },

        # --- Additional reading/writing/vocabulary/listening (content-depth expansion) ---
        {
            "topic": "Listening and responding",
            "prompt": "A passenger on the phone says: 'I'm not fussed which way you go, whatever's quickest for you.' What does this mean?",
            "choices": [
                ("The passenger wants the scenic route", False),
                ("The passenger is leaving the route choice up to the driver, as long as it's quick", True),
                ("The passenger wants to be consulted on every turn", False),
                ("The passenger doesn't want to be picked up at all", False),
            ],
            "explanation": "'Not fussed' means the passenger has no strong preference, and they're explicitly handing the route decision to the driver, prioritising speed.",
        },
        {
            "topic": "Listening and responding",
            "prompt": "A passenger says: 'Sorry, could you say that again? I didn't quite catch the address.' What should the driver do?",
            "choices": [
                ("Continue the conversation without repeating anything", False),
                ("Repeat the address clearly, perhaps more slowly", True),
                ("Assume the passenger heard correctly and move on", False),
                ("End the call", False),
            ],
            "explanation": "The passenger has directly asked for the information to be repeated — the appropriate response is to repeat it clearly.",
        },
        {
            "topic": "Listening and responding",
            "prompt": "On a call, a passenger says: 'Hang on a sec, let me just check with my partner.' What should the driver understand?",
            "choices": [
                ("The passenger is ending the call for good", False),
                ("The passenger needs a brief pause before continuing the conversation", True),
                ("The passenger wants the driver to call back later", False),
                ("The booking has been cancelled", False),
            ],
            "explanation": "'Hang on a sec' is a common way of asking for a short pause, not ending the conversation — the driver should simply wait briefly.",
        },
        {
            "topic": "Vocabulary",
            "prompt": "If a passenger describes a street as 'congested', they mean it is:",
            "choices": [
                ("Closed completely", False),
                ("Very busy with traffic", True),
                ("Under construction", False),
                ("One-way only", False),
            ],
            "explanation": "'Congested' describes heavy traffic, not closure, construction or one-way status specifically.",
        },
        {
            "topic": "Vocabulary",
            "prompt": "A passenger asks the driver to 'hang back' from the car in front. What do they mean?",
            "choices": [
                ("Drive closer to the car in front", False),
                ("Keep a greater distance from the car in front", True),
                ("Overtake the car in front", False),
                ("Stop immediately", False),
            ],
            "explanation": "To 'hang back' means to keep more distance or hold a position further behind, not to close the gap.",
        },
        {
            "topic": "Vocabulary",
            "prompt": "What does it mean if a passenger says their flight has been 'rerouted'?",
            "choices": [
                ("The flight has been cancelled entirely", False),
                ("The flight's path or destination airport has been changed", True),
                ("The flight has landed early", False),
                ("The flight number has changed but nothing else", False),
            ],
            "explanation": "'Rerouted' means the flight's path, and sometimes its arrival airport, has changed — distinct from cancellation or simply landing early.",
        },
        {
            "topic": "Writing",
            "prompt": "Which sentence uses the correct singular possessive form?",
            "choices": [
                ("The driver's badge was clearly displayed.", True),
                ("The drivers badge was clearly displayed.", False),
                ("The driver's badge' was clearly displayed.", False),
                ("The drivers' badge were clearly displayed.", False),
            ],
            "explanation": "\"The driver's badge\" correctly shows singular possession, with correct subject-verb agreement ('was').",
        },
        {
            "topic": "Writing",
            "prompt": "Which sentence is written in the correct tense to describe something that happened yesterday?",
            "choices": [
                ("I pick up the passenger at the station yesterday.", False),
                ("I picked up the passenger at the station yesterday.", True),
                ("I am picking up the passenger at the station yesterday.", False),
                ("I will pick up the passenger at the station yesterday.", False),
            ],
            "explanation": "Past simple ('picked up') is correct for a completed action in the past, signalled by 'yesterday'.",
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
        {
            "topic": "Safeguarding",
            "question_type": "fill_blank",
            "prompt": "A driver should never attempt to personally ____ a safeguarding concern — their role is to report it, not resolve it themselves.",
            "accepted_answers": ["investigate", "resolve", "handle"],
            "explanation": "Drivers are not trained safeguarding investigators — their responsibility is to report concerns through the proper channel, not to investigate or resolve them personally.",
        },
        {
            "topic": "Safeguarding",
            "question_type": "fill_blank",
            "prompt": "Vulnerable adults, as well as children, can be at risk of ____ and should be given the same safeguarding attention by drivers.",
            "accepted_answers": ["harm", "exploitation", "abuse"],
            "explanation": "Safeguarding responsibility extends to vulnerable adults, not only children, and drivers should apply the same level of awareness to both groups.",
        },
        {
            "topic": "Equality",
            "question_type": "fill_blank",
            "prompt": "A driver who assumes a passenger's needs based on their appearance, rather than asking them directly, risks making a discriminatory ____.",
            "accepted_answers": ["assumption"],
            "explanation": "Assuming needs based on appearance, rather than asking, can lead to discriminatory treatment — professional conduct means asking the passenger directly.",
        },
        {
            "topic": "Equality",
            "question_type": "fill_blank",
            "prompt": "The Equality Act 2010 protects people from discrimination based on characteristics such as age, disability, race, religion and ____.",
            "accepted_answers": ["sex", "gender", "sexual orientation"],
            "explanation": "The Equality Act 2010 lists a defined set of protected characteristics, including age, disability, race, religion, sex and sexual orientation among others.",
        },
        {
            "topic": "Licensing",
            "question_type": "fill_blank",
            "prompt": "A private hire vehicle must be regularly ____ to ensure it remains roadworthy and compliant with licensing standards.",
            "accepted_answers": ["inspected", "serviced", "maintained"],
            "explanation": "Regular inspection/maintenance is a licensing requirement to ensure the vehicle remains roadworthy and compliant.",
        },
        {
            "topic": "Licensing",
            "question_type": "fill_blank",
            "prompt": "Operating as a private hire driver without the correct ____ from TfL is a criminal offence.",
            "accepted_answers": ["licence", "license", "licensing"],
            "explanation": "Driving for private hire without the correct TfL licence is a criminal offence, regardless of experience or vehicle condition.",
        },
        {
            "topic": "Licensing",
            "question_type": "fill_blank",
            "prompt": "A driver must inform TfL of certain changes in circumstances, such as a new criminal conviction, within the required ____.",
            "accepted_answers": ["timeframe", "time limit", "deadline"],
            "explanation": "Licence conditions require drivers to notify TfL of relevant changes, such as new convictions, within a set timeframe.",
        },
        {
            "topic": "Professional conduct",
            "question_type": "fill_blank",
            "prompt": "Arriving on time for a booking, wherever reasonably possible, is part of being a ____ private hire driver.",
            "accepted_answers": ["reliable", "professional", "punctual"],
            "explanation": "Punctuality and reliability are core expectations of professional conduct for a private hire driver.",
        },
        {
            "topic": "Professional conduct",
            "question_type": "fill_blank",
            "prompt": "A driver should avoid engaging in ____ conversation about politics or religion with passengers who have not invited it, to keep the journey comfortable for everyone.",
            "accepted_answers": ["unsolicited", "unwanted", "uninvited"],
            "explanation": "Professional conduct includes being sensitive to topics passengers may not want to discuss, such as unsolicited political or religious conversation.",
        },
        {
            "topic": "Road safety",
            "question_type": "fill_blank",
            "prompt": "Drivers should maintain a safe following ____ from the vehicle in front, allowing enough time to react and stop safely.",
            "accepted_answers": ["distance"],
            "explanation": "A safe following distance gives a driver enough time to react and stop safely if the vehicle ahead brakes suddenly.",
        },
        {
            "topic": "Road safety",
            "question_type": "fill_blank",
            "prompt": "Driving after consuming alcohol or drugs significantly impairs a driver's ____ and reaction times, and is illegal.",
            "accepted_answers": ["judgement", "judgment", "concentration", "reaction time"],
            "explanation": "Alcohol and drugs impair judgement and reaction time, which is why driving under their influence is both dangerous and illegal.",
        },
        {
            "topic": "Road safety",
            "question_type": "fill_blank",
            "prompt": "Before starting a journey, a driver should carry out basic vehicle ____, such as checking lights, tyres and mirrors.",
            "accepted_answers": ["checks", "inspections"],
            "explanation": "Basic pre-journey vehicle checks (lights, tyres, mirrors) are part of a driver's responsibility to keep the vehicle safe to drive.",
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
        {
            "topic": "Reading & understanding",
            "question_type": "reading",
            "passage": (
                "A private hire operator reminds its drivers that passengers using wheelchairs or "
                "other mobility aids must never be refused a booking because of the aid itself, "
                "unless the driver holds a valid medical exemption certificate. The operator explains "
                "that even where loading a wheelchair takes a little longer, this is a normal part of "
                "the job, and refusing such a booking without a valid exemption would breach the "
                "driver's legal obligations."
            ),
            "prompt": "According to the passage, when can a driver refuse a booking from a wheelchair user?",
            "choices": [
                ("Whenever loading the wheelchair would take extra time", False),
                ("Never — there is no circumstance in which this is allowed", False),
                ("Only if the driver holds a valid medical exemption certificate", True),
                ("Only during busy periods", False),
            ],
            "explanation": "The passage states the refusal is only acceptable with a valid medical exemption certificate — extra time or inconvenience is not a valid reason.",
        },
        {
            "topic": "Reading & understanding",
            "question_type": "reading",
            "passage": (
                "After a vehicle breakdown left a passenger waiting at the roadside, a driver's operator "
                "reviewed what happened. The driver had pulled over safely, explained the situation "
                "calmly to the passenger, and contacted the operator straight away to arrange a "
                "replacement vehicle. The operator noted that the driver followed the correct procedure "
                "and kept the passenger informed throughout, which minimised the disruption to their "
                "journey."
            ),
            "prompt": "According to the passage, what made the driver's handling of the breakdown correct?",
            "choices": [
                ("The driver tried to repair the vehicle themselves before calling for help", False),
                ("The driver pulled over safely, communicated calmly with the passenger, and promptly arranged a replacement through the operator", True),
                ("The driver asked the passenger to find their own way to the destination", False),
                ("The driver waited for the passenger to contact the operator", False),
            ],
            "explanation": "The passage highlights safety first, clear communication with the passenger, and prompt use of the proper channel (the operator) to arrange a replacement — exactly what good practice during a breakdown looks like.",
        },
        {
            "topic": "Reading & understanding",
            "question_type": "reading",
            "passage": (
                "A new private hire driver asks a more experienced colleague whether it's acceptable "
                "to accept a direct approach from someone in the street who wants a lift, since no "
                "other cars are available nearby. The experienced driver explains that this isn't "
                "allowed — private hire vehicles can only accept pre-booked journeys arranged through "
                "a licensed operator, regardless of how convenient a direct approach might seem."
            ),
            "prompt": "According to the passage, why can't the new driver accept the street approach?",
            "choices": [
                ("Because the street was too busy", False),
                ("Because private hire vehicles can only accept bookings made in advance through a licensed operator, not direct approaches", True),
                ("Because the passenger hadn't paid in advance", False),
                ("Because only licensed taxis are allowed to operate in that area", False),
            ],
            "explanation": "The passage states plainly that private hire vehicles can only accept pre-booked journeys through a licensed operator — a direct street approach isn't permitted, however convenient.",
        },
        {
            "topic": "Reading & understanding",
            "question_type": "reading",
            "passage": (
                "A driver completed a safeguarding awareness course before sitting their SERU "
                "assessment. During the course, they learned that if a child passenger says something "
                "that raises concern, the right response is to stay calm, avoid asking leading or "
                "probing questions, and pass on exactly what was said to the operator as soon as it "
                "is safe to do so, rather than interpreting or adding to it."
            ),
            "prompt": "According to the passage, what should a driver avoid doing if a child says something concerning?",
            "choices": [
                ("Avoid asking leading or probing questions, or interpreting what the child said", True),
                ("Avoid reporting it until the end of the day", False),
                ("Avoid driving the rest of the journey", False),
                ("Avoid telling the operator at all", False),
            ],
            "explanation": "The passage specifically warns against leading or probing questions and against interpreting or adding to what the child said — the driver should pass on exactly what was said, unembellished.",
        },

        # --- Additional multiple-choice (content-depth expansion) ---
        {
            "topic": "Safeguarding",
            "prompt": "A driver regularly transports an unaccompanied 10-year-old to school on a pre-arranged booking. What is the most appropriate approach?",
            "choices": [
                ("Chat to the child about their home life to build rapport", False),
                ("Treat the journey professionally, keep the child safe and supervised, and raise any concerns through the operator rather than informally", True),
                ("Ask the child for their parents' phone number to contact them directly if ever needed", False),
                ("Allow the child to decide the route since they travel it often", False),
            ],
            "explanation": "Journeys involving unaccompanied children call for professional conduct and safeguarding awareness — concerns are raised through the proper channel (the operator), not handled informally or personally.",
        },
        {
            "topic": "Safeguarding",
            "prompt": "Which of these is a recognised sign that might indicate a child passenger is at risk and should prompt a safeguarding concern?",
            "choices": [
                ("The child is wearing a school uniform", False),
                ("The child appears frightened of the adult accompanying them, or shows unexplained injuries", True),
                ("The child is travelling with a sibling", False),
                ("The child falls asleep during the journey", False),
            ],
            "explanation": "Fear of an accompanying adult or unexplained injuries are recognised indicators that should prompt a driver to raise a safeguarding concern through the proper channel.",
        },
        {
            "topic": "Safeguarding",
            "prompt": "A driver overhears a passenger on the phone describing a plan that could put someone else in danger. What should the driver do?",
            "choices": [
                ("Ignore it — phone calls are private and not the driver's concern", False),
                ("Interrupt the call immediately and confront the passenger", False),
                ("Note what was heard and report the concern to the police or the operator once it is safe to do so", True),
                ("Post about it on social media to warn others", False),
            ],
            "explanation": "A driver who becomes aware of a genuine risk to someone's safety should report it through the proper channel (police or operator) rather than ignoring it, confronting the passenger, or handling it informally.",
        },
        {
            "topic": "Equality",
            "prompt": "A driver refuses a booking because the passenger uses a wheelchair and the driver 'doesn't want the hassle' of loading it. Is this acceptable?",
            "choices": [
                ("Yes, as long as the driver explains the reason politely", False),
                ("No — this is unlawful discrimination against a disabled passenger unless a specific, valid medical exemption applies", True),
                ("Yes, if the driver offers to call another car instead", False),
                ("No, but only if the wheelchair is motorised", False),
            ],
            "explanation": "Refusing a booking because of the inconvenience of assisting a disabled passenger is unlawful discrimination under the Equality Act 2010, absent a valid medical exemption.",
        },
        {
            "topic": "Equality",
            "prompt": "What is a 'protected characteristic' under the Equality Act 2010?",
            "choices": [
                ("A type of vehicle modification", False),
                ("A personal characteristic — such as disability, age, race, religion or sex — that is legally protected from discrimination", True),
                ("A licensing category for private hire vehicles", False),
                ("A safety feature required in all private hire vehicles", False),
            ],
            "explanation": "Protected characteristics (including disability, age, race, religion, sex and others) are the specific grounds on which the Equality Act 2010 makes discrimination unlawful.",
        },
        {
            "topic": "Equality",
            "prompt": "A passenger asks a driver to skip a stop to pick up their visually impaired friend's guide dog, saying it will 'make a mess.' What should the driver do?",
            "choices": [
                ("Agree, since it's the passenger's choice", False),
                ("Carry the guide dog as normal — refusing it would be unlawful discrimination, regardless of another passenger's preference", True),
                ("Only allow the dog in the boot", False),
                ("Charge the visually impaired passenger extra to compensate", False),
            ],
            "explanation": "A driver must carry an assistance dog; another passenger's personal preference doesn't change the legal duty, and charging more or relegating the dog to the boot would also be inappropriate.",
        },
        {
            "topic": "Licensing",
            "prompt": "What should a driver do if their private hire driver's licence is due to expire soon?",
            "choices": [
                ("Keep driving as normal until TfL contacts them", False),
                ("Apply to renew it in good time before the expiry date, to avoid a gap in being legally licensed", True),
                ("Switch to driving a licensed taxi instead, since no licence is needed for that", False),
                ("Nothing — licences renew automatically", False),
            ],
            "explanation": "Licences do not renew automatically; a driver is responsible for applying to renew in good time to avoid driving without a valid licence.",
        },
        {
            "topic": "Licensing",
            "prompt": "Why is it important for a private hire operator to keep accurate records of bookings?",
            "choices": [
                ("It is only useful for the operator's own accounting", False),
                ("It is a licensing requirement that supports accountability, safety and the ability to trace a journey if needed", True),
                ("It has no real purpose beyond tradition", False),
                ("It is only required for journeys over a certain distance", False),
            ],
            "explanation": "Accurate booking records are a licensing requirement that supports accountability and safety, including the ability to trace who travelled in which vehicle and when.",
        },
        {
            "topic": "Professional conduct",
            "prompt": "A driver is asked by a passenger to make an unscheduled detour to run a personal errand unrelated to the booking. What's the appropriate response?",
            "choices": [
                ("Agree without question to keep the passenger happy", False),
                ("Politely explain that the journey needs to stay within what was booked, and suggest arranging it properly through the operator if a change is genuinely needed", True),
                ("Refuse and end the journey immediately", False),
                ("Charge whatever extra fee feels fair, without informing the operator", False),
            ],
            "explanation": "Private hire bookings go through the operator, so unscheduled changes should be handled through the proper channel rather than informally agreed or improvised on the fly.",
        },
        {
            "topic": "Professional conduct",
            "prompt": "Which of these best reflects professional conduct towards a passenger with a visible disability?",
            "choices": [
                ("Speaking loudly and slowly to all disabled passengers by default", False),
                ("Asking the passenger directly, respectfully, what assistance (if any) they would like, rather than assuming", True),
                ("Avoiding conversation with the passenger altogether", False),
                ("Deciding on their behalf what help they need", False),
            ],
            "explanation": "Respectful, professional conduct means asking rather than assuming — treating the passenger as the best judge of what assistance, if any, they need.",
        },
        {
            "topic": "Road safety",
            "prompt": "Why are driver 'hours of work' limits relevant to road safety for private hire drivers?",
            "choices": [
                ("They aren't relevant — private hire drivers can work unlimited hours safely", False),
                ("Excessive hours without rest increase fatigue, which significantly raises the risk of a collision", True),
                ("They only matter for drivers of large goods vehicles", False),
                ("They are a tax matter, not a safety matter", False),
            ],
            "explanation": "Fatigue from excessive working hours without adequate rest is a well-established, significant road safety risk, which is why managing working hours matters for drivers.",
        },
        {
            "topic": "Road safety",
            "prompt": "A driver notices their tyre tread is close to the legal minimum. What should they do before their next booking?",
            "choices": [
                ("Continue driving and check again at the next scheduled service", False),
                ("Get the tyre checked and replaced if needed before continuing to drive passengers", True),
                ("Only worry about it if it starts raining", False),
                ("Reduce the vehicle's advertised capacity instead", False),
            ],
            "explanation": "A driver is responsible for keeping their vehicle roadworthy; a tyre near the legal minimum tread should be addressed before continuing to carry passengers, not left until the next scheduled service.",
        },

        # --- Further multiple-choice (second content-depth expansion) ---
        {
            "topic": "Safeguarding",
            "prompt": "A passenger who is clearly intoxicated is being carefully looked after by two sober friends throughout the journey. Is this necessarily a safeguarding concern?",
            "choices": [
                ("Yes, intoxication alone always requires a safeguarding report", False),
                ("Not necessarily — being cared for by others reduces risk, though the driver should stay alert to any change", True),
                ("No, intoxicated passengers are never a safeguarding concern", False),
                ("Yes, but only if the passenger is under 25", False),
            ],
            "explanation": "Context matters: a passenger being appropriately cared for by sober companions is lower risk than one alone, though drivers should still stay alert to any signs things are not as they appear.",
        },
        {
            "topic": "Safeguarding",
            "prompt": "A driver drops off a child passenger at night but no adult is visibly waiting at the address. What is the most appropriate action?",
            "choices": [
                ("Drop the child off immediately and drive away", False),
                ("Wait a reasonable time to see an adult arrive, and contact the operator if no one appears, rather than leaving the child unsupervised", True),
                ("Take the child to the nearest police station directly", False),
                ("Leave the child with a neighbour chosen by the driver", False),
            ],
            "explanation": "Leaving an unaccompanied child with no visible adult present is a safeguarding risk; the driver should wait a reasonable time and escalate through the operator rather than simply driving off.",
        },
        {
            "topic": "Safeguarding",
            "prompt": "What is the main purpose of safeguarding awareness training for private hire drivers?",
            "choices": [
                ("To train drivers to personally investigate suspected abuse", False),
                ("To help drivers recognise possible signs of harm or risk and know the correct way to raise a concern", True),
                ("To qualify drivers as safeguarding officers", False),
                ("To replace the need for a DBS check", False),
            ],
            "explanation": "Safeguarding awareness training builds recognition and reporting skills — it does not turn drivers into investigators or officers, and it doesn't replace other checks like DBS.",
        },
        {
            "topic": "Safeguarding",
            "prompt": "A passenger discloses a safety concern and asks the driver to keep it 'just between us.' What should the driver do?",
            "choices": [
                ("Promise full confidentiality to maintain the passenger's trust", False),
                ("Avoid promising confidentiality, and still report the concern through the proper channel because safety comes first", True),
                ("Ignore the disclosure since it was shared in confidence", False),
                ("Tell other passengers about it later for context", False),
            ],
            "explanation": "Drivers should never promise total confidentiality on a safety disclosure — passenger (or third-party) safety takes priority over a request for secrecy.",
        },
        {
            "topic": "Safeguarding",
            "prompt": "Which best describes 'county lines' exploitation, as a safeguarding risk drivers should be aware of?",
            "choices": [
                ("A type of vehicle insurance fraud", False),
                ("Criminal groups using children or vulnerable people, sometimes moved between areas, to transport drugs or money", True),
                ("A licensing rule about operating across borough boundaries", False),
                ("A traffic enforcement scheme", False),
            ],
            "explanation": "County lines exploitation involves criminal networks using children or vulnerable people — sometimes transported between areas — to move drugs or money, which is why unusual passenger patterns can be a safeguarding signal.",
        },
        {
            "topic": "Equality",
            "prompt": "A passenger using crutches asks for a little extra time to get into the vehicle. What should the driver do?",
            "choices": [
                ("Rush them politely to keep to schedule", False),
                ("Allow the reasonable extra time needed without complaint", True),
                ("Suggest they book a different driver next time", False),
                ("Charge a small waiting fee for the extra time", False),
            ],
            "explanation": "Allowing reasonable extra time for a passenger with a mobility impairment is a basic reasonable adjustment, not something to charge for or discourage.",
        },
        {
            "topic": "Equality",
            "prompt": "A driver assumes an elderly passenger needs help with their bags without asking first. What would be a better approach?",
            "choices": [
                ("Continue assuming, since it's usually correct", False),
                ("Ask the passenger directly what help, if any, they would like", True),
                ("Avoid offering any help at all", False),
                ("Only help if the passenger looks very frail", False),
            ],
            "explanation": "Asking rather than assuming respects the passenger's own judgement of what help they want, and avoids patronising or inaccurate assumptions based on age or appearance.",
        },
        {
            "topic": "Equality",
            "prompt": "Is it lawful for a driver to charge a blind passenger extra because they need help finding their destination?",
            "choices": [
                ("Yes, since it takes the driver more time", False),
                ("No — charging a disabled passenger more for the same service is unlawful discrimination", True),
                ("Yes, but only a small surcharge", False),
                ("It depends on how long the journey takes", False),
            ],
            "explanation": "Charging a disabled passenger more for the same service because of their disability breaches the Equality Act 2010, regardless of the amount.",
        },
        {
            "topic": "Equality",
            "prompt": "A passenger who communicates in British Sign Language brings a friend along to interpret. What should the driver do?",
            "choices": [
                ("Refuse the booking since direct communication isn't possible", False),
                ("Communicate politely via the interpreter and treat the passenger with the same respect as any other passenger", True),
                ("Speak only to the friend and ignore the passenger", False),
                ("Ask the passenger to cancel and rebook without the interpreter", False),
            ],
            "explanation": "Communicating through an interpreter the passenger has brought is a reasonable and respectful way to provide an accessible service, not grounds for refusal.",
        },
        {
            "topic": "Equality",
            "prompt": "A driver is unsure whether their vehicle can safely accommodate a passenger's mobility scooter. What is the best approach?",
            "choices": [
                ("Refuse the booking immediately to avoid any risk", False),
                ("Check the scooter's size and how it can be safely secured before accepting, rather than guessing or refusing outright", True),
                ("Accept without checking and deal with any problem on arrival", False),
                ("Ask the passenger to leave the scooter behind", False),
            ],
            "explanation": "Checking practical details like size and secure stowage lets a driver make an informed decision, rather than refusing outright or accepting blind and risking an unsafe journey.",
        },
        {
            "topic": "Road safety",
            "prompt": "Why should a driver avoid lengthy hands-free phone conversations while driving, even though it's legal?",
            "choices": [
                ("It isn't actually a safety concern if hands stay on the wheel", False),
                ("It still causes cognitive distraction that can reduce reaction times, even without physically holding the phone", True),
                ("It drains the vehicle's battery too quickly", False),
                ("It is only a concern on motorways", False),
            ],
            "explanation": "Even hands-free conversations draw mental attention away from driving, which is why limiting lengthy calls while driving is good practice beyond the legal minimum.",
        },
        {
            "topic": "Road safety",
            "prompt": "A dashboard warning light comes on during a journey with a passenger on board. What should the driver do?",
            "choices": [
                ("Ignore it until the next scheduled service", False),
                ("Note it and get the vehicle checked as soon as it is safely possible", True),
                ("Turn off the dashboard display so it isn't distracting", False),
                ("Pull over immediately in the middle of the road", False),
            ],
            "explanation": "A warning light shouldn't be ignored, but the correct response is to note it and arrange a check as soon as safely possible — not to stop dangerously or wait for a routine service.",
        },
        {
            "topic": "Road safety",
            "prompt": "Why is it important to increase following distance in wet or icy conditions?",
            "choices": [
                ("It isn't necessary if the driver has good tyres", False),
                ("Stopping distances increase significantly in poor conditions, so more space and time are needed to react safely", True),
                ("It only matters for motorway driving", False),
                ("It's a legal formality with no real safety benefit", False),
            ],
            "explanation": "Wet or icy roads substantially increase stopping distances, so a greater following distance gives the driver more time and space to stop safely if needed.",
        },
        {
            "topic": "Road safety",
            "prompt": "A driver is dazzled by oncoming headlights at night. What is the safest response?",
            "choices": [
                ("Close both eyes briefly until the glare passes", False),
                ("Slow down, avoid looking directly at the lights, and focus on the left side of the road until vision recovers", True),
                ("Flash headlights back repeatedly", False),
                ("Speed up to get past the glare quickly", False),
            ],
            "explanation": "The safest response to being dazzled is to slow down, avoid staring at the lights, and use the road edge as a visual reference until normal vision returns.",
        },
        {
            "topic": "Road safety",
            "prompt": "What is a legal requirement regarding a private hire vehicle's MOT?",
            "choices": [
                ("MOTs are optional for private hire vehicles", False),
                ("The vehicle must have a valid, up-to-date MOT certificate as a condition of remaining roadworthy and licensed", True),
                ("MOTs are only required once, when the vehicle is first registered", False),
                ("MOTs are the passenger's responsibility, not the driver's", False),
            ],
            "explanation": "A valid, current MOT is a licensing and roadworthiness requirement for a private hire vehicle — it isn't optional or a one-off check.",
        },
        {
            "topic": "Professional conduct",
            "prompt": "A driver disagrees with a passenger's political opinion expressed during the journey. What is the professional response?",
            "choices": [
                ("Argue the point to correct the passenger", False),
                ("Remain neutral, avoid arguing, and keep the conversation respectful or change the subject", True),
                ("Refuse to continue the journey", False),
                ("Share strong opposing views to make a point", False),
            ],
            "explanation": "Professional conduct calls for neutrality on contentious personal topics like politics — staying respectful and steering the conversation elsewhere if needed, rather than arguing.",
        },
        {
            "topic": "Professional conduct",
            "prompt": "Why is it considered unprofessional for a driver to eat a meal while driving passengers?",
            "choices": [
                ("It isn't unprofessional, as long as the driver eats quickly", False),
                ("It is distracting, reduces vehicle control, and reflects poorly on the standard of service", True),
                ("It is only a problem in vehicles with cloth seats", False),
                ("It is a matter of personal taste with no safety relevance", False),
            ],
            "explanation": "Eating while driving is both a distraction and safety risk, and it falls below the professional standard passengers expect during a booked journey.",
        },
        {
            "topic": "Professional conduct",
            "prompt": "Why should a driver check with passengers before playing loud music?",
            "choices": [
                ("It doesn't matter what passengers think as long as the driver enjoys it", False),
                ("Passenger comfort matters, and music choice or volume can be unwelcome or distressing to some passengers", True),
                ("Music is never appropriate in a private hire vehicle", False),
                ("Only classical music is considered acceptable", False),
            ],
            "explanation": "Good customer service means being considerate of passenger comfort, including checking before imposing a music choice or volume on them.",
        },
        {
            "topic": "Professional conduct",
            "prompt": "A driver is running late for a booking because of traffic. What is the professional approach?",
            "choices": [
                ("Say nothing and hope the passenger doesn't notice", False),
                ("Inform the passenger or operator as soon as possible and give a realistic updated time", True),
                ("Cancel the booking rather than explain the delay", False),
                ("Blame the passenger for booking at a busy time", False),
            ],
            "explanation": "Proactively communicating a realistic delay, as soon as it's known, is the professional and courteous response, rather than staying silent or cancelling without explanation.",
        },
        {
            "topic": "Professional conduct",
            "prompt": "Which best reflects professional conduct towards a passenger with a visible disability?",
            "choices": [
                ("Speaking loudly and slowly to all disabled passengers by default", False),
                ("Asking the passenger directly, respectfully, what assistance (if any) they would like, rather than assuming", True),
                ("Avoiding conversation with the passenger altogether", False),
                ("Deciding on the passenger's behalf what help they need", False),
            ],
            "explanation": "Respectful professional conduct means asking rather than assuming — treating the passenger as the best judge of what, if any, assistance they need.",
        },
        {
            "topic": "Licensing",
            "prompt": "What could happen if a private hire driver allows someone else to use their vehicle for private hire work under the driver's own licence?",
            "choices": [
                ("Nothing, as long as the other person is also a competent driver", False),
                ("It would be a serious licensing breach, since a licence is personal to the individual driver", True),
                ("It is allowed for one-off emergencies only", False),
                ("It is only a problem if an accident occurs", False),
            ],
            "explanation": "A private hire driver's licence is personal and non-transferable — letting someone else drive under it is a serious licensing breach regardless of the other person's competence.",
        },
        {
            "topic": "Licensing",
            "prompt": "Why does TfL require private hire operators, as well as drivers, to be licensed?",
            "choices": [
                ("Operator licensing is just a formality with no practical effect", False),
                ("To ensure the whole private hire chain — booking, vehicle and driver — meets required safety and regulatory standards", True),
                ("Only to collect additional licensing fees", False),
                ("Because operators are legally the ones who drive passengers", False),
            ],
            "explanation": "Licensing the operator as well as the driver and vehicle closes the loop on accountability across the whole private hire booking chain.",
        },
        {
            "topic": "Licensing",
            "prompt": "From TfL's perspective, what is the shared purpose of the topographical, SERU and ELR assessments?",
            "choices": [
                ("They exist purely as a revenue source for TfL", False),
                ("To confirm a new driver has the local knowledge, regulatory understanding and language ability needed to serve London passengers safely and professionally", True),
                ("They are only relevant for drivers working nights", False),
                ("They replace the need for a driving test", False),
            ],
            "explanation": "Together, the three assessments confirm the practical knowledge, regulatory awareness and communication ability TfL considers necessary for safe, professional private hire driving in London.",
        },
        {
            "topic": "Licensing",
            "prompt": "A driver's vehicle is involved in an accident. What should happen regarding its private hire licence status?",
            "choices": [
                ("Nothing — licensing is unaffected by accidents", False),
                ("The vehicle may need to be assessed or re-inspected before continuing private hire use, depending on the damage", True),
                ("The driver's own licence is automatically revoked", False),
                ("Only the insurer needs to be informed, with no licensing implications", False),
            ],
            "explanation": "Depending on the extent of any damage, a vehicle involved in an accident may need to be checked or re-inspected before it continues to be used for private hire work.",
        },

        # --- Further fill-in-the-blank (second content-depth expansion) ---
        {
            "topic": "Safeguarding",
            "question_type": "fill_blank",
            "prompt": "A driver who overhears a passenger being threatened on a phone call should report the concern to the operator or police once safe, rather than ____ directly.",
            "accepted_answers": ["intervening", "confronting", "getting involved"],
            "explanation": "Drivers should not intervene or confront directly — the safe response is to report the concern through the proper channel once it is safe to do so.",
        },
        {
            "topic": "Safeguarding",
            "question_type": "fill_blank",
            "prompt": "Drivers are expected to complete safeguarding ____ training as part of becoming and remaining a licensed private hire driver.",
            "accepted_answers": ["awareness"],
            "explanation": "Safeguarding awareness training is a standard part of licensing requirements for private hire drivers.",
        },
        {
            "topic": "Safeguarding",
            "question_type": "fill_blank",
            "prompt": "If a driver is in doubt about whether something is a genuine safeguarding concern, the safest approach is to ____ it anyway through the proper channel.",
            "accepted_answers": ["report"],
            "explanation": "When in doubt, reporting through the proper channel is always the safer choice than staying silent.",
        },
        {
            "topic": "Equality",
            "question_type": "fill_blank",
            "prompt": "Refusing to carry a passenger because of their religion is a breach of the Equality Act and is a form of unlawful ____.",
            "accepted_answers": ["discrimination"],
            "explanation": "Religion is a protected characteristic, so refusing service on that basis is unlawful discrimination.",
        },
        {
            "topic": "Equality",
            "question_type": "fill_blank",
            "prompt": "A driver should offer the same standard of service to every passenger, regardless of ____ characteristics such as race or disability.",
            "accepted_answers": ["protected"],
            "explanation": "'Protected characteristics' is the specific term used in the Equality Act 2010 for traits such as race, disability, age, sex and religion.",
        },
        {
            "topic": "Equality",
            "question_type": "fill_blank",
            "prompt": "Assuming what help a disabled passenger needs, instead of simply ____ them, can come across as patronising or incorrect.",
            "accepted_answers": ["asking"],
            "explanation": "Asking a disabled passenger what help they want, rather than assuming, is the respectful and accurate approach.",
        },
        {
            "topic": "Road safety",
            "question_type": "fill_blank",
            "prompt": "Drivers should never attempt to read or send a text message while the vehicle is ____.",
            "accepted_answers": ["moving"],
            "explanation": "Reading or sending texts while the vehicle is moving is both illegal and extremely dangerous.",
        },
        {
            "topic": "Road safety",
            "question_type": "fill_blank",
            "prompt": "Carrying out a basic vehicle check before a shift, such as checking tyres and lights, helps a driver spot problems ____ they become dangerous.",
            "accepted_answers": ["before"],
            "explanation": "Pre-shift checks are designed to catch small problems early, before they develop into something dangerous on the road.",
        },
        {
            "topic": "Road safety",
            "question_type": "fill_blank",
            "prompt": "A driver who is unsure a route is safe in poor weather should ____ speed and increase following distance.",
            "accepted_answers": ["reduce", "lower"],
            "explanation": "Reducing speed and increasing following distance are the standard, sensible responses to uncertain conditions such as poor weather.",
        },
        {
            "topic": "Professional conduct",
            "question_type": "fill_blank",
            "prompt": "A driver should keep passenger conversations and any personal information shared during a journey ____, rather than repeating them to others afterwards.",
            "accepted_answers": ["confidential", "private"],
            "explanation": "Respecting passenger confidentiality is a core part of professional conduct expected of a licensed private hire driver.",
        },
        {
            "topic": "Professional conduct",
            "question_type": "fill_blank",
            "prompt": "Arriving at a pickup location in good time, where reasonably possible, reflects a driver's ____.",
            "accepted_answers": ["reliability", "professionalism", "punctuality"],
            "explanation": "Punctuality and reliability are core expectations of professional conduct for a private hire driver.",
        },
        {
            "topic": "Professional conduct",
            "question_type": "fill_blank",
            "prompt": "A driver who receives a complaint should respond ____ rather than arguing with the passenger.",
            "accepted_answers": ["calmly", "professionally"],
            "explanation": "Responding calmly and professionally to a complaint, rather than arguing, is the expected standard of conduct.",
        },
        {
            "topic": "Licensing",
            "question_type": "fill_blank",
            "prompt": "A driver whose licence has been suspended must not accept any private hire ____ until the suspension is lifted.",
            "accepted_answers": ["bookings", "work", "jobs"],
            "explanation": "A suspended licence means the driver is not permitted to accept any private hire bookings until the suspension ends.",
        },
        {
            "topic": "Licensing",
            "question_type": "fill_blank",
            "prompt": "TfL may carry out spot ____ of private hire vehicles to confirm they continue to meet licensing standards.",
            "accepted_answers": ["checks", "inspections"],
            "explanation": "Spot checks/inspections are one of the ways TfL enforces ongoing compliance with licensing standards, not just at initial licensing.",
        },
        {
            "topic": "Licensing",
            "question_type": "fill_blank",
            "prompt": "A new private hire driver must pass the English test, SERU and topographical assessments before being issued a full ____.",
            "accepted_answers": ["licence", "license"],
            "explanation": "All three assessments must be passed as part of qualifying for a full TfL private hire driver's licence.",
        },
        {
            "topic": "Licensing",
            "question_type": "fill_blank",
            "prompt": "Operating without valid private hire insurance covering hire and ____ is a serious licensing breach.",
            "accepted_answers": ["reward"],
            "explanation": "Private hire insurance must specifically cover 'hire and reward' use (carrying fare-paying passengers), not just social/domestic use.",
        },

        # --- Further reading & understanding (second content-depth expansion) ---
        {
            "topic": "Reading & understanding",
            "question_type": "reading",
            "passage": (
                "After dropping off a passenger, a driver discovers a phone left on the back seat. "
                "Rather than keeping it or leaving it for the next passenger to find, the driver "
                "contacts the operator straight away, describes the item, and arranges for it to be "
                "safely returned to its owner through the proper lost-property process."
            ),
            "prompt": "According to the passage, what did the driver do correctly on finding the lost phone?",
            "choices": [
                ("Kept the phone in case the owner never claimed it", False),
                ("Contacted the operator promptly and followed the proper lost-property process", True),
                ("Left the phone in the vehicle for the next passenger to find", False),
                ("Tried to return the phone directly without telling the operator", False),
            ],
            "explanation": "The passage describes the driver reporting the item to the operator straight away and going through the proper lost-property process, rather than keeping it, leaving it, or handling it informally.",
        },
        {
            "topic": "Reading & understanding",
            "question_type": "reading",
            "passage": (
                "After dropping off a passenger, a driver discovers a phone left on the back seat. "
                "Rather than keeping it or leaving it for the next passenger to find, the driver "
                "contacts the operator straight away, describes the item, and arranges for it to be "
                "safely returned to its owner through the proper lost-property process."
            ),
            "prompt": "Based on the passage, which of these would have been an inappropriate response to finding the phone?",
            "choices": [
                ("Describing the item accurately to the operator", False),
                ("Keeping the phone or leaving it in the vehicle for someone else to find, rather than reporting it", True),
                ("Arranging for the item to be returned through the proper process", False),
                ("Contacting the operator as soon as possible", False),
            ],
            "explanation": "The passage makes clear that keeping the item or leaving it unreported would fall short of the proper lost-property process the driver actually followed.",
        },
        {
            "topic": "Reading & understanding",
            "question_type": "reading",
            "passage": (
                "A passenger asks the driver to confirm their name before getting in, since the booking "
                "app showed a slightly different name to the one printed on the driver's badge. The "
                "driver calmly explains that the badge shows their full legal name, and reassures the "
                "passenger by showing that the vehicle registration and booking reference match what "
                "was confirmed in the app."
            ),
            "prompt": "According to the passage, how did the driver reassure the passenger?",
            "choices": [
                ("By asking the passenger to cancel and rebook", False),
                ("By calmly explaining the name discrepancy and showing that the vehicle registration and booking reference matched the app", True),
                ("By refusing to discuss the name difference", False),
                ("By asking another driver to take the booking instead", False),
            ],
            "explanation": "The passage describes the driver calmly explaining the badge name and confirming the matching vehicle registration and booking reference, which reassured the passenger.",
        },
        {
            "topic": "Reading & understanding",
            "question_type": "reading",
            "passage": (
                "A passenger asks the driver to confirm their name before getting in, since the booking "
                "app showed a slightly different name to the one printed on the driver's badge. The "
                "driver calmly explains that the badge shows their full legal name, and reassures the "
                "passenger by showing that the vehicle registration and booking reference match what "
                "was confirmed in the app."
            ),
            "prompt": "Why is it reasonable for a passenger to check these details before getting into a private hire vehicle?",
            "choices": [
                ("It isn't reasonable — passengers shouldn't question the driver's identity", False),
                ("To confirm they are getting into the correct, licensed vehicle for their booking, which is good passenger safety practice", True),
                ("Because all bookings are automatically suspicious until checked", False),
                ("Because the app is usually wrong", False),
            ],
            "explanation": "Checking that the vehicle, driver and booking reference match is a sensible passenger-safety habit, not an unreasonable imposition on the driver.",
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

        # --- Additional multiple-choice (content-depth expansion) ---
        {
            "topic": "Compass directions",
            "prompt": "If you are travelling south-east and need to reverse your direction exactly, which way should you now be heading?",
            "choices": [
                ("North-east", False),
                ("South-west", False),
                ("North-west", True),
                ("East", False),
            ],
            "explanation": "The exact opposite of south-east on a compass is north-west — each direction's opposite is the one 180 degrees around the compass.",
        },
        {
            "topic": "Compass directions",
            "prompt": "A passenger asks you to head 'roughly towards the river, then east along it.' Which direction should you be heading overall first?",
            "choices": [
                ("Whichever direction gets you to the nearest stretch of the River Thames, then turn to travel eastward along it", True),
                ("Due north regardless of where the river is", False),
                ("Due south regardless of where the river is", False),
                ("It's impossible to interpret this instruction", False),
            ],
            "explanation": "This instruction requires first identifying the nearest point on the river relative to your position, then heading east once you reach it — exactly the kind of practical direction-following the topographical test assesses.",
        },
        {
            "topic": "Map symbols",
            "prompt": "On a typical street atlas, what does a symbol showing a small building with a cross on top usually represent?",
            "choices": [
                ("A supermarket", False),
                ("A church or other place of worship", True),
                ("A hospital car park", False),
                ("A cemetery boundary", False),
            ],
            "explanation": "A building symbol topped with a cross is a standard map convention for a church or place of worship.",
        },
        {
            "topic": "Map symbols",
            "prompt": "What is the purpose of a one-way street symbol (typically an arrow along the road) on a street atlas?",
            "choices": [
                ("It shows the direction traffic may legally travel on that street", True),
                ("It shows the direction of pedestrian footfall only", False),
                ("It indicates a recommended scenic route", False),
                ("It has no functional meaning, purely decorative", False),
            ],
            "explanation": "A one-way arrow on a map shows the only legal direction of travel on that street — ignoring it when planning a route would make the route illegal.",
        },
        {
            "topic": "Grid references",
            "prompt": "Why might a street atlas use a letter-and-number grid reference (e.g. '4B') rather than numbers alone?",
            "choices": [
                ("It has no practical benefit over numbers alone", False),
                ("Combining a letter (column) and number (row) lets you pinpoint a smaller, more specific square on the page", True),
                ("Letters are only used for motorway junctions", False),
                ("It's purely a stylistic choice with no effect on precision", False),
            ],
            "explanation": "A letter-and-number grid reference narrows a location down using two independent coordinates (column and row), giving a more precise square than a single number alone.",
        },
        {
            "topic": "Road rules and restrictions",
            "prompt": "A road on the map is marked as having a width restriction. What does this mean for route planning?",
            "choices": [
                ("It only affects cyclists, not private hire vehicles", False),
                ("Some vehicles may not be able to pass through legally or physically, so this should be factored into route choice", True),
                ("It means the road is closed entirely to all traffic", False),
                ("It has no bearing on route planning for a standard private hire vehicle", False),
            ],
            "explanation": "A width restriction can affect whether a given vehicle can legally or physically use that road, so it's a genuine factor in planning a route, not something to ignore.",
        },
        {
            "topic": "Road rules and restrictions",
            "prompt": "What does a 'no entry' symbol at the start of a street mean for route planning?",
            "choices": [
                ("Vehicles cannot enter the street from that end at all", True),
                ("Only buses may enter from that end", False),
                ("The street is one-way, but entry from that end is still allowed at certain times", False),
                ("It is only a warning, not a legal restriction", False),
            ],
            "explanation": "A 'no entry' symbol means vehicles are not permitted to enter the street from that point — a legally compliant route must avoid it, not just note it as a warning.",
        },
        {
            "topic": "London geography",
            "prompt": "Which river is the single most significant geographic reference point for orientation across central London?",
            "choices": [
                ("The River Thames", True),
                ("The River Lea", False),
                ("The Regent's Canal", False),
                ("The River Wandle", False),
            ],
            "explanation": "The Thames is the dominant geographic reference for orientation across London, commonly used to describe north/south position.",
        },
        {
            "topic": "London geography",
            "prompt": "Why is it useful to know which side of the River Thames a destination is on before planning a route?",
            "choices": [
                ("It isn't useful — all bridges are freely interchangeable with no practical difference", False),
                ("Crossing points are limited to specific bridges or tunnels, which significantly affects route choice and timing", True),
                ("It only matters for journeys outside London", False),
                ("The river has no bearing on road routes, only river traffic", False),
            ],
            "explanation": "Since the Thames can only be crossed at specific bridges or tunnels, knowing which side your destination is on is essential for planning a sensible, direct route.",
        },
        {
            "topic": "Route planning",
            "prompt": "When planning a route, why should a driver avoid relying solely on 'shortest distance' without checking for restrictions?",
            "choices": [
                ("Shortest distance always produces a legal route, so no further checking is needed", False),
                ("A shorter route on paper may include one-way streets, width restrictions or closures that make it illegal or impossible to actually drive", True),
                ("Restrictions never apply to private hire vehicles", False),
                ("It's not something the topographical assessment actually tests", False),
            ],
            "explanation": "The shortest route by distance isn't necessarily legal or drivable — restrictions such as one-way streets must be checked, which is exactly what the real route-planning questions assess.",
        },

        # --- Further multiple-choice (content-depth expansion) ---
        {
            "topic": "Compass directions",
            "prompt": "You are facing south-west and need to end up travelling north-east. What have you done?",
            "choices": [
                ("Turned 90 degrees", False),
                ("Turned 180 degrees — reversed your direction of travel", True),
                ("Not changed direction at all", False),
                ("Turned 45 degrees", False),
            ],
            "explanation": "South-west and north-east are directly opposite directions, so getting from one to the other is a 180-degree turn.",
        },
        {
            "topic": "Compass directions",
            "prompt": "A passenger asks you to head 'roughly north-east' from your current position. Which of these best matches that instruction?",
            "choices": [
                ("Directly north only", False),
                ("Between north and east, leaning toward a 45-degree heading", True),
                ("Directly south", False),
                ("Due west", False),
            ],
            "explanation": "North-east sits roughly halfway between north and east, around a 45-degree compass heading.",
        },
        {
            "topic": "Map symbols",
            "prompt": "On a typical road map, what does a symbol showing a tunnel usually indicate for a private hire driver?",
            "choices": [
                ("A pedestrian-only area", False),
                ("A section of road passing underground, which may have restrictions such as height limits", True),
                ("A permanently closed road", False),
                ("A speed camera location", False),
            ],
            "explanation": "Tunnel symbols mark underground road sections, which can carry restrictions like height limits that matter for vehicle route planning.",
        },
        {
            "topic": "Road rules and restrictions",
            "prompt": "What does a 'bus gate' restriction typically mean for a private hire driver?",
            "choices": [
                ("It is a bus stop with no restriction on other vehicles", False),
                ("It is a road section that only buses (and usually cyclists/taxis, depending on signage) may use, excluding ordinary private vehicles", True),
                ("It is a car park reserved for buses only", False),
                ("It has no practical effect on route planning", False),
            ],
            "explanation": "A bus gate restricts a road section to specific vehicle types as shown on the sign — driving through one when not permitted can result in a penalty, so it must be factored into route planning.",
        },
        {
            "topic": "Road rules and restrictions",
            "prompt": "A road sign shows a width restriction (e.g. '6'6\" width limit'). What should a driver do?",
            "choices": [
                ("Ignore it, since private hire vehicles are always exempt", False),
                ("Check their vehicle's width against the limit and avoid the road if the vehicle exceeds it", True),
                ("Only worry about it if towing a trailer", False),
                ("Proceed slowly regardless of vehicle width", False),
            ],
            "explanation": "A width restriction applies to any vehicle exceeding the stated limit — drivers must check their own vehicle's width and choose an alternative route if it doesn't comply.",
        },
        {
            "topic": "Route planning",
            "prompt": "Why might a driver deliberately choose a slightly longer route over the shortest one shown on a map?",
            "choices": [
                ("To increase the fare unfairly", False),
                ("Because the shortest route may be subject to restrictions, closures or heavy congestion that make it slower or illegal to use", True),
                ("Longer routes are always required by TfL", False),
                ("There is never a good reason to do this", False),
            ],
            "explanation": "A genuinely efficient route accounts for real-world restrictions and congestion, not just raw distance — sometimes a longer route on paper is faster or the only legal option.",
        },
        {
            "topic": "Route planning",
            "prompt": "A planned route includes a road currently closed for roadworks. What is the correct approach?",
            "choices": [
                ("Continue as planned and deal with it on arrival", False),
                ("Identify a suitable legal alternative before or as soon as the closure is reached", True),
                ("Reverse the entire journey and start again from the pickup point", False),
                ("Ignore the closure signage if no one appears to be working", False),
            ],
            "explanation": "A driver should plan around a known closure with a suitable legal alternative, rather than ignoring signage or treating the closure as something to improvise around at the last moment.",
        },
        {
            "topic": "Route planning",
            "prompt": "Why is it useful for a driver to have a general mental map of London's key areas, even when using a satnav?",
            "choices": [
                ("It isn't useful — satnavs make background knowledge unnecessary", False),
                ("It helps the driver sense-check satnav directions and recover quickly if the device fails or gives an odd route", True),
                ("It is only useful for passing the assessment, not for real driving", False),
                ("It replaces the need to follow traffic regulations", False),
            ],
            "explanation": "Background geographic knowledge lets a driver notice an obviously wrong satnav instruction and cope if the device fails — exactly the skill the topographical assessment is testing.",
        },
        {
            "topic": "Grid references",
            "prompt": "On a standard map grid reference, which number is given first?",
            "choices": [
                ("The vertical (north-south) grid line number", False),
                ("The horizontal (west-east, 'along the corridor') grid line number", True),
                ("Whichever number is smaller", False),
                ("There is no fixed order", False),
            ],
            "explanation": "The convention 'along the corridor, up the stairs' means the horizontal (easting/west-east) reference is always given before the vertical (northing) reference.",
        },
        {
            "topic": "London geography",
            "prompt": "Why does it matter to a private hire driver which side of the Thames a pickup and drop-off are on?",
            "choices": [
                ("It doesn't matter — all roads connect freely regardless of the river", False),
                ("River crossings are limited to specific bridges or tunnels, which significantly affects route choice and journey time", True),
                ("It only matters for journeys longer than 10 miles", False),
                ("It affects the fare but never the route", False),
            ],
            "explanation": "Because the Thames can only be crossed at specific points, knowing which side a destination is on is essential for choosing a sensible route and estimating journey time accurately.",
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

    speaking_added = 0
    for item in SPEAKING_PROMPTS:
        existing = SpeakingPrompt.query.filter_by(prompt_text=item["prompt_text"]).first()
        if existing:
            continue
        db.session.add(
            SpeakingPrompt(
                module_slug="elr",
                topic=item["topic"],
                prompt_text=item["prompt_text"],
                model_answer=item["model_answer"],
                tips=item.get("tips"),
            )
        )
        speaking_added += 1
    db.session.commit()
    summary.append(f"speaking prompts: {speaking_added} new prompt(s) added")

    admin_email = "admin@example.com"
    admin_created = False
    if not User.query.filter_by(email=admin_email).first():
        admin = User(email=admin_email, full_name="Admin", is_admin=True)
        admin.set_password("change-this-password")
        db.session.add(admin)
        db.session.commit()
        admin_created = True

    return summary, admin_created
