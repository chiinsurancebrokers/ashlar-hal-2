from __future__ import annotations

import json
import re
from typing import Any

import httpx

from backend.app.core.config import get_settings
from backend.app.providers.service import provider_context, provider_definition
from backend.app.schemas.applicant import Applicant
from backend.app.rates.registry import quote_current
from backend.app.services.leads import classify_journey, lead_intent, journey_cta
from backend.app.knowledge.service import (
    education_context,
    destination_context,
    international_vs_local,
    destination,
    destination_sources,
    hnwi_context,
    hnwi_ipmi,
    ipmi_value_context,
    ipmi_value_proposition,
)


BOOL_FIELDS = {
    "outpatient_required","maternity_required","dental_required",
    "mental_health_required","wellness_required","optical_required",
    "evacuation_required","chronic_required",
    "private_hospital_choice_required","cross_border_treatment_required",
    "home_country_treatment_required","continuity_portability_required",
    "high_annual_limit_required","private_room_required","direct_billing_required",
    "second_medical_opinion_required",
}
ALLOWED_FIELDS = {
    "age","residence_country","nationality","coverage_area","currency",
    "deductible","budget_annual","client_segment","journey",*BOOL_FIELDS,
}

AREA_HELP = {
    "area1":"Europe",
    "area2":"Worldwide excluding USA, Singapore, Hong Kong and China",
    "area3":"Worldwide excluding USA",
    "area4":"Worldwide including USA",
}


def _is_greek(text: str) -> bool:
    return bool(re.search(r"[\u0370-\u03ff]", text or ""))


def _extract_json(text: str) -> dict:
    """Best-effort structured parsing. Never raise merely because the LLM used prose."""
    raw=(text or "").strip()
    if not raw:
        return {"reply":"","applicant_updates":{},"provider_sources_used":[],"knowledge_sources_used":[]}

    cleaned=raw
    if cleaned.startswith("```"):
        cleaned=re.sub(r"^```(?:json)?\s*|\s*```$", "", cleaned, flags=re.I|re.S).strip()

    try:
        parsed=json.loads(cleaned)
        if isinstance(parsed,dict):
            return parsed
    except Exception:
        pass

    m=re.search(r"\{.*\}", cleaned, flags=re.S)
    if m:
        try:
            parsed=json.loads(m.group(0))
            if isinstance(parsed,dict):
                return parsed
        except Exception:
            pass

    # A plain-language model response is still a usable answer.
    return {
        "reply": cleaned,
        "applicant_updates": {},
        "provider_sources_used": [],
        "knowledge_sources_used": [],
    }


def _clean_updates(updates: dict[str, Any]) -> dict[str, Any]:
    clean={}
    for key,value in (updates or {}).items():
        if key not in ALLOWED_FIELDS or value is None:
            continue
        if key in BOOL_FIELDS:
            clean[key]=bool(value)
        elif key=="age":
            try:
                value=int(value)
                if 0 <= value <= 120:
                    clean[key]=value
            except Exception:
                pass
        elif key in {"deductible","budget_annual"}:
            try:
                v=float(value)
                if v >= 0:
                    clean[key]=v
            except Exception:
                pass
        elif key=="coverage_area":
            if value in AREA_HELP:
                clean[key]=value
        elif key in {"client_segment","journey"}:
            clean[key]=str(value)[:80]
        else:
            clean[key]=str(value)[:150]
    return clean


def _merge_state(state: dict, updates: dict) -> dict:
    merged=dict(state or {})
    merged.update(_clean_updates(updates))
    merged.setdefault("currency","EUR")
    return merged


