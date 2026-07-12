"""
Static, human-written translations for the KB-built features (Simple Story,
Compare, chatbot recommendation).

The scheme *content* (title, benefits, eligibility, ...) is already translated
per scheme in data/translations/<slug>__<lang>.json. This module supplies the
small set of fixed connector/label strings that wrap that content, so every
feature renders fully in the selected language WITHOUT any live LLM call.

Languages: en, hi, bn, ta.
"""

# --- fixed connector / label strings ------------------------------------
UI = {
    "en": {
        "story_intro": "{name} is {role}. For a long time, government help felt confusing and out of reach.",
        "story_learn": "Then {name} learned about {title}.",
        "story_benefit": "It offered something real: {benefit}",
        "story_end": "{name} took one simple step to apply, and life felt a little more secure and hopeful.",
        "in_short": "In short, it gives you:",
        "example": "Think of {title} as a helping hand from the government — you take one small step and get real support back.",
        "eligible_if": "You may be eligible if:",
        "disclaimer": "This is AI-assisted guidance — always confirm on the official portal before applying.",
        "asp_what": "What is it",
        "asp_benefits": "Main benefits",
        "asp_eligibility": "Who is eligible",
        "asp_documents": "Documents needed",
        "asp_apply": "How to apply",
        "asp_deadline": "Deadline",
        "cmp_pick_help": "Pick the one whose eligibility matches your situation.",
        "cmp_unknown": "One or both of these schemes are not in JanNiti's 18 covered schemes.",
        "reco_prefix": "Based on your profile, these schemes look most relevant to you:",
        "reco_none": "Tell me your occupation or age (or fill your profile) and I'll suggest the most relevant schemes.",
        "reco_ask_name": "Ask me about any of these by name for full point-by-point details.",
        "no_scheme_story": "Please pick one of JanNiti's 18 schemes to see its simple story.",
    },
    "hi": {
        "story_intro": "{name} एक {role} है। लंबे समय तक सरकारी मदद उलझी हुई और पहुँच से बाहर लगती थी।",
        "story_learn": "फिर {name} को {title} के बारे में पता चला।",
        "story_benefit": "इसने कुछ वास्तविक दिया: {benefit}",
        "story_end": "{name} ने आवेदन के लिए एक आसान कदम उठाया, और ज़िंदगी थोड़ी अधिक सुरक्षित और आशावान महसूस हुई।",
        "in_short": "संक्षेप में, यह आपको देता है:",
        "example": "{title} को सरकार की मदद के एक हाथ की तरह समझिए — आप एक छोटा कदम उठाते हैं और बदले में असली सहारा पाते हैं।",
        "eligible_if": "आप पात्र हो सकते हैं यदि:",
        "disclaimer": "यह AI-सहायता प्राप्त मार्गदर्शन है — आवेदन से पहले हमेशा आधिकारिक पोर्टल पर पुष्टि करें।",
        "asp_what": "यह क्या है",
        "asp_benefits": "मुख्य लाभ",
        "asp_eligibility": "कौन पात्र है",
        "asp_documents": "आवश्यक दस्तावेज़",
        "asp_apply": "आवेदन कैसे करें",
        "asp_deadline": "समय-सीमा",
        "cmp_pick_help": "वही चुनें जिसकी पात्रता आपकी स्थिति से मेल खाती है।",
        "cmp_unknown": "इनमें से एक या दोनों योजनाएँ JanNiti की 18 कवर की गई योजनाओं में नहीं हैं।",
        "reco_prefix": "आपकी प्रोफ़ाइल के आधार पर, ये योजनाएँ आपके लिए सबसे प्रासंगिक लगती हैं:",
        "reco_none": "मुझे अपना व्यवसाय या उम्र बताएं (या अपनी प्रोफ़ाइल भरें) और मैं सबसे प्रासंगिक योजनाएँ सुझाऊँगा।",
        "reco_ask_name": "पूरी जानकारी के लिए इनमें से किसी के बारे में नाम लेकर पूछें।",
        "no_scheme_story": "उसकी सरल कहानी देखने के लिए कृपया JanNiti की 18 योजनाओं में से एक चुनें।",
    },
    "bn": {
        "story_intro": "{name} একজন {role}। দীর্ঘদিন ধরে সরকারি সাহায্য জটিল ও নাগালের বাইরে মনে হত।",
        "story_learn": "তারপর {name} {title} সম্পর্কে জানতে পারলেন।",
        "story_benefit": "এটি সত্যিকারের কিছু দিল: {benefit}",
        "story_end": "{name} আবেদনের জন্য একটি সহজ পদক্ষেপ নিলেন, আর জীবন একটু বেশি নিরাপদ ও আশাবাদী মনে হল।",
        "in_short": "সংক্ষেপে, এটি আপনাকে দেয়:",
        "example": "{title}-কে সরকারের একটি সাহায্যের হাত হিসেবে ভাবুন — আপনি একটি ছোট পদক্ষেপ নেন এবং বিনিময়ে সত্যিকারের সহায়তা পান।",
        "eligible_if": "আপনি যোগ্য হতে পারেন যদি:",
        "disclaimer": "এটি AI-সহায়তায় দেওয়া নির্দেশনা — আবেদনের আগে সর্বদা সরকারি পোর্টালে নিশ্চিত করুন।",
        "asp_what": "এটি কী",
        "asp_benefits": "প্রধান সুবিধা",
        "asp_eligibility": "কে যোগ্য",
        "asp_documents": "প্রয়োজনীয় নথি",
        "asp_apply": "কীভাবে আবেদন করবেন",
        "asp_deadline": "সময়সীমা",
        "cmp_pick_help": "যেটির যোগ্যতা আপনার পরিস্থিতির সাথে মেলে সেটি বেছে নিন।",
        "cmp_unknown": "এই প্রকল্পগুলির একটি বা উভয়ই JanNiti-র 18টি কভার করা প্রকল্পে নেই।",
        "reco_prefix": "আপনার প্রোফাইলের ভিত্তিতে, এই প্রকল্পগুলি আপনার জন্য সবচেয়ে প্রাসঙ্গিক মনে হচ্ছে:",
        "reco_none": "আমাকে আপনার পেশা বা বয়স বলুন (বা প্রোফাইল পূরণ করুন), আমি সবচেয়ে প্রাসঙ্গিক প্রকল্প সুপারিশ করব।",
        "reco_ask_name": "পূর্ণ বিবরণের জন্য এদের যেকোনো একটির নাম ধরে জিজ্ঞাসা করুন।",
        "no_scheme_story": "এর সরল গল্প দেখতে অনুগ্রহ করে JanNiti-র 18টি প্রকল্পের একটি বেছে নিন।",
    },
    "ta": {
        "story_intro": "{name} ஒரு {role}. நீண்ட காலமாக அரசு உதவி குழப்பமாகவும் எட்டாததாகவும் இருந்தது.",
        "story_learn": "பிறகு {name} {title} பற்றி அறிந்தார்.",
        "story_benefit": "அது உண்மையான ஒன்றைத் தந்தது: {benefit}",
        "story_end": "{name} விண்ணப்பிக்க ஒரு எளிய அடி எடுத்தார், வாழ்க்கை கொஞ்சம் பாதுகாப்பாகவும் நம்பிக்கையாகவும் உணர்ந்தது.",
        "in_short": "சுருக்கமாக, இது உங்களுக்கு வழங்குகிறது:",
        "example": "{title}-ஐ அரசின் உதவிக் கரம் என நினைத்துக் கொள்ளுங்கள் — நீங்கள் ஒரு சிறிய அடி எடுத்தால் உண்மையான ஆதரவு கிடைக்கும்.",
        "eligible_if": "நீங்கள் தகுதி பெறலாம்:",
        "disclaimer": "இது AI-உதவியுடன் வழங்கப்படும் வழிகாட்டல் — விண்ணப்பிக்கும் முன் எப்போதும் அதிகாரப்பூர்வ போர்ட்டலில் உறுதிப்படுத்தவும்.",
        "asp_what": "இது என்ன",
        "asp_benefits": "முக்கிய நன்மைகள்",
        "asp_eligibility": "யார் தகுதியானவர்",
        "asp_documents": "தேவையான ஆவணங்கள்",
        "asp_apply": "எப்படி விண்ணப்பிப்பது",
        "asp_deadline": "காலக்கெடு",
        "cmp_pick_help": "உங்கள் நிலைமைக்கு தகுதி பொருந்தும் ஒன்றைத் தேர்ந்தெடுக்கவும்.",
        "cmp_unknown": "இந்தத் திட்டங்களில் ஒன்று அல்லது இரண்டும் JanNiti-யின் 18 திட்டங்களில் இல்லை.",
        "reco_prefix": "உங்கள் விவரங்களின் அடிப்படையில், இந்தத் திட்டங்கள் உங்களுக்கு மிகவும் பொருத்தமானதாகத் தெரிகிறது:",
        "reco_none": "உங்கள் தொழில் அல்லது வயதைச் சொல்லுங்கள் (அல்லது சுயவிவரத்தை நிரப்புங்கள்), மிகப் பொருத்தமான திட்டங்களைப் பரிந்துரைக்கிறேன்.",
        "reco_ask_name": "முழு விவரங்களுக்கு இவற்றில் ஏதேனும் ஒன்றின் பெயரைக் கூறிக் கேளுங்கள்.",
        "no_scheme_story": "அதன் எளிய கதையைப் பார்க்க JanNiti-யின் 18 திட்டங்களில் ஒன்றைத் தேர்ந்தெடுக்கவும்.",
    },
}

