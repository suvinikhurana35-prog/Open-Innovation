import type { LangCode } from './i18n'

export type ApplyMode = 'online' | 'offline' | 'hybrid'

export interface SchemeOption {
  id: string          // query sent to backend (English official name -> best retrieval)
  apply: string       // official government APPLICATION / enrolment portal (scheme-specific, verified)
  official: string    // official SCHEME INFORMATION page (ministry / scheme portal)
  mode: ApplyMode     // online = full digital apply; hybrid = digital + bank/branch step; offline = branch/school only
  en: string; hi: string; bn: string; ta: string
}

// The 18 schemes in the JanNiti knowledge base.
// `apply` = where the citizen actually applies (verified official portals).
// `official` = the scheme's own official page (never the MyScheme homepage).
export const SCHEMES: SchemeOption[] = [
  { id: 'Pradhan Mantri Kisan Samman Nidhi (PM-KISAN)',
    apply: 'https://pmkisan.gov.in', official: 'https://pmkisan.gov.in', mode: 'online',
    en: 'PM-KISAN (Kisan Samman Nidhi)', hi: 'पीएम-किसान सम्मान निधि', bn: 'পিএম-কিসান সম্মান নিধি', ta: 'பிஎம்-கிசான் சம்மான் நிதி' },
  { id: 'Kisan Credit Card (KCC)',
    apply: 'https://www.jansamarth.in/kisan-credit-card-scheme', official: 'https://www.myscheme.gov.in/schemes/kcc', mode: 'hybrid',
    en: 'Kisan Credit Card (KCC)', hi: 'किसान क्रेडिट कार्ड', bn: 'কিষান ক্রেডিট কার্ড', ta: 'கிசான் கிரெடிட் கார்டு' },
  { id: 'Pradhan Mantri Fasal Bima Yojana (PMFBY)',
    apply: 'https://pmfby.gov.in', official: 'https://pmfby.gov.in', mode: 'online',
    en: 'PM Fasal Bima Yojana', hi: 'पीएम फसल बीमा योजना', bn: 'পিএম ফসল বিমা যোজনা', ta: 'பிஎம் பசல் பீமா யோஜனா' },
  { id: 'Atal Pension Yojana (APY)',
    apply: 'https://enps.nsdl.com', official: 'https://www.npscra.nsdl.co.in/scheme-details.php', mode: 'hybrid',
    en: 'Atal Pension Yojana', hi: 'अटल पेंशन योजना', bn: 'অটল পেনশন যোজনা', ta: 'அடல் ஓய்வூதியத் திட்டம்' },
  { id: 'Pradhan Mantri Jeevan Jyoti Bima Yojana (PMJJBY)',
    apply: 'https://www.jansuraksha.gov.in', official: 'https://www.jansuraksha.gov.in', mode: 'hybrid',
    en: 'PM Jeevan Jyoti Bima Yojana', hi: 'पीएम जीवन ज्योति बीमा योजना', bn: 'পিএম জীবন জ্যোতি বিমা যোজনা', ta: 'பிஎம் ஜீவன் ஜோதி பீமா' },
  { id: 'Pradhan Mantri Suraksha Bima Yojana (PMSBY)',
    apply: 'https://www.jansuraksha.gov.in', official: 'https://www.jansuraksha.gov.in', mode: 'hybrid',
    en: 'PM Suraksha Bima Yojana', hi: 'पीएम सुरक्षा बीमा योजना', bn: 'পিএম সুরক্ষা বিমা যোজনা', ta: 'பிஎம் சுரக்ஷா பீமா' },
  { id: 'Pradhan Mantri Jan Dhan Yojana (PMJDY)',
    apply: 'https://www.pmjdy.gov.in', official: 'https://www.pmjdy.gov.in', mode: 'offline',
    en: 'PM Jan Dhan Yojana', hi: 'पीएम जन धन योजना', bn: 'পিএম জন ধন যোজনা', ta: 'பிஎம் ஜன் தன் யோஜனா' },
  { id: 'Pradhan Mantri Garib Kalyan Anna Yojana (PMGKAY)',
    apply: 'https://nfsa.gov.in', official: 'https://nfsa.gov.in', mode: 'offline',
    en: 'PM Garib Kalyan Anna Yojana', hi: 'पीएम गरीब कल्याण अन्न योजना', bn: 'পিএম গরিব কল্যাণ অন্ন যোজনা', ta: 'பிஎம் கரீப் கல்யாண் அன்ன யோஜனா' },
  { id: 'Pradhan Mantri MUDRA Yojana (PMMY)',
    apply: 'https://www.udyamimitra.in', official: 'https://www.mudra.org.in', mode: 'online',
    en: 'PM MUDRA Yojana', hi: 'पीएम मुद्रा योजना', bn: 'পিএম মুদ্রা যোজনা', ta: 'பிஎம் முத்ரா யோஜனா' },
  { id: 'Stand-Up India',
    apply: 'https://www.standupmitra.in', official: 'https://www.standupmitra.in', mode: 'online',
    en: 'Stand-Up India', hi: 'स्टैंड-अप इंडिया', bn: 'স্ট্যান্ড-আপ ইন্ডিয়া', ta: 'ஸ்டாண்ட்-அப் இந்தியா' },
  { id: 'Pradhan Mantri Viksit Bharat Rozgar Yojana (PM-VBRY)',
    apply: 'https://pmvbry.epfindia.gov.in', official: 'https://www.epfindia.gov.in', mode: 'online',
    en: 'PM Viksit Bharat Rozgar Yojana', hi: 'पीएम विकसित भारत रोजगार योजना', bn: 'পিএম বিকশিত ভারত রোজগার যোজনা', ta: 'பிஎம் விக்சித் பாரத் ரோஜ்கார்' },
  { id: 'Pradhan Mantri Kaushal Vikas Yojana - Short Term Training (PMKVY 4.0)',
    apply: 'https://www.skillindiadigital.gov.in', official: 'https://www.msde.gov.in', mode: 'online',
    en: 'PM Kaushal Vikas Yojana', hi: 'पीएम कौशल विकास योजना', bn: 'পিএম কৌশল বিকাশ যোজনা', ta: 'பிஎம் கௌசல் விகாஸ்' },
  { id: 'Skill Loan Scheme (Model Skill Loan Scheme)',
    apply: 'https://www.jansamarth.in', official: 'https://www.msde.gov.in', mode: 'hybrid',
    en: 'Skill Loan Scheme', hi: 'स्किल लोन योजना', bn: 'স্কিল লোন স্কিম', ta: 'திறன் கடன் திட்டம்' },
  { id: 'CBSE Merit Scholarship Scheme for Single Girl Child (SGC)',
    apply: 'https://www.cbse.gov.in/cbsenew/scholar.html', official: 'https://www.cbse.gov.in/cbsenew/scholar.html', mode: 'online',
    en: 'CBSE Single Girl Child Scholarship', hi: 'सीबीएसई एकल बालिका मेधा छात्रवृत्ति', bn: 'সিবিএসই একক কন্যা মেধা বৃত্তি', ta: 'சிபிஎஸ்இ ஒற்றை பெண் உதவித்தொகை' },
  { id: 'Post Graduate Indira Gandhi Scholarship for Single Girl Child (PG-IGSSGC)',
    apply: 'https://scholarships.gov.in', official: 'https://www.ugc.gov.in/page/Scholarships.aspx', mode: 'online',
    en: 'PG Indira Gandhi SGC Scholarship', hi: 'पीजी इंदिरा गांधी एकल बालिका छात्रवृत्ति', bn: 'পিজি ইন্দিরা গান্ধী একক কন্যা বৃত্তি', ta: 'பிஜி இந்திரா காந்தி உதவித்தொகை' },
  { id: 'National Scholarship for Post Graduate Studies (NSPG)',
    apply: 'https://scholarships.gov.in', official: 'https://www.ugc.gov.in/page/Scholarships.aspx', mode: 'online',
    en: 'National PG Scholarship (NSPG)', hi: 'स्नातकोत्तर राष्ट्रीय छात्रवृत्ति', bn: 'স্নাতকোত্তর জাতীয় বৃত্তি', ta: 'முதுகலை தேசிய உதவித்தொகை' },
  { id: 'National Talent Scholarship (Undergraduate) - ICAR',
    apply: 'https://education.icar.gov.in', official: 'https://education.icar.gov.in', mode: 'online',
    en: 'ICAR National Talent Scholarship', hi: 'राष्ट्रीय प्रतिभा छात्रवृत्ति (स्नातक)', bn: 'জাতীয় মেধা বৃত্তি (স্নাতক)', ta: 'தேசிய திறமை உதவித்தொகை (இளங்கலை)' },
  { id: 'Junior Research Fellowship in Engineering & Technology (UGC)',
    apply: 'https://www.ugc.gov.in', official: 'https://www.ugc.gov.in', mode: 'online',
    en: 'UGC JRF (Engineering & Technology)', hi: 'जेआरएफ इंजीनियरिंग एवं प्रौद्योगिकी', bn: 'জেআরএফ ইঞ্জিনিয়ারিং ও প্রযুক্তি', ta: 'ஜேஆர்எஃப் பொறியியல் & தொழில்நுட்பம்' },
]

export function schemeLabel(s: SchemeOption, lang: LangCode): string {
  return (s as any)[lang] || s.en
}

export function findScheme(id: string): SchemeOption | undefined {
  return SCHEMES.find((s) => s.id === id)
}