def _deterministic_updates(message: str, state: dict, history: list[dict] | None = None) -> dict:
    """Extract high-confidence facts without relying on an LLM."""
    text=(message or "").strip()
    lower=text.lower()
    updates={}

    # A bare number after an age question is almost certainly age.
    if "age" not in state:
        m=re.fullmatch(r"\s*(\d{1,3})\s*(?:years?|yrs?|yo|y/o)?\s*", lower)
        if m and 0 <= int(m.group(1)) <= 120:
            updates["age"]=int(m.group(1))
        else:
            m=re.search(r"\b(?:i am|i'm|aged|age is|είμαι|ειμαι)\s*(\d{1,3})\b", lower)
            if m and 0 <= int(m.group(1)) <= 120:
                updates["age"]=int(m.group(1))

    if any(x in lower for x in ["greece","hellas","ελλάδα","ελλαδα"]):
        if any(x in lower for x in ["live","living","reside","resident","μένω","μενω","κατοικ"]):
            updates["residence_country"]="Greece"

    # Geographic scope.
    if any(x in lower for x in ["worldwide including usa","worldwide incl usa","including usa","με ηπα","με usa"]):
        updates["coverage_area"]="area4"
    elif any(x in lower for x in ["worldwide excluding usa","worldwide excl usa","χωρίς ηπα","χωρις ηπα","excluding usa"]):
        updates["coverage_area"]="area3"
    elif any(x in lower for x in ["europe only","cover in europe","coverage in europe","ευρώπη","ευρωπη"]):
        updates["coverage_area"]="area1"

    # High-confidence needs.
    keywords={
        "outpatient_required":["outpatient","εξωνοσοκομ"],
        "maternity_required":["maternity","pregnancy","τοκετ","μητρότ","μητροτ"],
        "dental_required":["dental","dentist","οδοντ"],
        "mental_health_required":["mental health","psychiatr","psycholog","ψυχικ","ψυχιατρ","ψυχολ"],
        "wellness_required":["wellness","check-up","check up","screening","προληπ"],
        "optical_required":["optical","eye test","glasses","vision","οπτικ","γυαλ"],
        "evacuation_required":["evacuation","repatriation","διακομιδ","επαναπατρ"],
        "chronic_required":["chronic","χρόνι","χρονι"],
        "private_hospital_choice_required":["private hospital","hospital choice","choice of hospital","ιδιωτικ", "επιλογή νοσοκομ", "επιλογη νοσοκομ"],
        "cross_border_treatment_required":["treatment abroad","treatment overseas","cross-border","abroad for treatment","θεραπεία στο εξωτερικό","θεραπεια στο εξωτερικο"],
        "continuity_portability_required":["portability","relocate","move country","continuity","μετακομ","αλλάξω χώρα","αλλαξω χωρα"],
        "high_annual_limit_required":["high limit","high annual limit","maximum cover","μεγάλο όριο","μεγαλο οριο"],
        "private_room_required":["private room","μονόκλινο","μονοκλινο"],
        "direct_billing_required":["direct billing","direct settlement","απευθείας πληρωμή","απευθειας πληρωμη"],
        "second_medical_opinion_required":["second opinion","second medical opinion","δεύτερη γνώμη","δευτερη γνωμη"],
    }
    for field,words in keywords.items():
        if any(w in lower for w in words):
            updates[field]=True

    if any(x in lower for x in ["hnwi","high net worth","high-net-worth","affluent","wealthy","family office","ευκατάστα","ευκαταστα","εύπορ","ευπορ"]):
        updates["client_segment"]="affluent_hnwi"

    # Budget.
    budget_patterns=[
        r"(?:budget|spend|up to|max(?:imum)?|μέχρι|μεχρι)\s*(?:is|of|around|about)?\s*[€$£]?\s*([\d,.]+)",
        r"[€]\s*([\d,.]+)\s*(?:budget|per year|annually|ετησίως|ετησιως)?",
    ]
    for pat in budget_patterns:
        m=re.search(pat,lower)
        if m:
            try:
                value=float(m.group(1).replace(",",""))
                if value>=100:
                    updates["budget_annual"]=value
                    break
            except Exception:
                pass

    m=re.search(r"(?:deductible|excess|απαλλαγ)\D{0,15}([\d,.]+)",lower)
    if m:
        try:
            updates["deductible"]=float(m.group(1).replace(",",""))
        except Exception:
            pass

    return updates


def _complete_for_quote(state: dict) -> bool:
    return all(k in state and state[k] not in (None,"") for k in ("age","residence_country","coverage_area"))


def _fallback_reply(state: dict, greek: bool=False) -> str:
    if "age" not in state:
        return "Πόσων ετών είναι το άτομο που θα ασφαλιστεί;" if greek else "How old is the person to be insured?"
    if "residence_country" not in state:
        return "Σε ποια χώρα κατοικεί μόνιμα ο ασφαλισμένος;" if greek else "Which country does the applicant normally reside in?"
    if "coverage_area" not in state:
        return ("Ποια γεωγραφική περιοχή κάλυψης θέλετε: Ευρώπη, παγκόσμια χωρίς ΗΠΑ ή παγκόσμια με ΗΠΑ;"
                if greek else
                "Which area of cover do you need: Europe, worldwide excluding USA, or worldwide including USA?")
    return ("Έχω αρκετά στοιχεία για μια ενδεικτική προσφορά. Μπορείτε επίσης να μου πείτε το budget και ποιες παροχές είναι σημαντικότερες."
            if greek else
            "I have enough information to calculate an indicative quotation. You can also tell me your budget and the benefits that matter most.")


