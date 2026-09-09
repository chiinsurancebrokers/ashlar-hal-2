from __future__ import annotations

import re
from typing import Any

from backend.app.travel.europesure import destination_scope


TRAVEL_KEYS={
    "travel_trip_type","travel_destination","travel_destination_scope","travel_age",
    "travel_cover_preference","travel_tier_preference","travel_travellers",
    "travel_duration_days","travel_winter_sports","travel_business_cover",
    "travel_gadget_cover","travel_covid_extension","travel_car_hire_excess",
    "travel_pending_question","travel_discovery_complete","travel_long_term_warning_shown",
}


def _is_greek(text: str) -> bool:
    return bool(re.search(r"[\u0370-\u03ff]", text or ""))


def _clean_text(value: str, limit: int=120) -> str:
    return re.sub(r"\s+"," ",str(value or "")).strip()[:limit]


def _yes(text: str) -> bool:
    return _clean_text(text).lower() in {"yes","y","ναι","sure","include","required"}


def _no(text: str) -> bool:
    return _clean_text(text).lower() in {"no","n","όχι","οχι","not needed","none"}


def deterministic_travel_updates(message: str, state: dict | None=None) -> dict[str, Any]:
    state=state or {}
    text=_clean_text(message,500)
    low=text.lower()
    out:dict[str,Any]={}

    if any(x in low for x in ("annual multi-trip","annual multi trip","annual travel","multiple trips","multi trip","ετήσια","ετησια","πολλαπλά ταξίδια","πολλαπλα ταξιδια")):
        out["travel_trip_type"]="annual"
    elif any(x in low for x in ("single trip","one trip","one-off trip","single-trip","ένα ταξίδι","ενα ταξιδι","μεμονωμένο ταξίδι","μεμονωμενο ταξιδι")):
        out["travel_trip_type"]="single"

    tier_hits={"silver":"silver","gold":"gold","platinum":"platinum"}
    for word,tier in tier_hits.items():
        if re.search(rf"\b{word}\b",low):
            out["travel_tier_preference"]=tier
            break

    if any(x in low for x in ("budget","basic","cheap","economy","lowest price","οικονομ","φθην","βασικ")):
        out["travel_cover_preference"]="budget"
    elif any(x in low for x in ("maximum","highest","strongest","premium","best cover","max cover","ανώτα","ανωτα","ισχυρότερ","ισχυροτερ","πλήρη","πληρη")):
        out["travel_cover_preference"]="highest"
    elif any(x in low for x in ("balanced","balance","value","most popular","ισορροπ","καλή σχέση","καλη σχεση")):
        out["travel_cover_preference"]="balanced"

    age_patterns=[
        r"\b(?:i am|i'm|aged|age is|είμαι|ειμαι)\s*(\d{1,3})\b",
        r"\b(?:oldest(?: traveller)?(?: is)?|ηλικία|ηλικια)\D{0,10}(\d{1,3})\b",
    ]
    for pat in age_patterns:
        m=re.search(pat,low)
        if m and 0<=int(m.group(1))<=120:
            out["travel_age"]=int(m.group(1))
            out["age"]=int(m.group(1))
            break

    m=re.search(r"\b(\d{1,3})\s*(?:days?|ημέρ|ημερ)",low)
    if m:
        out["travel_duration_days"]=int(m.group(1))
    else:
        m=re.search(r"\b(\d{1,2})\s*(?:weeks?|εβδομάδ|εβδομαδ)",low)
        if m:
            out["travel_duration_days"]=int(m.group(1))*7
        else:
            m=re.search(r"\b(\d{1,2})\s*(?:months?|μήν|μην)",low)
            if m:
                out["travel_duration_days"]=int(m.group(1))*30

    traveller_patterns=[
        r"\b(?:family of|party of|we are|for)\s+(\d{1,2})\b",
        r"\b(\d{1,2})\s+(?:travellers?|travelers?|people|persons|άτομα|ατομα)\b",
    ]
    for pat in traveller_patterns:
        m=re.search(pat,low)
        if m and 1<=int(m.group(1))<=30:
            out["travel_travellers"]=int(m.group(1))
            break

    addon_map={
        "travel_winter_sports":("winter sports","ski","skiing","snowboard","χειμερινά σπορ","χειμερινα σπορ","σκι"),
        "travel_business_cover":("business cover","business trip","work trip","επαγγελματικό ταξίδι","επαγγελματικο ταξιδι"),
        "travel_gadget_cover":("gadget","laptop","phone cover","κινητό","κινητο","λάπτοπ","λαπτοπ"),
        "travel_covid_extension":("covid","coronavirus","κορονο","covid-19"),
        "travel_car_hire_excess":("car hire","rental car","car rental","ενοικιαζόμενο αυτοκίνητο","ενοικιαζομενο αυτοκινητο"),
    }
    for key,words in addon_map.items():
        if any(w in low for w in words):
            out[key]=True

    # Destination extraction from high-confidence phrases.
    dest_patterns=[
        r"\b(?:going|travelling|traveling|flying|trip|holiday|vacation)\s+(?:to|in)\s+([A-Za-zÀ-ÖØ-öø-ÿΑ-Ωα-ωΆ-ώ .'-]{2,70})",
        r"\b(?:destination is|destination:)\s*([A-Za-zÀ-ÖØ-öø-ÿΑ-Ωα-ωΆ-ώ .'-]{2,70})",
        r"\b(?:πάω|παω|ταξιδεύω|ταξιδευω|ταξίδι|ταξιδι)\s+(?:στη|στην|στο|σε)\s+([A-Za-zÀ-ÖØ-öø-ÿΑ-Ωα-ωΆ-ώ .'-]{2,70})",
    ]
    for pat in dest_patterns:
        m=re.search(pat,text,flags=re.I)
        if m:
            dest=_clean_text(m.group(1)).rstrip(".,!?")
            # Trim common continuation words.
            dest=re.split(r"\b(?:for|with|and i|and we|για|με)\b",dest,maxsplit=1,flags=re.I)[0].strip()
            if dest:
                out["travel_destination"]=dest
                out["travel_destination_scope"]=destination_scope(dest)
                break

    pending=state.get("travel_pending_question")
    if pending=="travel_trip_type" and "travel_trip_type" not in out:
        if low in {"single","single trip","one trip","ενιαίο","ενιαιο","ένα ταξίδι","ενα ταξιδι"}:
            out["travel_trip_type"]="single"
        elif low in {"annual","annual multi-trip","annual multi trip","ετήσια","ετησια"}:
            out["travel_trip_type"]="annual"

    if pending=="travel_destination" and "travel_destination" not in out and len(text)>=2:
        out["travel_destination"]=text
        out["travel_destination_scope"]=destination_scope(text)

    if pending=="travel_age" and "travel_age" not in out:
        m=re.fullmatch(r"\s*(\d{1,3})\s*",low)
        if m and 0<=int(m.group(1))<=120:
            out["travel_age"]=int(m.group(1))
            out["age"]=int(m.group(1))

    if pending=="travel_cover_preference" and "travel_cover_preference" not in out:
        if any(x in low for x in ("budget","basic","price","οικονομ")):
            out["travel_cover_preference"]="budget"
        elif any(x in low for x in ("highest","maximum","premium","strongest","πλήρ","ισχυρ","μέγισ","μεγισ")):
            out["travel_cover_preference"]="highest"
        elif any(x in low for x in ("balanced","balance","value","ισορροπ")):
            out["travel_cover_preference"]="balanced"

    return out


