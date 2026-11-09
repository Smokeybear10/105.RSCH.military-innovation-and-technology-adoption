"""Domain dictionaries for BOF 1901-1902 text interpretation."""

from __future__ import annotations


ACTION_STATUS_PATTERNS = {
    "Rejected": [
        r"\brejected\b",
        r"\bdisapproved\b",
        r"\bdeclined\b",
        r"\bnot\s+(?:approved|adopted|accepted|authori[sz]ed|allotted|granted|ordered)\b",
        r"\bnot\s+recom{1,2}ended\b",
        r"\bdenied\b",
        r"\bunfavo[u]?rable\b",
    ],
    "Approved": [
        r"\bapproved\b",
        r"\badopted\b",
        r"\bauthori[sz]ed\b",
        r"\ballotment made\b",
        r"\ballotted\b",
        r"\bgranted\b",
        r"\baccepted\b",
        r"\bcontract awarded\b",
        r"\bordered\b",
        r"\brecommended for adoption\b",
        r"\bappropriation made\b",
    ],
    "Investigating": [
        r"\bfiled\b",
        r"\baction deferred\b",
        r"\bdeferred\b",
        r"\breferred\b",
        r"\bfor report\b",
        r"\bunder consideration\b",
        r"\bunder\s+(?:review|test|investigation)\b",
        r"\bto be tested\b",
        r"^(?:additional )?allotments?\.?$",
        r"\bpending\b",
        r"\bcontinued\b",
        r"\bpostponed\b",
        r"\bfor trial\b",
        r"\bfor test\b",
        r"\bno final action\b",
    ],
}


TECHNOLOGY_CLUSTER_PATTERNS = {
    "Small Arms": [
        r"\brifles?\b",
        r"\bpistols?\b",
        r"\bmuskets?\b",
        r"\bcarbines?\b",
        r"\bsmall[- ]arms?\b",
        r"\bmachine[- ]guns?\b",
    ],
    "Artillery": [
        r"\bguns?\b",
        r"\bcannons?\b",
        r"\bhowitzers?\b",
        r"\bfield pieces?\b",
        r"\bvickers\b",
        r"\bordnance\b",
        r"\bcarriages?\b",
        r"\b(?:[2-9]|\d{2,})(?:\.\d+)?[- ]inch\s+rifles?\b",
    ],
    "Explosives": [
        r"\bshell\b",
        r"\bpowder\b",
        r"\bexplosive\b",
        r"\bdetonator\b",
        r"\bfuse\b",
        r"\btorpedo\b",
        r"\bmine\b",
        r"\bisham\b",
    ],
    "Armor and Protection": [
        r"\barmor\b",
        r"\barmour\b",
        r"\bshield\b",
        r"\bhelmet\b",
        r"\bprotective\b",
        r"\bfortification plate\b",
    ],
    "Fortification and Engineering": [
        r"\bfort\b",
        r"\bfortification\b",
        r"\bbattery\b",
        r"\bemplacement\b",
        r"\brange finder\b",
        r"\bsearchlight\b",
        r"\bengineering\b",
        r"\bsiege\b",
    ],
    "Communications and Observation": [
        r"\btelegraph\b",
        r"\btelephone\b",
        r"\bsignal\b",
        r"\bobservation\b",
        r"\boptical\b",
        r"\bwireless\b",
    ],
    "Logistics and Support": [
        r"\bwagon\b",
        r"\btransport\b",
        r"\bsupply\b",
        r"\bquartermaster\b",
        r"\bpack\b",
        r"\bmedical\b",
    ],
}


GOVERNMENT_PROPOSER_PATTERNS = [
    r"\bwar department\b",
    r"\bnavy department\b",
    r"\bordnance department\b",
    r"\bchief of ordnance\b",
    r"\b(?:u\.?\s*s\.?|united states)\s*(?:army|navy|marine corps)\b",
    r"\bu\.?\s*s\.?\s*a\.(?:\s|$)",
    r"\bu\.?\s*s\.?\s*n\.(?:\s|$)",
    r"\bsecretary of war\b",
    r"\bboard of ordnance\b",
    r"\barsenals?\b",
    r"\bcommanding officer\b",
    r"\b(?:lieutenant|lieut\.?|lt\.?|colonel|col\.?|major|maj\.?|admiral|brigadier|gen\.)(?=\s|$)",
]


PRIVATE_PROPOSER_PATTERNS = [
    r"\b(?:company|corporation|incorporated|limited)\b",
    r"\b(?:co|corp|inc|ltd)\.(?:\s|$|,)",
    r"\b(?:co|corp|inc|ltd)\s*$",
]


COLUMN_ALIASES = {
    "subject": ["subject", "topic", "title", "matter"],
    "action": ["action", "decision", "board action", "disposition", "status text"],
    "reasoning": [
        "recommendation reasoning",
        "reasoning",
        "recommendation",
        "remarks",
        "notes",
    ],
    "proposer": ["proposer", "submitted by", "originator", "applicant", "proposed by"],
    "year": [
        "year",
        "date",
        "fiscal year",
        "calendar year",
        "bof annual report #",
        "annual report",
        "report #",
    ],
}
