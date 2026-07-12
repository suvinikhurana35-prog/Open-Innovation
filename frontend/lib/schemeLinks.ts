// Official portal URLs for each scheme.
// Keys are the English scheme name (from SCHEMES list) or slug.
// Falls back to MyScheme search for any unrecognised name.

export const SCHEME_URLS: Record<string, string> = {
  // By English name
  "Atal Pension Yojana": "https://www.npscra.nsdl.co.in/scheme-details.php",
  "CBSE Merit Scholarship (Single Girl Child)": "https://cbse.gov.in/cbsenew/scholarship.html",
  "PM Fasal Bima Yojana": "https://pmfby.gov.in",
  "Junior Research Fellowship (Engineering & Technology)": "https://aicte-india.org/schemes/students-development-schemes/PG-Scholarship-Scheme",
  "Kisan Credit Card": "https://www.pmkisan.gov.in/KCC.aspx",
  "PM-KISAN (Kisan Samman Nidhi)": "https://pmkisan.gov.in",
  "National Scholarship for Post Graduate Studies": "https://scholarships.gov.in",
  "National Talent Scholarship (Undergraduate)": "https://scholarships.gov.in",
  "PM Kaushal Vikas Yojana": "https://www.pmkvyofficial.org",
  "PG Indira Gandhi Scholarship (Single Girl Child)": "https://www.ugc.gov.in/page/Scholarships.aspx",
  "PM Garib Kalyan Anna Yojana": "https://dfpd.gov.in/pmgkay.htm",
  "PM Jan Dhan Yojana": "https://pmjdy.gov.in",
  "PM Jeevan Jyoti Bima Yojana": "https://jansuraksha.gov.in",
  "PM MUDRA Yojana": "https://www.mudra.org.in",
  "PM Viksit Bharat Rozgar Yojana (ELI)": "https://eli.epfindia.gov.in",
  "Skill Loan Scheme": "https://www.skilldevelopment.gov.in/en/schemes",
  "Stand-Up India Scheme": "https://www.standupmitra.in",
  "PM Suraksha Bima Yojana": "https://jansuraksha.gov.in",

  // By slug (fallback)
  atal_pension_yojna: "https://www.npscra.nsdl.co.in/scheme-details.php",
  cbse_merit_scholarship_scheme_for_single_girl_child: "https://cbse.gov.in/cbsenew/scholarship.html",
  fasal_bima_yojna: "https://pmfby.gov.in",
  junior_research_fellowship_in_engineering_and_technology:
    "https://aicte-india.org/schemes/students-development-schemes/PG-Scholarship-Scheme",
  kisan_credit_card: "https://www.pmkisan.gov.in/KCC.aspx",
  kissan_samman_nidhi: "https://pmkisan.gov.in",
  national_scholarship_for_post_graduate_studies: "https://scholarships.gov.in",
  national_talent_scholarship_undergraduate: "https://scholarships.gov.in",
  pm_kaushal_vikas_yojna: "https://www.pmkvyofficial.org",
  post_graduate_scholarship_for_single_girl_child: "https://www.ugc.gov.in/page/Scholarships.aspx",
  pradhan_mantri_garib_kalyan_anna_yojna: "https://dfpd.gov.in/pmgkay.htm",
  pradhan_mantri_jan_dhan_dhan_yojna: "https://pmjdy.gov.in",
  pradhan_mantri_jeevan_jyoti_bima_yojna: "https://jansuraksha.gov.in",
  pradhan_mantri_mudra_yojna: "https://www.mudra.org.in",
  pradhan_mantri_viksit_bharat_rozgar_yojna: "https://eli.epfindia.gov.in",
  skill_loan_scheme: "https://www.skilldevelopment.gov.in/en/schemes",
  stand_up_india_scheme_for_buisness: "https://www.standupmitra.in",
  suraksha_bina_yojna: "https://jansuraksha.gov.in",
};

/**
 * Resolve the official URL for a scheme given its display name or slug.
 * Falls back to MyScheme search if not found.
 */
export function getSchemeUrl(nameOrSlug: string): string {
  return (
    SCHEME_URLS[nameOrSlug] ||
    `https://www.myscheme.gov.in/search?q=${encodeURIComponent(nameOrSlug)}`
  );
}
