"""Example transcripts NoteGenerator.generate() could realistically receive, covering both
typical exam-room visits and edge cases (missing info, multiple patients, irrelevant
chatter, garbled ASR output) that the SOAP_SYSTEM_PROMPT's "Not discussed" instruction and
provider parsing need to hold up against.

Each Case's metadata may include "must_include": a dict of SoapNote field name -> list of
substrings that should appear (case-insensitively) in that field, checked by
evals.evaluators.FieldKeywordCoverage.
"""

from pydantic_evals import Case

CASES = [
    Case(
        name="routine_wellness_exam",
        inputs=(
            "Vet: Bring Biscuit up here for me. So he's in for his annual wellness visit today. "
            "Owner: Yep, just the usual checkup and he's due for shots. Vet: Great, he's looking "
            "good, nice and shiny coat. Weight is 62 pounds, up two pounds from last year but "
            "still in a healthy range for a lab mix. Heart rate 90, lungs clear, temp 101.4. "
            "Teeth look decent, a little tartar building on the molars. I'm going to give him "
            "the DHPP and rabies boosters today. Owner: Sounds good. Vet: He's all set, no "
            "concerns. See you next year, keep up with the heartworm prevention monthly."
        ),
        metadata={
            "category": "routine",
            "must_include": {
                "subjective": ["annual", "wellness"],
                "objective": ["62", "101.4"],
                "plan": ["dhpp", "rabies"],
            },
        },
    ),
    Case(
        name="acute_gi_illness",
        inputs=(
            "Owner: He's been throwing up since yesterday morning, probably five or six times, "
            "and he won't touch his food. Vet: Any diarrhea? Owner: A little, yeah, this morning. "
            "Vet: Okay. Rex, let's take a look at you. Temp is 102.1, that's a bit elevated. "
            "Gums are a little tacky, mild dehydration, maybe 5%. Abdomen is a little tense but "
            "no obvious mass. Owner: Could he have eaten something? Vet: Possible, he's a "
            "labrador after all. My read is acute gastroenteritis, could be dietary indiscretion. "
            "I want to start him on subcutaneous fluids today, give him a Cerenia injection for "
            "the nausea, and send you home with a bland diet, boiled chicken and rice, for the "
            "next three days. If he's not improving by tomorrow, call us or head to the ER."
        ),
        metadata={
            "category": "sick_visit",
            "must_include": {
                "subjective": ["vomiting"],
                "objective": ["102.1", "dehydrat"],
                "assessment": ["gastroenteritis"],
                "plan": ["fluids", "cerenia", "bland diet"],
            },
        },
    ),
    Case(
        name="emergency_trauma",
        inputs=(
            "Owner: She got hit by a car, oh my god, she was just in the driveway. Vet: Okay, "
            "we've got her, let's move fast. Gums are pale, cap refill is over three seconds, "
            "heart rate 180, femoral pulses are weak. She's got obvious deformity of the right "
            "hind leg, probably fractured. Breathing is rapid and shallow. Get me an IV catheter "
            "and start a bolus of lactated ringers, and pull blood for a PCV and total solids. "
            "I'm worried about internal bleeding, we need chest and abdominal films as soon as "
            "she's stable enough. Owner: Is she going to be okay? Vet: She's critical right now, "
            "we're doing everything we can, I'll update you as soon as we know more."
        ),
        metadata={
            "category": "emergency",
            "must_include": {
                "subjective": ["hit by a car"],
                "objective": ["pale", "180", "fracture"],
                "plan": ["iv", "fluids", "radiograph"],
            },
        },
    ),
    Case(
        name="multi_pet_visit",
        inputs=(
            "Owner: I brought both of them in today, figured I'd save a trip. Vet: No problem, "
            "let's start with Whiskers. She's here for the itchy skin you mentioned on the phone. "
            "I see some redness and hair loss around the base of the tail, looks like flea "
            "allergy dermatitis, I don't see any fleas now but that's consistent with the "
            "pattern. I'll send you home with a topical flea preventative and a short course of "
            "an anti-itch medication. Now for Tom, he's just here for his rabies booster, "
            "correct? Owner: Right, he's due. Vet: Tom looks great otherwise, weight's stable at "
            "11 pounds, heart and lungs sound normal. Giving him the rabies vaccine now."
        ),
        metadata={
            "category": "multi_patient",
            "must_include": {
                "assessment": ["flea allergy dermatitis"],
                "plan": ["flea", "rabies"],
            },
        },
    ),
    Case(
        name="vague_incomplete_transcript",
        inputs=(
            "Owner: Hey doc. Vet: Hey, how's it going. So what brings you in today. Owner: Yeah "
            "he's just been kind of off. Vet: Off how? Owner: I don't know, just not himself. "
            "Vet: Okay, well let's take a look. Yeah, hmm. Owner: What do you think? Vet: I'm "
            "not totally sure yet, let me think about it and get back to you."
        ),
        metadata={"category": "low_information"},
    ),
    Case(
        name="owner_declines_treatment",
        inputs=(
            "Vet: Based on what I'm feeling on that mass, and given her age, I'd really like to "
            "run bloodwork and get X-rays before we decide anything, and honestly I think "
            "surgical removal and biopsy is the right call here. Owner: I hear you, but money's "
            "really tight right now, I can't do the full workup today. Vet: I understand. At "
            "minimum I'd like to monitor it closely, can you check it weekly and let me know if "
            "it changes size, color, or if she starts licking at it? Owner: Yeah, I can do that. "
            "Vet: Okay, let's plan to recheck in three weeks, and if it grows at all before "
            "then, please bring her back in sooner, even if that means we have to figure out "
            "financing for the surgery."
        ),
        metadata={
            "category": "declined_care",
            "must_include": {"plan": ["recheck", "three weeks"]},
        },
    ),
    Case(
        name="chronic_condition_recheck",
        inputs=(
            "Vet: So this is the three month recheck for her diabetes. How's she doing on the "
            "insulin? Owner: Good I think, she's drinking less water than she was. Vet: That's a "
            "great sign. Let's get a fructosamine level and a quick glucose curve today. ... "
            "Okay, fructosamine came back at 380, that's improved from 520 last time but still "
            "above target. Weight's stable at 9.2 kilos. I want to bump her Lantus up slightly, "
            "from 2 units to 2.5 units twice daily, and recheck the fructosamine again in six "
            "weeks. Keep feeding the prescription diabetic diet, no changes there."
        ),
        metadata={
            "category": "chronic_recheck",
            "must_include": {
                "objective": ["380", "9.2"],
                "plan": ["lantus", "2.5", "six weeks"],
            },
        },
    ),
    Case(
        name="garbled_partial_transcript",
        inputs=(
            "-- can't really hear -- something about the leg -- limping since -- [inaudible] -- "
            "yeah he does that -- okay let's -- [static] -- put weight on it fine when -- I "
            "think maybe -- [inaudible] -- x-ray just to be safe -- okay -- thanks doc --"
        ),
        metadata={"category": "poor_audio"},
    ),
    Case(
        name="dental_procedure_consult",
        inputs=(
            "Vet: Let's talk about Max's teeth. On exam I'm seeing grade 3 periodontal disease, "
            "heavy tartar buildup on the upper premolars and molars, some gum recession, and a "
            "couple of teeth that look mobile, probably the upper fourth premolar and first "
            "molar on the right side. Owner: Is that serious? Vet: It can lead to infection and "
            "pain if we don't address it, and it's likely already uncomfortable for him. I'd "
            "recommend a dental cleaning under anesthesia with full mouth X-rays, and we should "
            "plan on extracting those two mobile teeth. Owner: What's the cost looking like? "
            "Vet: I'll have the front desk put together an estimate, but plan for anesthesia, "
            "cleaning, X-rays, and possible extractions. We can schedule for next Tuesday if "
            "that works, and he'll need to fast the night before."
        ),
        metadata={
            "category": "dental",
            "must_include": {
                "objective": ["periodontal", "tartar"],
                "plan": ["dental cleaning", "extract"],
            },
        },
    ),
    Case(
        name="non_clinical_chitchat_with_embedded_complaint",
        inputs=(
            "Owner: Traffic was insane getting here, is the parking lot getting repaved? Vet: "
            "Yeah I heard that's happening next month, annoying isn't it. Owner: Totally. Oh, "
            "and how was your vacation, did you go to the lake house again? Vet: We did, it was "
            "great, weather was perfect the whole week. Anyway, so what's going on with Luna "
            "today? Owner: Oh right, sorry, she's been scratching her left ear a lot and there's "
            "kind of a brown discharge and a smell. Vet: Let's take a look. Yeah, ear canal is "
            "red and inflamed, I can see debris, this looks like a yeast infection. I'll clean "
            "it out and send you home with an ear medication, apply twice daily for ten days. "
            "Owner: Great, thanks. So are you doing anything for the holidays?"
        ),
        metadata={
            "category": "irrelevant_chatter",
            "must_include": {
                "subjective": ["ear", "scratching"],
                "assessment": ["yeast"],
                "plan": ["ear medication", "ten days"],
            },
        },
    ),
]