def _quote_payload(state: dict) -> list[dict]:
    if not _complete_for_quote(state):
        return []
    try:
        applicant=Applicant(**state)
        return [q.model_dump() for q in quote_current(applicant)[:8]]
    except Exception:
        return []


def _provider_direct_answer(greek: bool) -> tuple[str,list[str]]:
    p=provider_definition("morgan_price")
    source=next((s["url"] for s in p["sources"] if s["kind"]=="about"),"https://morgan-price.eu/about-us/")
    facts=p.get("seed_facts",[])
    if greek:
        reply=(
            "Η Morgan Price δραστηριοποιείται στη διεθνή ιδιωτική ασφάλιση υγείας. "
            "Η Morgan Price (Europe) ApS δημιουργήθηκε το 2020 για την εξυπηρέτηση συνεργατών και ασφαλισμένων στην ΕΕ "
            "και περιγράφεται από την ίδια ως MGA/MGU και όχι ως ασφαλιστική εταιρεία. "
            "Σύμφωνα με την επίσημη σελίδα της, εποπτεύεται στη Δανία από τη Danish Financial Supervisory Authority "
            "(DFSA), FTID 36351. Για τον HAL, αυτά είναι στοιχεία του provider· οι παροχές και τα ασφάλιστρα "
            "ελέγχονται ξεχωριστά από τα επίσημα rate tables και policy documents."
        )
    else:
        reply=(
            "Morgan Price operates in the international private medical insurance market. "
            "Morgan Price (Europe) ApS was formed in 2020 to support EU partners and members, and describes itself "
            "as an MGA/MGU rather than an insurer. Its official information states that it is regulated in Denmark "
            "by the Danish Financial Supervisory Authority (DFSA), FTID 36351. In HAL, these provider facts are kept "
            "separate from plan benefits and premiums, which are verified from official policy documents and rate tables."
        )
    return reply,[source]


def _greece_direct_answer(greek: bool) -> tuple[str,list[str]]:
    data=destination("GR")
    facts={f["id"]:f for f in data["facts"]}
    srcs=[]
    for key in ["core_coverage","satisfaction","unmet_needs_oecd","oop","waiting_trend"]:
        u=facts.get(key,{}).get("source_url")
        if u and u not in srcs:
            srcs.append(u)
    if greek:
        reply=(
            "Η Ελλάδα έχει καθολική κάλυψη για βασικές υπηρεσίες υγείας, επομένως το δημόσιο σύστημα παραμένει σημαντικός πυλώνας "
            "και δεν είναι σωστό να παρουσιάζεται ως «ανεπαρκές» συνολικά. Παράλληλα όμως, τα επίσημα στοιχεία δείχνουν ουσιαστικές "
            "πιέσεις πρόσβασης και χρηματοδότησης: το OECD αναφέρει 27% ικανοποίηση από τη διαθεσιμότητα ποιοτικής περίθαλψης έναντι "
            "64% μέσου όρου OECD, ενώ το comparable unmet-needs indicator ήταν 12,1% έναντι 3,4%. Το Country Health Profile 2025 "
            "αναφέρει επίσης ότι οι out-of-pocket πληρωμές αντιστοιχούσαν περίπου στο 34% της τρέχουσας δαπάνης υγείας το 2023.\n\n"
            "Αυτό δεν σημαίνει ότι το 34% αφορά απορριφθείσες ασφαλιστικές απαιτήσεις ή ανασφάλιστους. Είναι συνολικές άμεσες πληρωμές "
            "των νοικοκυριών, όπως συμμετοχές, φάρμακα, ιδιωτικές υπηρεσίες, dental και άλλες μη πλήρως χρηματοδοτούμενες δαπάνες.\n\n"
            "Για έναν affluent/HNWI κάτοικο Ελλάδας, το επιχείρημα υπέρ IPMI είναι κυρίως η μεγαλύτερη επιλογή ιδιωτικών παρόχων, "
            "η δυνατότητα θεραπείας εκτός Ελλάδας όπου το επιτρέπει το συμβόλαιο, υψηλότερα όρια, continuity/portability και διεθνής "
            "διαχείριση — όχι απλώς η αντικατάσταση του δημόσιου συστήματος."
        )
    else:
        reply=(
            "Greece provides universal coverage for a core set of health services, so the public system remains an important part of "
            "healthcare access and should not be portrayed as simply inadequate. At the same time, official data show meaningful access "
            "and financing pressures: the OECD reports 27% satisfaction with the availability of quality healthcare versus a 64% OECD "
            "average, and a comparable unmet-needs indicator of 12.1% versus 3.4%. The 2025 Country Health Profile also reports that "
            "out-of-pocket payments were about 34% of current health expenditure in 2023.\n\n"
            "That 34% does not mean that local insurers rejected those expenses or that the people paying were uninsured. It is aggregate "
            "direct household health spending, including co-payments, medicines, private services, dental care and other costs not fully "
            "financed by a third party.\n\n"
            "For an affluent/HNWI resident of Greece, the IPMI case is therefore mainly about broader private-provider choice, eligible "
            "treatment abroad, high limits, continuity/portability and international service infrastructure—not simply replacing the public system."
        )
    return reply,srcs[:5]


