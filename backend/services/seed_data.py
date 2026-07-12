"""Seed the vector database with initial scheme data for JanNiti."""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.rag_service import rag_service

SEED_DOCUMENTS = [
    {
        "text": """Pradhan Mantri Kisan Samman Nidhi (PM-KISAN) is a Central Sector scheme launched in February 2019. Under this scheme, the Government of India provides income support of Rs. 6,000 per year to all landholding farmer families across the country. The amount is paid in three equal installments of Rs. 2,000 each every four months. The scheme is fully funded by the Central Government. Farmers can check their beneficiary status on the PM-KISAN portal. The scheme aims to supplement the financial needs of farmers in procuring various inputs to ensure proper crop health and appropriate yields. Exclusions: The scheme excludes institutional land holders, farmer families covered under other similar income support schemes may be excluded. Application: Through PM-KISAN portal or local agriculture office. Documents: Aadhaar card, land records, bank account details.""",
        "metadata": {
            "name": "PM Kisan Samman Nidhi",
            "ministry": "Ministry of Agriculture",
            "type": "Central Scheme",
            "source": "pmkisan.gov.in",
            "language": "en",
            "last_updated": "2024-12-01"
        },
        "id": "pm-kisan-1"
    },
    {
        "text": """Pradhan Mantri Jan Arogya Yojana (PM-JAY) is the world's largest health insurance scheme, launched under Ayushman Bharat in September 2018. It provides a health cover of Rs. 5 lakh per family per year for secondary and tertiary care hospitalization. The scheme targets over 12 crore poor and vulnerable families (approximately 55 crore beneficiaries) based on SECC 2011 data. Benefits include cashless and paperless access to services at empanelled hospitals. Coverage includes 3 days pre-hospitalization and 15 days post-hospitalization costs. Pre-existing diseases are covered from day one. There is no cap on family size and age. The scheme also includes free diagnostic services and medicines. Transport allowance of up to Rs. 1000 per hospitalization is provided. IMPORTANT: The scheme only covers hospitalization costs, not OPD (outpatient) visits. Some high-end procedures may require prior authorization. The scheme is portable across India.""",
        "metadata": {
            "name": "Ayushman Bharat PM-JAY",
            "ministry": "Ministry of Health",
            "type": "Central Scheme",
            "source": "pmjay.gov.in",
            "language": "en",
            "last_updated": "2024-11-15"
        },
        "id": "ayushman-1"
    },
    {
        "text": """Pradhan Mantri Ujjwala Yojana (PMUY) was launched in May 2016 to provide LPG connections to women from Below Poverty Line (BPL) households. The scheme provides a deposit-free LPG connection to eligible households. The initial connection and first refill are provided free of cost. As of 2024, over 10.3 crore connections have been released under the scheme. Eligibility: Adult women from BPL households, women from SC/ST communities, PM Awas Yojana beneficiaries, Antyodaya Anna Yojana cardholders, and beneficiaries of select other social schemes. Documents: Aadhaar card, BPL ration card or any notified document, proof of address, passport size photo, and a declaration on Rs. 10 stamp paper. The scheme has been extended to include migrant families and those without Aadhaar (subject to other ID proofs). IMPORTANT: Beneficiaries must pay for subsequent refills. The free first refill policy has changed over time.""",
        "metadata": {
            "name": "PM Ujjwala Yojana",
            "ministry": "Ministry of Petroleum",
            "type": "Central Scheme",
            "source": "pmujjwala.gov.in",
            "language": "en",
            "last_updated": "2024-10-20"
        },
        "id": "pm-ujjwala-1"
    },
    {
        "text": """Pradhan Mantri Awas Yojana (PMAY) is a flagship housing scheme launched in June 2015 with the aim of providing affordable housing to all by 2024. The scheme has two components: PMAY-Urban and PMAY-Gramin. PMAY-Urban provides a subsidy of up to Rs. 2.67 lakh on home loans through CLSS (Credit Linked Subsidy Scheme). Beneficiaries receive houses with basic amenities like toilet, electricity, and water connection. The beneficiary contribution is minimal, with substantial government support. Eligibility: Families belonging to EWS (annual income up to Rs. 3 lakh), LIG (Rs. 3-6 lakh), and MIG (Rs. 6-18 lakh). The woman of the family must be the owner or co-owner of the house. No adult member of the family should own a pucca house anywhere in India. Subsidy interest rates vary by category: EWS/LIG - 6.5%, MIG-I - 4%, MIG-II - 3%. The subsidy is available for a maximum loan period of 20 years.""",
        "metadata": {
            "name": "PM Awas Yojana",
            "ministry": "Ministry of Housing",
            "type": "Central Scheme",
            "source": "pmay.gov.in",
            "language": "en",
            "last_updated": "2024-09-30"
        },
        "id": "pm-awas-1"
    },
    {
        "text": """Mahatma Gandhi National Rural Employment Guarantee Act (MGNREGA) is a landmark law enacted in 2005 that guarantees 100 days of wage employment per year to every rural household whose adult members volunteer to do unskilled manual work. Wages are paid at the notified minimum wage rate applicable in each state. Work must be provided within 15 days of application, otherwise unemployment allowance must be paid. The scheme mandates that one-third of beneficiaries must be women. Priority is given to SC/ST households. Works include water conservation, drought proofing, land development, rural connectivity, and sanitation. Social audit is a key feature - beneficiaries can audit the scheme implementation. IMPORTANT: Employment is not a right if work demands are made during agricultural peak seasons when the local authority determines work cannot be provided. The 100 days are per household, not per individual. Payment is based on work output (measurement), not just attendance.""",
        "metadata": {
            "name": "MGNREGA",
            "ministry": "Ministry of Rural Development",
            "type": "Central Scheme",
            "source": "nrega.nic.in",
            "language": "en",
            "last_updated": "2024-08-15"
        },
        "id": "mgnrega-1"
    },
    {
        "text": """Pradhan Mantri Shram Yogi Maan-dhan (PM-SYM) is a voluntary and contributory pension scheme for unorganized sector workers launched in February 2019. Workers aged 18-40 years with monthly income of Rs. 15,000 or less can join. Under the scheme, a monthly pension of Rs. 3,000 is assured after attaining the age of 60 years. The subscriber contributes a small monthly amount based on his/her age at entry, and the Government contributes an equal amount. Benefits include a guaranteed minimum pension of Rs. 3,000 per month, family pension (50% of the subscriber's pension) to spouse after the subscriber's death, and the option to exit the scheme early with return of contributions plus interest. To enroll, visit Common Service Centres (CSC) with Aadhaar card and savings bank account. The scheme is administered by the Ministry of Labour and Employment through the Life Insurance Corporation of India (LIC).""",
        "metadata": {
            "name": "PM Shram Yogi Maan-dhan",
            "ministry": "Ministry of Labour",
            "type": "Central Scheme",
            "source": "labour.gov.in",
            "language": "en",
            "last_updated": "2024-07-20"
        },
        "id": "pm-shram-1"
    },
    {
        "text": """Pradhan Mantri Mudra Yojana (PMMY) was launched in April 2015 to provide loans of up to Rs. 10 lakh to non-corporate, non-farm small/micro enterprises. The scheme provides three categories of loans: Shishu (up to Rs. 50,000), Kishore (Rs. 50,001 to Rs. 5 lakh), and Tarun (Rs. 5,00,001 to Rs. 10 lakh). Any Indian citizen who has a business plan for a non-farm income-generating activity can apply. Manufacturing, processing, trading, and service sector businesses are eligible. There is no collateral required for any category of loan. Loans are provided by banks, NBFCs, MFIs, and other financial institutions. Existing MUDRA loans can be upgraded from one category to next as business grows. The scheme has been particularly successful for women entrepreneurs, SC/ST, and OBC entrepreneurs. IMPORTANT: The loan is for business purposes only, not personal use. Interest rates vary by institution. Late payment penalties apply.""",
        "metadata": {
            "name": "PM Mudra Yojana",
            "ministry": "Ministry of Finance",
            "type": "Central Scheme",
            "source": "mudra.org.in",
            "language": "en",
            "last_updated": "2024-06-10"
        },
        "id": "pm-mudra-1"
    },
    {
        "text": """Pradhan Mantri Fasal Bima Yojana (PMFBY) is a crop insurance scheme launched in January 2016. It provides insurance coverage for crops against natural calamities like drought, flood, cyclone, hailstorm, pest attacks, and other risks. Farmers pay a uniform premium of 2% for all kharif crops, 1.5% for all rabi crops, and 5% for annual commercial/horticultural crops. The remaining premium is subsidized by the Government. Coverage includes prevented sowing, post-harvest losses, localized calamities, and damage to standing crops. Claims are settled through bank accounts of farmers. The scheme uses technology like remote sensing, drones, and smartphones for crop assessment. All farmers growing notified crops in notified areas during the season are eligible, including sharecroppers and tenants. IMPORTANT: The scheme covers only the loan amount for loanee farmers. Non-loanee farmers can also apply but must do so before the cutoff date. Assessment of loss may take time.""",
        "metadata": {
            "name": "PM Fasal Bima Yojana",
            "ministry": "Ministry of Agriculture",
            "type": "Central Scheme",
            "source": "pmfby.gov.in",
            "language": "en",
            "last_updated": "2024-05-20"
        },
        "id": "pmfby-1"
    },
    {
        "text": """Pradhan Mantri Kaushal Vikas Yojana (PMKVY) is a skill development initiative launched in 2015 to enable India's youth to take up industry-relevant skill training. The scheme provides free skill training to youth aged 15-45 years. Upon successful completion of training, candidates receive Government certification and placement assistance. The scheme also offers recognition of prior learning (RPL) for those with existing skills. Training courses cover 300+ job roles across 40+ sectors including IT, healthcare, retail, construction, tourism, and more. Stipends may be provided for travel and boarding during training. The scheme targets unemployed youth, school/college dropouts, and women. Candidates must have a valid Aadhaar card. IMPORTANT: Training center attendance is mandatory - minimum 70% attendance required to appear for assessment. Not all courses guarantee job placement. Certification is valid as per respective Sector Skill Council norms.""",
        "metadata": {
            "name": "PM Kaushal Vikas Yojana",
            "ministry": "Ministry of Skill Development",
            "type": "Central Scheme",
            "source": "pmkvyofficial.org",
            "language": "en",
            "last_updated": "2024-04-15"
        },
        "id": "skill-india-1"
    },
    {
        "text": """Jal Jeevan Mission (JJM) - Har Ghar Jal was launched in August 2019 to provide tap water connections to every rural household in India by 2024. The mission aims to provide 55 litres of water per person per day. Water quality is ensured through regular testing - every village has 5 trained women tested using FTK kits. The mission follows a community approach - villages prepare their own Village Action Plans (VAP). The Central and State Governments share the cost in a 50:50 ratio for most states (90:10 for Himalayan/North Eastern states and 100% for UTs). Priority is given to SC/ST majority villages, villages in drought-prone areas, and quality-affected habitations. The mission also focuses on greywater management and groundwater recharge. IMPORTANT: The mission provides infrastructure, but villagers must form a Village Water & Sanitation Committee (VWSC) to manage the local water supply. Failure to maintain the system may result in service disruption.""",
        "metadata": {
            "name": "Jal Jeevan Mission (Har Ghar Jal)",
            "ministry": "Ministry of Water",
            "type": "Central Scheme",
            "source": "jaljeevanmission.gov.in",
            "language": "en",
            "last_updated": "2024-03-25"
        },
        "id": "jai-jeevan-1"
    },
    {
        "text": """Pradhan Mantri Matru Vandana Yojana (PMMVY) is a maternity benefit scheme launched in 2017. It provides a cash incentive of Rs. 5,000 to pregnant women and lactating mothers for the first living child. The amount is released in three installments: Rs. 1,000 on early registration of pregnancy (within 150 days), Rs. 2,000 after six months of pregnancy (subject to at least one ANC visit), and Rs. 2,000 after childbirth (for child immunization and registration). The total benefit including institutional delivery under Janani Suraksha Yojana is approximately Rs. 6,000. Eligible: All pregnant women and lactating mothers aged 19 years and above for first living child. Government employees are excluded. IMPORTANT: The scheme is only for the FIRST living child. If a woman marries after 18 and conceives, she must register within 150 days of pregnancy. Aadhaar is mandatory. Missed installments cannot be claimed later. Applications are through Anganwadi Centers.""",
        "metadata": {
            "name": "PM Matru Vandana Yojana",
            "ministry": "Ministry of Women & Child",
            "type": "Central Scheme",
            "source": "wcd.nic.in",
            "language": "en",
            "last_updated": "2024-02-10"
        },
        "id": "matru-vandana-1"
    },
    {
        "text": """Sukanya Samriddhi Yojana (SSY) is a small savings scheme launched in 2015 under the Beti Bachao Beti Padhao campaign. It is designed to secure the future of the girl child. The account can be opened for a girl child from birth up to age 10 years. The minimum deposit is Rs. 250 and maximum is Rs. 1.5 lakh per financial year. The account earns interest rate (currently 8.2% p.a. for FY 2024-25) compounded annually. The account matures after 21 years from the date of opening or the girl's marriage after 18. Partial withdrawal (up to 50%) is allowed for higher education after the girl attains 18. Benefits: Tax deduction under Section 80C, tax-free interest, and tax-free maturity amount. The account can be opened at any post office or authorized bank branch. IMPORTANT: Only one account per girl child (maximum 2 accounts per family). If minimum balance is not maintained, account becomes inactive. Premature closure allowed only in case of the girl's marriage or death of guardian.""",
        "metadata": {
            "name": "Sukanya Samriddhi Yojana",
            "ministry": "Ministry of Finance",
            "type": "Central Scheme",
            "source": "indiapost.gov.in",
            "language": "en",
            "last_updated": "2024-01-15"
        },
        "id": "sukanya-1"
    },
    {
        "text": """प्रधानमंत्री किसान सम्मान निधि (PM-KISAN) एक केंद्रीय क्षेत्र की योजना है जिसे फरवरी 2019 में शुरू किया गया था। इस योजना के तहत, भारत सरकार देशभर के सभी भूमि धारक किसान परिवारों को प्रति वर्ष 6,000 रुपये की आय सहायता प्रदान करती है। यह राशि हर चार महीने में 2,000 रुपये की तीन समान किश्तों में दी जाती है। यह योजना पूरी तरह से केंद्र सरकार द्वारा वित्त पोषित है। किसान पीएम-किसान पोर्टल पर अपनी लाभार्थी स्थिति देख सकते हैं। आवेदन: पीएम-किसान पोर्टल या स्थानीय कृषि कार्यालय के माध्यम से। दस्तावेज: आधार कार्ड, भूमि रिकॉर्ड, बैंक खाता विवरण।""",
        "metadata": {
            "name": "PM Kisan Samman Nidhi",
            "ministry": "Ministry of Agriculture",
            "type": "Central Scheme",
            "source": "pmkisan.gov.in",
            "language": "hi",
            "last_updated": "2024-12-01"
        },
        "id": "pm-kisan-hi-1"
    },
    {
        "text": """आयुष्मान भारत प्रधानमंत्री जन आरोग्य योजना (PM-JAY) दुनिया की सबसे बड़ी स्वास्थ्य बीमा योजना है, जिसे सितंबर 2018 में आयुष्मान भारत के तहत शुरू किया गया था। यह प्रति परिवार प्रति वर्ष 5 लाख रुपये तक का स्वास्थ्य कवर प्रदान करती है। यह योजना SECC 2011 डेटा के आधार पर 12 करोड़ से अधिक गरीब और कमजोर परिवारों को लक्षित करती है। लाभों में कैशलेस और पेपरलेस अस्पताल में भर्ती होना शामिल है। पूर्व मौजूदा बीमारियां पहले दिन से कवर की जाती हैं। परिवार के आकार और उम्र की कोई सीमा नहीं है। महत्वपूर्ण: यह योजना केवल अस्पताल में भर्ती होने की लागत को कवर करती है, OPD विज़िट को नहीं।""",
        "metadata": {
            "name": "Ayushman Bharat PM-JAY",
            "ministry": "Ministry of Health",
            "type": "Central Scheme",
            "source": "pmjay.gov.in",
            "language": "hi",
            "last_updated": "2024-11-15"
        },
        "id": "ayushman-hi-1"
    },
    {
        "text": """PM Street Vendor's AtmaNirbhar Nidhi (PM SVANidhi) was launched in June 2020 to provide affordable working capital loans to street vendors. The scheme provides collateral-free loans of up to Rs. 10,000 (first tranche), Rs. 20,000 (second tranche), and Rs. 50,000 (third tranche). The loan tenure is 12 months. Interest subsidy of 7% per annum is provided on timely repayment. Digital transactions are incentivized with cashbacks. All street vendors vending on or before March 24, 2020 are eligible. The scheme is implemented through Small Industries Development Bank of India (SIDBI). IMPORTANT: The scheme is only for street vendors engaged in vending in urban areas. The loan should be repaid on time to qualify for subsequent tranches. Failure to repay affects eligibility for future loans under the scheme.""",
        "metadata": {
            "name": "PM SVANidhi",
            "ministry": "Ministry of Housing",
            "type": "Central Scheme",
            "source": "pmsvanidhi.mohua.gov.in",
            "language": "en",
            "last_updated": "2024-03-01"
        },
        "id": "pm-svanidhi-1"
    }
]

def seed_database():
    print(f"Existing documents: {rag_service.count_documents()}")
    if rag_service.count_documents() > 0:
        print("Database already seeded. Skipping...")
        return

    for doc in SEED_DOCUMENTS:
        rag_service.add_document(
            text=doc["text"],
            metadata=doc["metadata"],
            doc_id=doc["id"]
        )
        print(f"Added: {doc['metadata']['name']} ({doc['metadata'].get('language', 'en')})")

    print(f"\nTotal documents in database: {rag_service.count_documents()}")

if __name__ == "__main__":
    seed_database()
