from __future__ import annotations
import re

YES={"yes","y","sure","include it","include","important","needed","want it","ναι","βεβαιως","βεβαίως","θελω","θέλω"}
NO={"no","n","not needed","no thanks","none","όχι","οχι","δεν με ενδιαφερει","δεν με ενδιαφέρει"}


def _norm(text: str) -> str:
    return re.sub(r"\s+"," ",(text or "").strip().lower())


def _has_any(text: str, terms: set[str]) -> bool:
    return any(t in text for t in terms)


def _extract_amount(text: str) -> float | None:
    """Extract a simple guided amount such as €500 or Budget €3,000."""
    m=re.search(r"(?:€|eur)?\s*([0-9][0-9,.]*)", text or "", flags=re.I)
    if not m:
        return None
    try:
        return float(m.group(1).replace(",",""))
    except Exception:
        return None


def apply_discovery_answer(message: str, state: dict) -> dict:
    """Interpret short answers according to HAL's current guided question."""
    pending=state.get("pending_question")
    if not pending:
        return {}
    text=_norm(message)
    out={}

    # Core identity/location answers must also work as short guided replies.
    # Without this, answers such as "Greece" / "in Greece" can loop forever
    # while HAL is waiting for residence.
    if pending=="age":
        m=re.search(r"\b(\d{1,3})\b",text)
        if m:
            age=int(m.group(1))
            if 0 <= age <= 120:
                out["age"]=age

    elif pending=="residence":
        raw=text.strip(" .,!?:;")
        aliases={
            "greece":"Greece","hellas":"Greece","ελλάδα":"Greece","ελλαδα":"Greece",
            "uk":"United Kingdom","u.k.":"United Kingdom","united kingdom":"United Kingdom",
            "england":"United Kingdom",
            "usa":"United States","u.s.a.":"United States","united states":"United States",
            "united states of america":"United States",
        }
        # Strip common answer prefixes while preserving the actual country.
        cleaned=re.sub(
            r"^(?:i\s+(?:live|reside)\s+in|i'?m\s+(?:living|resident)\s+in|"
            r"living\s+in|resident\s+in|residing\s+in|in|"
            r"μένω\s+(?:στη|στην|στο|σε)|μενω\s+(?:στη|στην|στο|σε)|"
            r"κατοικώ\s+(?:στη|στην|στο|σε)|κατοικω\s+(?:στη|στην|στο|σε))\s+",
            "",
            raw,
            flags=re.I,
        ).strip(" .,!?:;")
        canonical=aliases.get(cleaned.lower())
        if canonical:
            out["residence_country"]=canonical
        elif cleaned and len(cleaned)<=80 and re.fullmatch(r"[A-Za-zÀ-ÖØ-öø-ÿΑ-Ωα-ωΆ-ώ .'-]+",cleaned):
            out["residence_country"]=" ".join(part.capitalize() for part in cleaned.split())

    elif pending=="coverage_area":
        if any(x in text for x in [
            "worldwide including usa","worldwide incl usa","including usa",
            "worldwide with usa","με ηπα","με usa",
        ]):
            out["coverage_area"]="area4"
        elif any(x in text for x in [
            "worldwide excluding usa, singapore, hong kong","worldwide excluding usa singapore hong kong",
            "excluding usa, singapore","excl usa singapore","area 2",
        ]):
            out["coverage_area"]="area2"
        elif any(x in text for x in [
            "worldwide excluding usa","worldwide excl usa","excluding usa","without usa",
            "χωρίς ηπα","χωρις ηπα",
        ]):
            out["coverage_area"]="area3"
        elif any(x in text for x in [
            "europe","europe only","eu only","ευρώπη","ευρωπη",
        ]):
            out["coverage_area"]="area1"

    if pending=="deductible":
        if any(x in text for x in ["flexible","no preference","any deductible","whatever","χωρις προτιμηση","χωρίς προτίμηση","ευελικ"]):
            out["deductible_answered"]=True
            out["deductible_preference"]="flexible"
        else:
            amount=_extract_amount(text)
            if amount is not None:
                out["deductible"]=amount
                out["deductible_answered"]=True
                out["deductible_preference"]="fixed"

    elif pending=="outpatient":
        if any(x in text for x in ["hospital only","inpatient only","hospitalisation only","hospitalization only","νοσοκομειακη μονο","νοσοκομειακή μόνο","μονο νοσοκομ","μόνο νοσοκομ"]):
            out.update(outpatient_required=False,outpatient_answered=True)
        elif _has_any(text,{"outpatient","include outpatient","comprehensive","doctor visits","diagnostic","εξωνοσοκομ","ιατρ","διαγνωσ"}) or _has_any(text,YES):
            out.update(outpatient_required=True,outpatient_answered=True)
        elif _has_any(text,NO):
            out.update(outpatient_required=False,outpatient_answered=True)

    elif pending in {"maternity","dental","mental_health","evacuation"}:
        field={
            "maternity":"maternity_required",
            "dental":"dental_required",
            "mental_health":"mental_health_required",
            "evacuation":"evacuation_required",
        }[pending]
        answered=f"{pending}_answered"
        if _has_any(text,YES): out.update({field:True,answered:True})
        elif _has_any(text,NO): out.update({field:False,answered:True})
        else:
            keywords={
                "maternity":{"maternity","pregnancy","childbirth","τοκετ","εγκυμοσ","μητροτ"},
                "dental":{"dental","dentist","οδοντ"},
                "mental_health":{"mental health","psycholog","psychiatr","ψυχολ","ψυχιατρ"},
                "evacuation":{"evacuation","repatriation","διακομιδ","επαναπατρ"},
            }[pending]
            if _has_any(text,keywords): out.update({field:True,answered:True})

    elif pending=="budget":
        if any(x in text for x in ["no fixed budget","no budget","flexible budget","budget flexible","χωρις budget","χωρίς budget","χωρις συγκεκριμενο","χωρίς συγκεκριμένο"]):
            out.update(budget_answered=True,budget_preference="flexible")
        else:
            amount=_extract_amount(text)
            if amount is not None:
                out.update(budget_annual=amount,budget_answered=True,budget_preference="fixed")

    if out:
        out["pending_question"]=None
    return out