def _education_direct_answer(greek: bool) -> tuple[str,list[str]]:
    data=ipmi_value_proposition()
    srcs=[s["url"] for s in data.get("sources",[])]

    if greek:
        reply=(
            "Αν ο στόχος είναι πραγματικά comprehensive ιδιωτική προστασία, ένα καλό international health insurance (IPMI) "
            "είναι συνήθως η ανώτερη λύση από ένα τυπικό local πρόγραμμα ως προς το συνολικό εύρος: μεγαλύτερη γεωγραφική κάλυψη, "
            "ευρύτερη επιλογή ιδιωτικών νοσοκομείων και specialists, υψηλότερα ή λιγότερο κατακερματισμένα limits, international direct billing/"
            "assistance, evacuation/repatriation και continuity όταν αλλάζει η χώρα κατοικίας.\n\n"
            "Η διαφορά φαίνεται ιδιαίτερα στα outpatient benefits. Ανάλογα με το plan, comprehensive IPMI μπορεί να καλύπτει specialist visits, "
            "diagnostics όπως MRI/CT/PET, prescribed medicines, physiotherapy, mental-health treatment και complementary therapies. Στα υψηλότερα "
            "tiers μπορεί να προσθέτει dental, optical, wellness και maternity. Αυτό είναι ιδιαίτερα σημαντικό σε χώρες με waiting-list pressure, "
            "unmet needs ή υψηλές out-of-pocket πληρωμές: ο πελάτης αγοράζει μια εναλλακτική οδό πρόσβασης σε ιδιωτική περίθαλψη.\n\n"
            "Στο inpatient πρέπει επίσης να ελέγχουμε πώς πληρώνονται surgeon/anaesthetist/consultant fees. Ορισμένα domestic contracts χρησιμοποιούν "
            "fee schedules ή sublimits και ο ασφαλισμένος μπορεί να μείνει με σημαντική διαφορά αν ο ιατρός της επιλογής του χρεώνει πάνω από το plafond. "
            "Ένα ισχυρό IPMI μπορεί να χρησιμοποιεί Full refund ή reasonable-and-customary basis, πάντοτε σύμφωνα με annual maximum και wording.\n\n"
            "Στο verified Morgan Price Evolution EU 2026, οι hospital αμοιβές surgeons, anaesthetists, consultants και physicians αναγράφονται Full refund "
            "σε όλα τα plans. MRI/CT/PET είναι Full refund από Standard Plus και πάνω, ενώ υπάρχουν verified benefits για physiotherapy, complementary "
            "therapies, outpatient psychiatry, dental, maternity, rehabilitation και evacuation ανάλογα με το tier και τους όρους.\n\n"
            "Ο HAL θα παρουσιάζει λοιπόν το IPMI ως premium/comprehensive επιλογή όταν ο πελάτης ζητά breadth, freedom of choice, high limits και "
            "international flexibility. Δεν θα υπόσχεται benefit που δεν υπάρχει στο συγκεκριμένο wording. Ειδικά vitamins/supplements δεν θα "
            "θεωρούνται αυτόματα covered· prescribed medicines μόνο όταν το plan το επιβεβαιώνει."
        )
    else:
        reply=(
            "If the goal is genuinely comprehensive private protection, a well-designed international private medical insurance (IPMI) plan is usually "
            "the stronger solution than a typical local plan in overall breadth: wider geography, broader private-hospital and specialist choice, higher "
            "or less fragmented limits, international direct billing/assistance, evacuation/repatriation and continuity when residence changes.\n\n"
            "The difference is especially important in outpatient care. Depending on the plan, comprehensive IPMI can cover specialist visits, diagnostics "
            "such as MRI/CT/PET, prescribed medicines, physiotherapy, mental-health treatment and complementary therapies; higher tiers may add dental, "
            "optical, wellness and maternity. Where waiting lists, unmet needs or household direct spending are material, that creates an alternative route "
            "to private care.\n\n"
            "Inpatient design matters too: some domestic contracts use physician fee schedules or sublimits, which can leave a balance when the chosen "
            "surgeon charges above the policy ceiling. Strong IPMI can use Full refund or reasonable-and-customary structures, subject to the annual maximum "
            "and policy wording.\n\n"
            "In the verified Morgan Price Evolution EU 2026 Table of Benefits, hospital surgeon/anaesthetist/consultant/physician fees are shown as Full refund "
            "across all plans; MRI/CT/PET is Full refund from Standard Plus upward, with verified tiered benefits for physiotherapy, complementary therapies, "
            "outpatient psychiatry, dental, maternity, rehabilitation and evacuation.\n\n"
            "HAL should therefore position IPMI as the premium/comprehensive choice for breadth, provider freedom, high limits and international flexibility, "
            "while proving the recommendation from the actual policy."
        )
    return reply,srcs[:5]