def apply_travel_updates(state: dict, updates: dict) -> dict:
    merged=dict(state or {})
    for key,value in (updates or {}).items():
        if key in TRAVEL_KEYS or key=="age":
            merged[key]=value
    merged["journey"]="travel"
    return merged


def long_term_mismatch(message: str, state: dict) -> bool:
    low=(message or "").lower()
    relocation_terms=(
        "moving abroad","relocating","relocation","move to live","live abroad","working abroad",
        "work abroad for a year","expat","long-term residence","long term residence",
        "μετακομίζ","μετακομιζ","μόνιμα","μονιμα","ζήσω στο εξωτερικό","ζησω στο εξωτερικο",
        "εργαστώ στο εξωτερικό","εργαστω στο εξωτερικο",
    )
    if any(x in low for x in relocation_terms):
        return True
    try:
        return int(state.get("travel_duration_days") or 0)>180
    except Exception:
        return False


def next_travel_question(state: dict, greek: bool=False) -> dict[str,Any] | None:
    if not state.get("travel_trip_type"):
        return {
            "key":"travel_trip_type",
            "reply":"Θέλετε κάλυψη για ένα μόνο ταξίδι ή ετήσια κάλυψη για πολλαπλά ταξίδια;" if greek else "Do you need cover for one trip or annual multi-trip cover?",
            "quick_replies":[
                {"label":"Single trip" if not greek else "Ένα ταξίδι","value":"single trip"},
                {"label":"Annual multi-trip" if not greek else "Ετήσια πολλαπλά ταξίδια","value":"annual multi-trip"},
            ],
        }
    if not state.get("travel_destination"):
        return {
            "key":"travel_destination",
            "reply":"Ποιος είναι ο προορισμός σας;" if greek else "Where are you travelling to?",
            "quick_replies":[],
        }
    if state.get("travel_age") is None:
        return {
            "key":"travel_age",
            "reply":"Ποια είναι η ηλικία του μεγαλύτερου ταξιδιώτη;" if greek else "How old is the oldest traveller?",
            "quick_replies":[],
        }
    if not state.get("travel_cover_preference") and not state.get("travel_tier_preference"):
        return {
            "key":"travel_cover_preference",
            "reply":"Προτιμάτε οικονομική κάλυψη, ισορροπία κάλυψης/κόστους ή τα υψηλότερα όρια;" if greek else "Would you prefer a budget option, a balanced level of cover, or the highest limits?",
            "quick_replies":[
                {"label":"Budget" if not greek else "Οικονομική","value":"budget"},
                {"label":"Balanced" if not greek else "Ισορροπημένη","value":"balanced"},
                {"label":"Highest limits" if not greek else "Υψηλότερα όρια","value":"highest"},
            ],
        }
    return None


def travel_progress(state: dict) -> dict[str,Any]:
    keys=("travel_trip_type","travel_destination","travel_age")
    core=sum(1 for k in keys if state.get(k) not in (None,""))
    preference=1 if state.get("travel_cover_preference") or state.get("travel_tier_preference") else 0
    total=4
    done=core+preference
    return {
        "completed":done,
        "total":total,
        "percent":round(done/total*100),
        "complete":done>=total,
    }