def _q(key: str, reply: str, choices: list[tuple[str,str]] | None=None) -> dict:
    return {
        "key":key,
        "reply":reply,
        "quick_replies":[{"label":a,"value":b} for a,b in (choices or [])],
    }


def next_discovery_question(state: dict, greek: bool=False) -> dict | None:
    """Return the next core advice question. None means shortlist-ready."""
    if not state.get("age"):
        return _q("age","Πόσων ετών είναι το άτομο που θα ασφαλιστεί;" if greek else "How old is the person to be insured?")
    if not state.get("residence_country"):
        return _q("residence","Σε ποια χώρα κατοικεί μόνιμα;" if greek else "Which country does the applicant normally reside in?")
    if not state.get("coverage_area"):
        return _q("coverage_area",
            "Πού θέλετε να ισχύει η κάλυψη;" if greek else "Where would you like the policy to provide cover?",
            [("Europe","Europe only"),("Worldwide excl. USA","Worldwide excluding USA"),("Worldwide incl. USA","Worldwide including USA")])
    if not state.get("deductible_answered"):
        text=("Τι απαλλαγή θα προτιμούσατε; Η απαλλαγή (deductible/excess) είναι το ποσό που αναλαμβάνετε εσείς πριν ή μαζί με τη συμμετοχή της ασφαλιστικής, ανάλογα με τους όρους του plan. Μεγαλύτερη απαλλαγή συνήθως μειώνει το ασφάλιστρο."
              if greek else
              "What deductible would you prefer? A deductible/excess is the amount you agree to pay yourself before or alongside the insurer's contribution, depending on the plan terms. A higher deductible will often reduce the premium.")
        return _q("deductible",text,[("€0","€0 deductible"),("€500","€500 deductible"),("€1,000","€1000 deductible"),("Flexible","No preference on deductible")])
    if not state.get("outpatient_answered"):
        text=("Θέλετε μόνο νοσοκομειακή κάλυψη ή και εξωνοσοκομειακή; Εξωνοσοκομειακή κάλυψη σημαίνει περίθαλψη χωρίς εισαγωγή στο νοσοκομείο — π.χ. επισκέψεις σε ιατρούς/specialists, διαγνωστικές εξετάσεις και, ανάλογα με το plan, φάρμακα ή φυσιοθεραπεία."
              if greek else
              "Would you like hospital-only cover, or should the plan also include outpatient care? Outpatient cover means treatment without a hospital admission—for example doctor/specialist visits, diagnostic tests and, depending on the plan, medicines or physiotherapy.")
        return _q("outpatient",text,[("Hospital only","Hospital only"),("Include outpatient","Include outpatient cover")])
    age=int(state.get("age") or 0)
    if 18 <= age <= 45 and not state.get("maternity_answered"):
        text=("Σας ενδιαφέρει routine maternity κάλυψη για εσάς ή για κάποιο μέλος που θα ασφαλιστεί; Είναι σημαντικό να το ξέρουμε από την αρχή, γιατί συνήθως υπάρχουν waiting periods και δεν την προσφέρουν όλα τα plans."
              if greek else
              "Is routine maternity cover important for you or anyone who will be insured? It is important to decide this early because maternity usually has a waiting period and is not available on every plan.")
        return _q("maternity",text,[("Yes, maternity","Yes, maternity is required"),("No","No maternity needed")])
    if not state.get("maternity_answered"):
        state["maternity_answered"]=True
    if not state.get("dental_answered"):
        return _q("dental","Σας ενδιαφέρει και οδοντιατρική κάλυψη;" if greek else "Would you like dental cover as part of the plan?",[("Yes","Yes, dental is important"),("No","No dental needed")])
    if not state.get("mental_health_answered"):
        text=("Θέλετε κάλυψη mental health, όπως psychologist/psychiatrist treatment, όπου το plan το προβλέπει;"
              if greek else "Would you like mental-health cover, such as psychologist/psychiatrist treatment where the plan provides it?")
        return _q("mental_health",text,[("Yes","Yes, mental health is important"),("No","No mental health cover needed")])
    if not state.get("evacuation_answered"):
        text=("Σας ενδιαφέρει medical evacuation / repatriation — δηλαδή οργανωμένη διακομιδή σε κατάλληλο νοσοκομείο όταν η απαιτούμενη θεραπεία δεν είναι διαθέσιμη τοπικά, σύμφωνα με τους όρους του plan;"
              if greek else "Is medical evacuation/repatriation important to you—meaning insurer-arranged transport to a suitable hospital when the required treatment is not available locally, subject to the plan terms?")
        return _q("evacuation",text,[("Yes","Yes, evacuation is important"),("No","No evacuation priority")])
    if not state.get("budget_answered"):
        return _q("budget","Έχετε κάποιο προτιμώμενο ετήσιο budget; Μπορείτε και να το αφήσετε ανοιχτό ώστε ο HAL να δώσει προτεραιότητα στην κάλυψη." if greek else "Do you have a preferred annual budget? You can leave it open if you want HAL to prioritise coverage rather than price.",[("No fixed budget","No fixed budget"),("Up to €3,000","Budget €3000"),("Up to €5,000","Budget €5000"),("Up to €8,000","Budget €8000")])
    return None


def discovery_progress(state: dict) -> dict:
    keys=["age","residence_country","coverage_area","deductible_answered","outpatient_answered","dental_answered","mental_health_answered","evacuation_answered","budget_answered"]
    age=int(state.get("age") or 0)
    if 18 <= age <= 45: keys.insert(5,"maternity_answered")
    done=sum(bool(state.get(k)) for k in keys)
    return {"completed":done,"total":len(keys),"percent":round(done/max(len(keys),1)*100)}