def _hnwi_direct_answer(greek: bool) -> tuple[str,list[str]]:
    data=ipmi_value_proposition()
    srcs=[s["url"] for s in data.get("sources",[])][:5]
    if greek:
        reply=(
            "Για έναν affluent local/HNWI που ζητά comprehensive protection, ο HAL θα παρουσιάζει το IPMI ως την premium επιλογή: "
            "broader private-hospital/specialist choice, outpatient diagnostics και treatment, high limits, eligible treatment abroad, "
            "continuity/portability, direct billing, evacuation/repatriation και international case management.\n\n"
            "Το outpatient είναι βασικός differentiator: specialist visits, diagnostics, prescribed medication, physiotherapy, mental health και — όταν "
            "το policy το επιβεβαιώνει — acupuncture/chiropractic/osteopathy/Ayurveda ή άλλα complementary treatments, dental, optical, wellness και maternity.\n\n"
            "Στο inpatient ο HAL θα ελέγχει physician/surgeon fee limits. Ένα local plan με fixed plafond μπορεί να αφήσει τον πελάτη να πληρώνει τη διαφορά "
            "ακόμη και όταν η νοσηλεία είναι insured. Στο Morgan Price Evolution EU 2026, το verified TOB αναγράφει Full refund για surgeon, anaesthetist, "
            "consultant και physician fees σε όλα τα plans, subject to annual maximum/policy terms."
        )
    else:
        reply=(
            "For an affluent local/HNWI seeking comprehensive protection, HAL will position IPMI as the premium solution: broader private-hospital/specialist "
            "choice, outpatient diagnostics and treatment, high limits, eligible treatment abroad, continuity/portability, direct billing, evacuation/"
            "repatriation and international case management.\n\n"
            "Outpatient breadth is a major differentiator: specialist visits, diagnostics, prescribed medication, physiotherapy, mental health and—where "
            "verified—complementary therapies, dental, optical, wellness and maternity.\n\n"
            "For inpatient care HAL will check physician/surgeon fee limits. A local policy with a fixed ceiling can leave the client paying the balance even "
            "when the admission is insured. In the verified Morgan Price Evolution EU 2026 TOB, surgeon, anaesthetist, consultant and physician fees are shown "
            "as Full refund across all plans, subject to policy terms and annual maximum."
        )
    return reply,srcs

def _local_review_direct_answer(greek: bool) -> tuple[str,list[str]]:
    data=ipmi_value_proposition()
    sources=[s["url"] for s in data.get("sources",[])][:4]
    if greek:
        reply=(
            "Βεβαίως. Ένα local private health plan μπορεί να είναι η πιο cost-effective λύση αν θέλετε κυρίως κάλυψη μέσα στην Ελλάδα, "
            "δεν σας ενδιαφέρει treatment abroad/portability και το βασικό σας κριτήριο είναι το χαμηλότερο premium. "
            "Δεν θα προσποιηθώ όμως ότι έχω local quotation αν δεν έχει φορτωθεί verified local rate table.\n\n"
            "Αν αντίθετα θέλετε μεγάλα outpatient limits, broad private-provider choice, treatment abroad, international continuity, mental-health/"
            "rehabilitation/evacuation ή γενικά comprehensive protection, τότε αξίζει να συγκρίνουμε σοβαρά IPMI, γιατί συνήθως προσφέρει πολύ "
            "ευρύτερο συνδυασμό παροχών και γεωγραφικής ευελιξίας.\n\n"
            "Μπορώ να καταγράψω τις ανάγκες σας και να στείλω το enquiry στην Ashlar για broker review local-vs-international."
        )
    else:
        reply=(
            "Certainly. A local private health plan can be the most cost-effective solution if you mainly need domestic cover, do not need treatment "
            "abroad or portability, and lowest premium is the main priority. HAL will not fabricate a local quotation if no verified local rate table "
            "has been loaded.\n\n"
            "If you instead want high outpatient limits, broad private-provider choice, treatment abroad, international continuity, mental-health/"
            "rehabilitation/evacuation or genuinely comprehensive protection, IPMI deserves serious consideration because it usually combines a much "
            "broader set of benefits and geographic flexibility.\n\n"
            "I can capture your requirements and send them to Ashlar for a broker local-vs-international review."
        )
    return reply,sources