# --- persona role per scheme category (for the Simple Story) --------------
ROLE = {
    "en": {"farmer": "a farmer", "worker": "a hard-working earner",
           "household": "someone from a modest household", "business": "a small business owner",
           "youth": "a young job-seeker", "student": "a bright student", "general": "an ordinary citizen"},
    "hi": {"farmer": "किसान", "worker": "मेहनती कमाने वाला",
           "household": "साधारण परिवार का व्यक्ति", "business": "छोटा व्यवसायी",
           "youth": "युवा नौकरी खोजने वाला", "student": "होनहार छात्र", "general": "आम नागरिक"},
    "bn": {"farmer": "কৃষক", "worker": "পরিশ্রমী উপার্জনকারী",
           "household": "সাধারণ পরিবারের মানুষ", "business": "ছোট ব্যবসায়ী",
           "youth": "তরুণ চাকরিপ্রার্থী", "student": "মেধাবী ছাত্র", "general": "সাধারণ নাগরিক"},
    "ta": {"farmer": "விவசாயி", "worker": "கடின உழைப்பாளி",
           "household": "சாதாரண குடும்பத்தைச் சேர்ந்தவர்", "business": "சிறு தொழில் முனைவோர்",
           "youth": "இளம் வேலைதேடுபவர்", "student": "திறமையான மாணவர்", "general": "சாதாரண குடிமகன்"},
}

