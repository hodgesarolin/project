# OSINT Report: Daniel Hodges (hodgesarolin@gmail.com)

**Generated:** 2026-01-14
**Purpose:** Personal digital footprint assessment for risk evaluation
**Scope:** Deep dive - both accounts confirmed (LinkedIn daniel-hodges-ba988715 + hodgesarolin)

---

## Executive Summary

**Overall Exposure Level: MODERATE-HIGH**

Your digital footprint has significant professional exposure but limited personal exposure. The main risk vectors are:

1. **LinkedIn aggregates substantial professional info** - employer history, education, location, community involvement, recommendations with personality details
2. **LOPSA board meeting minutes** contain your name in governance records
3. **openSUSE wiki page exists** under hodgesarolin username
4. **Wiza/data broker sites** have scraped your LinkedIn data
5. **Voices.com** profile exists under hodgesarolin (voice actor profile)
6. **Printables.com** has your 3D printing activity

However: **Your family (spouse, kids) and current employer (Prenosis) are NOT findable.**

---

## Detailed Findings

### 1. LinkedIn Profile (CONFIRMED: daniel-hodges-ba988715)

**Publicly Visible Information:**

| Field | Value |
|-------|-------|
| Name | Daniel Hodges |
| Title | Senior DevOps/Systems Engineer, Big Data specialization |
| Employer | Chainalysis Inc. (outdated - you're at Prenosis) |
| Education | Riverside Community College (California) |
| Location | Jersey City, NJ |
| Connections | 500+ |

**Community Involvement (exposed via LinkedIn):**
- openSUSE Project ambassador - traveled to conferences representing the project
- **LOPSA board member since December 2018** (LOPSA dissolved December 2025)
- Attended "many Southern California Linux Expositions" (SCALE)
- Active in local Linux User Groups
- Described as "incredibly knowledgeable" and enthusiastic about Linux

**Professional Endorsements (personality exposure):**
- "Daniel Hodge's enthusiasm for all things Linux was both a joy to watch and has created opportunities for him to advance his career"
- "I've worked with him at many Southern California Linux Expositions. He is always incredibly knowledgeable, and I have yet to see him falter in delivering answers to anyone no matter the complexity of the question"
- His "passion for technology would make him impossible to ignore as an asset to any company or project"

**Sources:**
- [LinkedIn Profile](https://www.linkedin.com/in/daniel-hodges-ba988715/)
- [Wiza Scraped Data](https://wiza.co/d/chainalysis/c10f/daniel-hodges)

---

### 2. LOPSA Board Records (CONFIRMED)

**What's Public:**
- Your name appears in LOPSA board meeting minutes from January 21, 2020
- Listed as attendee alongside Drew Adams
- LOPSA was a 501(c)(3) nonprofit - their governance records are public
- LOPSA dissolved December 26, 2025

**Significance:** This creates a paper trail linking your name to:
- Professional association leadership
- System administration community
- Specific dates of involvement

**Source:** [LOPSA Board Meeting Minutes](https://governance.lopsa.org/Board_meeting_Minutes/21_January_2020)

---

### 3. openSUSE Wiki Page (CONFIRMED)

**URL:** `http://en.opensuse.org/User:Hodgesarolin`

**What LinkedIn reveals about this page:**
- You traveled to conferences, trade shows, expos representing openSUSE
- You helped new community members learn openSUSE
- You participated in community meetings
- You went to local Linux User Groups to talk about openSUSE
- You worked booths at Southern California Linux Expositions

**Risk:** This page may contain:
- Your photo
- Your location
- Your contact info
- Your conference attendance history
- Links to your talks/presentations

**Note:** I couldn't fetch this page directly, but its existence is confirmed via LinkedIn content.

---

### 4. Voices.com Profile (NEW FINDING)

**URL:** `https://www.voices.com/profile/hodgesarolin/`

**What's There:** Voice actor profile under hodgesarolin username

**Potential Exposure:**
- Voice samples (your actual voice)
- Bio/about section
- Location
- Languages/accents
- Contact information

**Source:** Found via search - couldn't access full profile

---

### 5. Printables.com Activity (CONFIRMED)

**Profile:** @hodgesarolin_228300

**What's Public:**
- Pet Collar Display Picture Frame (memorial for deceased dog)
- Equipment: Ender 3 Pro 3D printer
- Print settings: 0.2mm layer height, supports from bed only
- Also 4x6 frame variant available

**Personal Detail Exposed:** Created as memorial plaque for deceased pet

**Source:** [Printables Model](https://www.printables.com/model/148776-pet-collar-display-picture-frame)

---

### 6. Data Broker Exposure

**Wiza has:**
- Your name
- Employer (Chainalysis - outdated)
- Location (Jersey City, NJ)
- Industry (Software Development)
- LinkedIn URL

**Note:** Full contact info (email, phone) is behind paywall on these sites.

---

## What Is NOT Publicly Findable

| Information | Searchable? | Notes |
|-------------|------------|-------|
| Spouse (veterinarian) | ❌ No | Not linked to your profiles |
| Children (3 young kids) | ❌ No | Not mentioned anywhere |
| Jersey City Heights (specific neighborhood) | ❌ No | Only "Jersey City" appears |
| hodgesarolin@gmail.com | ❌ No | Not indexed by search engines |
| Prenosis employment | ❌ No | LinkedIn outdated; no Prenosis employee listings |
| Current project details | ❌ No | Not public |
| Home address | ❓ Unknown | Likely on data broker sites (couldn't access) |
| Phone number | ❓ Unknown | Likely on data broker sites (couldn't access) |

**Your current employer is NOT findable** - this is significant protection.

---

## Username "hodgesarolin" Presence Map

| Platform | Found? | What's There |
|----------|--------|--------------|
| Printables.com | ✅ Yes | 3D print models, pet memorial |
| openSUSE Wiki | ✅ Yes | User page (content unknown) |
| Voices.com | ✅ Yes | Voice actor profile |
| GitHub | ❌ No | No account with this exact username |
| Twitter/X | ❌ No | No account found |
| Instagram | ❌ No | No account found |
| Facebook | ❌ No | No account found |
| YouTube | ❌ No | No account found |
| TikTok | ❌ No | No account found |
| Thingiverse | ❌ No | No account found |
| Mastodon/Fediverse | ❌ No | No account found |
| Reddit | ❌ No | No account found |

---

## Aggregation Attack Path

If an adversary wanted to identify and locate you:

```
STARTING POINT: "hodgesarolin"
         ↓
    Printables.com → Ender 3 Pro user, had a dog
         ↓
    openSUSE Wiki → Linux enthusiast, conference attendee
         ↓
    LinkedIn search → "openSUSE Jersey City"
         ↓
    LinkedIn Profile → Daniel Hodges, Chainalysis, Jersey City
         ↓
    Data brokers → Address, phone (behind paywall)
         ↓
    NJ voter records → Address confirmation (if public)
         ↓
    Property records → Full address, home value
```

OR

```
STARTING POINT: "Daniel Hodges"
         ↓
    LinkedIn → Senior DevOps, Jersey City, openSUSE, LOPSA
         ↓
    LOPSA records → Board member, governance documents
         ↓
    openSUSE User:Hodgesarolin → Links to hodgesarolin username
         ↓
    Printables/Voices → Personal details
```

**Time to full identification:** ~1-2 hours for someone with data broker access

---

## Name Collision Protection

Good news: There are MANY Daniel Hodges, which provides some cover:

| Daniel Hodges | Who They Are |
|---------------|--------------|
| Daniel Hodges (police officer) | Jan 6 Capitol defender, very famous |
| Dan Hodges (journalist) | British columnist, The Mail on Sunday |
| Daniel Hodges (Meta engineer) | Different person, speaks at USENIX |
| Daniel Hodges (CEO) | Consumers in Motion Group |
| Daniel Hodges (DMD) | Dentist in Georgia |

The famous Jan 6 police officer Daniel Hodges actually provides significant cover - most searches for your name return him instead.

---

## Risk Assessment for Resistance Work

### If You Work Under "hodgesarolin":
- **Traceable to:** openSUSE community → LinkedIn → Real name → Jersey City
- **Voice exposure:** Voices.com profile may have voice samples
- **Timeline risk:** Pet memorial timestamps your activity

### If You Work Under Real Name:
- **Immediately exposed:** LinkedIn gives employer, location, photo, professional network
- **Historical exposure:** LOPSA board records, conference attendance

### If You Work Under NEW Pseudonym:
- **Lowest risk:** No existing linkage
- **But:** Need OpSec discipline to not cross-contaminate

---

## Recommended Actions

### Immediate (This Week):

1. **Check Voices.com profile** - what's there? Voice samples? Delete if not using.

2. **Review openSUSE wiki page** - log in and see what's public. Consider removing personal details.

3. **Google yourself** in incognito:
   - "Daniel Hodges Jersey City"
   - "Daniel Hodges Chainalysis"
   - "Daniel Hodges openSUSE"
   - "hodgesarolin"
   - Your email address

4. **Check data brokers** (requires signing up):
   - BeenVerified
   - Spokeo
   - WhitePages
   - Intelius
   - Look for: home address, phone, relatives listed

### If Starting Resistance Work:

1. **Create new pseudonym** - don't use hodgesarolin OR real name

2. **Separate devices** - never log into resistance work from personal devices

3. **New email** - ProtonMail or similar, no personal info

4. **VPN always** - Mullvad or similar, paid with crypto

5. **Work through established orgs** - 501(c)(3) status provides some legal cover

### LinkedIn Hardening:

1. Review visibility settings
2. Consider hiding connections
3. Remove or generalize location
4. Check what non-logged-in users see

---

## What I Could NOT Access

- LinkedIn full profile details (requires login)
- openSUSE wiki user page content (domain blocked)
- Voices.com profile content (domain blocked)
- Data broker full records (requires payment)
- NJ voter registration records
- Hudson County property records
- Court records

A more determined searcher with:
- Data broker subscriptions
- Paid people-search tools
- Access to NJ public records databases

...would find significantly more.

---

## Summary

**Your exposure profile:**

| Category | Risk Level | Notes |
|----------|------------|-------|
| Professional identity | HIGH | LinkedIn + LOPSA + openSUSE well-documented |
| Geographic location | MEDIUM | Jersey City known, specific address unknown publicly |
| Current employer | LOW | Prenosis not linked to you publicly |
| Family | LOW | Spouse/kids not findable |
| Username linkage | MEDIUM | hodgesarolin traces back to real identity |

**Bottom line:** Your professional life is well-documented, but your family and current employment are protected. For resistance work, use a fresh identity with strict compartmentalization.

---

*Report generated: January 14, 2026*
*Search depth: ~40+ queries across multiple platforms*
*Limitations: Could not access paywalled data broker sites, some domains blocked*