def _travel_direct_answer(greek: bool) -> tuple[str,list[str]]:
    data=international_vs_local()
    sources=[]
    for p in data.get("principles",[]):
        for s in p.get("sources",[]):
            if s["url"] not in sources:
                sources.append(s["url"])
    if greek:
        reply=(
            "Αν το ζητούμενο είναι ένα προσωρινό ταξίδι και όχι μακροχρόνια διαμονή, πιθανότατα μιλάμε για Travel Insurance και όχι IPMI. "
            "Το travel plan είναι σχεδιασμένο κυρίως για απρόβλεπτα περιστατικά κατά τη διάρκεια του ταξιδιού, ενώ το IPMI αφορά συνεχή "
            "ιατρική κάλυψη για κάποιον που ζει ή κινείται διεθνώς.\n\n"
            "Μπορώ να στείλω travel enquiry στην Ashlar. Στη φόρμα θα χρειαστώ προορισμό, ημερομηνίες και βασικά στοιχεία των ταξιδιωτών."
        )
    else:
        reply=(
            "If the need is a temporary trip rather than long-term residence, you are probably looking for Travel Insurance rather than IPMI. "
            "Travel cover is mainly designed for unforeseen events during a trip, while IPMI is ongoing medical protection for people living or moving internationally.\n\n"
            "I can send a travel enquiry to Ashlar. The form will capture destination, travel dates and basic traveller details."
        )
    return reply,sources[:4]


def _intent_flags(message: str, state: dict) -> dict:
    lower=(message or "").lower()
    return {
        "provider": any(x in lower for x in ["morgan price","morgan","provider","company","insurer","εταιρ","πάροχ","ασφαλιστ"]),
        "education": any(x in lower for x in ["international vs local","international or local","why international","local insurance",
            "travel insurance","ipmi","international health","global health","διεθν","τοπικ","γιατί international","γιατι international","ταξιδιωτικ"]),
        "destination": any(x in lower for x in ["public hospital","public healthcare","health system","healthcare system","hospital system",
            "δημόσιο νοσοκομ","δημοσιο νοσοκομ","σύστημα υγείας","συστημα υγειας","ελλάδα","ελλαδα","greece"]),
        "hnwi": any(x in lower for x in ["hnwi","high net worth","high-net-worth","affluent","wealthy","premium client",
            "executive","business owner","entrepreneur","family office","comprehensive cover","best coverage","maximum coverage",
            "top hospitals","private hospitals","ευκατάστα","ευκαταστα","εύπορ","ευπορ","πλούσι","πλουσι","επιχειρηματ",
            "πλήρη κάλυψη","πληρη καλυψη","comprehensive"]),
    }