# scheme -> category (drives the persona role above)
SCHEME_CAT = {
    "pm-kisan": "farmer", "kisan-credit-card": "farmer", "fasal-bima": "farmer",
    "atal-pension": "worker", "jeevan-jyoti-bima": "worker", "suraksha-bima": "worker",
    "jan-dhan": "household", "garib-kalyan-anna": "household",
    "mudra": "business", "stand-up-india": "business",
    "viksit-bharat-rozgar": "youth", "kaushal-vikas": "youth", "skill-loan": "youth",
    "cbse-single-girl-child": "student", "pg-indira-gandhi-sgc": "student",
    "national-pg-scholarship": "student", "icar-national-talent": "student",
    "ugc-jrf-engineering": "student",
}

# a relatable first name per scheme (kept in Latin script, universally readable)
SCHEME_NAME = {
    "pm-kisan": "Ramesh", "kisan-credit-card": "Ramesh", "fasal-bima": "Ramesh",
    "atal-pension": "Sunita", "jeevan-jyoti-bima": "Amit", "suraksha-bima": "Amit",
    "jan-dhan": "Raju", "garib-kalyan-anna": "Lakshmi",
    "mudra": "Priya", "stand-up-india": "Meena",
    "viksit-bharat-rozgar": "Arjun", "kaushal-vikas": "Arjun", "skill-loan": "Arjun",
    "cbse-single-girl-child": "Anjali", "pg-indira-gandhi-sgc": "Anjali",
    "national-pg-scholarship": "Anjali", "icar-national-talent": "Kiran",
    "ugc-jrf-engineering": "Kiran",
}


def ui(lang: str) -> dict:
    return UI.get(lang, UI["en"])


def role(lang: str, slug: str) -> str:
    cat = SCHEME_CAT.get(slug, "general")
    return ROLE.get(lang, ROLE["en"]).get(cat, ROLE["en"]["general"])


def name(slug: str) -> str:
    return SCHEME_NAME.get(slug, "Ravi")