async def chat_turn(message: str, state: dict, history: list[dict] | None = None) -> dict:
    settings=get_settings()
    greek=_is_greek(message)
    state=_merge_state(state, _deterministic_updates(message,state,history))
    journey=classify_journey(message,state)
    state["journey"]=journey
    flags=_intent_flags(message,state)

    # Journey routing: travel / local review / IPMI.
    if journey=="travel":
        reply,sources=_travel_direct_answer(greek)
        return {
            "reply":reply,"state":state,"quotes":[],"ai_status":"journey_router",
            "provider_sources_used":[],"knowledge_sources_used":sources,
            "journey":journey,"lead_cta":journey_cta(journey,True),
            "open_application_form":lead_intent(message),
        }

    if journey=="local_review":
        reply,sources=_local_review_direct_answer(greek)
        return {
            "reply":reply,"state":state,"quotes":[],"ai_status":"journey_router",
            "provider_sources_used":[],"knowledge_sources_used":sources,
            "journey":journey,"lead_cta":journey_cta(journey,True),
            "open_application_form":lead_intent(message),
        }

    # High-confidence knowledge intents are answered directly from curated data.
    # This prevents an LLM formatting failure from hiding data that HAL already has.
    if flags["destination"] and any(x in message.lower() for x in ["greece","ελλάδα","ελλαδα","healthcare system","σύστημα υγείας","συστημα υγειας"]):
        reply,sources=_greece_direct_answer(greek)
        return {"reply":reply,"state":state,"quotes":_quote_payload(state),"ai_status":"curated_knowledge",
                "provider_sources_used":[],"knowledge_sources_used":sources,
                "journey":journey,"lead_cta":journey_cta(journey,True),"open_application_form":lead_intent(message)}
    if flags["provider"] and "morgan" in message.lower():
        reply,sources=_provider_direct_answer(greek)
        return {"reply":reply,"state":state,"quotes":_quote_payload(state),"ai_status":"curated_knowledge",
                "provider_sources_used":sources,"knowledge_sources_used":[],
                "journey":journey,"lead_cta":journey_cta(journey,True),"open_application_form":lead_intent(message)}
    if flags["hnwi"] and any(x in message.lower() for x in ["hnwi","affluent","high net worth","high-net-worth","ευκατάστα","ευκαταστα","comprehensive"]):
        reply,sources=_hnwi_direct_answer(greek)
        return {"reply":reply,"state":state,"quotes":_quote_payload(state),"ai_status":"curated_knowledge",
                "provider_sources_used":[],"knowledge_sources_used":sources,
                "journey":journey,"lead_cta":journey_cta(journey,True),"open_application_form":lead_intent(message)}
    if flags["education"] and any(x in message.lower() for x in ["why international","international vs local","international or local","γιατί international","γιατι international"]):
        reply,sources=_education_direct_answer(greek)
        return {"reply":reply,"state":state,"quotes":_quote_payload(state),"ai_status":"curated_knowledge",
                "provider_sources_used":[],"knowledge_sources_used":sources,
                "journey":journey,"lead_cta":journey_cta(journey,True),"open_application_form":lead_intent(message)}

    provider_text=""
    if flags["provider"]:
        try:
            provider_text=await provider_context("morgan_price", {"about","individual","group","downloads"}, char_limit=10000)
        except Exception:
            provider_text=""

    edu_text=education_context() if flags["education"] else ""
    ipmi_text=ipmi_value_context() if (flags["education"] or flags["hnwi"] or flags["destination"]) else ""
    hnwi_text=hnwi_context() if flags["hnwi"] else ""

    destination_code=None
    candidate=(state or {}).get("residence_country","")
    if any(x in message.lower() for x in ["greece","ελλάδα","ελλαδα","hellas"]) or str(candidate).lower() in {"greece","gr","hellas","ελλάδα","ελλαδα"}:
        destination_code="GR"
    dest_text=destination_context(destination_code) if flags["destination"] and destination_code else ""

    # Even without an LLM, deterministic intake keeps moving.
    if not settings.anthropic_api_key:
        return {
            "reply":_fallback_reply(state,greek),
            "state":state,
            "quotes":_quote_payload(state),
            "ai_status":"deterministic_fallback",
            "provider_sources_used":[],
            "knowledge_sources_used":[],
            "journey":journey,
            "lead_cta":journey_cta(journey, journey!="undetermined"),
            "open_application_form":lead_intent(message),
        }

    system=f"""
You are HAL, Ashlar Assurance's international health insurance assistant.

IMPORTANT OUTPUT RULE:
Return one valid JSON object only. Never answer with "..." or an empty reply.
If you cannot complete an explanation, ask one useful question instead.

Responsibilities:
1. Converse naturally in the user's language.
2. Extract applicant facts into applicant_updates.
3. Never calculate or invent premiums; HAL's deterministic engine calculates them.
4. Never invent policy benefits, exclusions, waiting periods, underwriting outcomes, regulators or provider facts.
5. Provider facts may be used only from OFFICIAL PROVIDER CONTEXT.
6. Product benefits are verified by a separate evidence engine.
7. Never claim acceptance. Final eligibility and underwriting remain with the insurer.
8. International vs local comparisons must be balanced and evidence-led, not fear-based.
9. Distinguish public healthcare, local private insurance, IPMI and travel insurance.
10. An affluent local national/HNWI may legitimately seek IPMI for provider choice, high limits, treatment abroad, portability, direct billing or comprehensive service.
11. Out-of-pocket spending is aggregate household direct spending; never present it as proof of insurance denials or uninsured status.
12. SALES POSITIONING: For international-vs-local or comprehensive/HNWI conversations, lead with why a strong IPMI is generally the premium solution for breadth, provider choice, high limits, international geography, service and continuity.
13. OUTPATIENT PRIORITY: Give significant weight to specialist consultations, diagnostics, prescribed medicines, physiotherapy, mental health and verified complementary therapies. Explain how these benefits can reduce reliance on public/local access bottlenecks.
14. Translate problem -> solution: waiting lists -> alternative private outpatient/diagnostic route; high OOP -> greater financial predictability; domestic geography -> international provider network; relocation -> portability; local physician fee ceiling -> stronger verified fee reimbursement.
15. Discuss dental, optical, wellness, maternity, rehabilitation and evacuation/repatriation when verified.
16. Explain physician fee schedules/sublimits as a potential domestic-plan risk, but never state that every local policy has them.
17. Never claim vitamins/supplements are covered unless the exact wording confirms it.
18. Never interpret Full refund as unlimited; annual maximum, pre-authorisation, network and other policy terms may apply.
19. When Morgan Price is relevant, use the verified 2026 Evolution examples from COMPREHENSIVE IPMI VALUE CONTEXT.
20. JOURNEY ROUTING: determine whether the applicant actually needs Travel Insurance, a local-vs-international broker review, or IPMI. Never force a short-trip traveller into IPMI.
21. LOCAL REQUESTS: do not lose a prospect merely because they ask for local insurance. Explain when local cover can be more cost-effective, discover the underlying need, and show where IPMI provides materially broader value. If HAL has no verified local rates, never fabricate a local premium.
22. LEAD CONVERSION: when the applicant asks to proceed, request a quote, be contacted, or send a proposal, tell them you can open the secure enquiry form. Do not ask for detailed medical history in the chat form.

Coverage-area codes:
area1=Europe
area2=Worldwide excluding USA, Singapore, Hong Kong and China
area3=Worldwide excluding USA
area4=Worldwide including USA

Applicant update fields:
age, residence_country, nationality, coverage_area, currency, deductible, budget_annual,
outpatient_required, maternity_required, dental_required, mental_health_required,
wellness_required, optical_required, evacuation_required, chronic_required,
client_segment, private_hospital_choice_required, cross_border_treatment_required,
home_country_treatment_required, continuity_portability_required, high_annual_limit_required,
private_room_required, direct_billing_required, second_medical_opinion_required.

Current applicant state:
{json.dumps(state,ensure_ascii=False)}

OFFICIAL PROVIDER CONTEXT:
{provider_text}

INTERNATIONAL VS LOCAL EDUCATION:
{edu_text}

COMPREHENSIVE IPMI VALUE CONTEXT:
{ipmi_text}

DESTINATION HEALTHCARE INTELLIGENCE:
{dest_text}

AFFLUENT / HNWI CONTEXT:
{hnwi_text}

Return exactly:
{{
  "reply":"useful natural-language answer or next question",
  "applicant_updates":{{}},
  "provider_sources_used":[],
  "knowledge_sources_used":[]
}}
"""
    messages=[]
    for item in (history or [])[-8:]:
        role=item.get("role")
        content=item.get("content")
        if role in {"user","assistant"} and content and content.strip() not in {"...","…"}:
            messages.append({"role":role,"content":str(content)[:4000]})
    messages.append({"role":"user","content":message[:8000]})

    parsed={}
    llm_error=None
    try:
        async with httpx.AsyncClient(timeout=60) as client:
            response=await client.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key":settings.anthropic_api_key,
                    "anthropic-version":"2023-06-01",
                    "content-type":"application/json",
                },
                json={
                    "model":settings.anthropic_model,
                    "max_tokens":1100,
                    "temperature":0.1,
                    "system":system,
                    "messages":messages,
                },
            )
            response.raise_for_status()
            payload=response.json()
        text="".join(block.get("text","") for block in payload.get("content",[]) if block.get("type")=="text").strip()
        parsed=_extract_json(text)
    except Exception as exc:
        llm_error=str(exc)[:160]
        parsed={}

    state=_merge_state(state, parsed.get("applicant_updates",{}))
    reply=str(parsed.get("reply","") or "").strip()

    # Never surface a meaningless ellipsis or parser failure to the client.
    if reply in {"","...","…",".."}:
        reply=_fallback_reply(state,greek)
        ai_status="deterministic_fallback"
    else:
        ai_status="active" if not llm_error else "degraded_fallback"

    return {
        "reply":reply,
        "state":state,
        "quotes":_quote_payload(state),
        "ai_status":ai_status,
        "provider_sources_used":[str(x) for x in parsed.get("provider_sources_used",[]) if isinstance(x,str)][:8],
        "knowledge_sources_used":[str(x) for x in parsed.get("knowledge_sources_used",[]) if isinstance(x,str)][:10],
        "journey":journey,
        "lead_cta":journey_cta(journey, journey!="undetermined"),
        "open_application_form":lead_intent(message),
    }
