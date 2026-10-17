"""
Hinglish Pronunciation Normalizer Engine
Converts Roman Hinglish, technical acronyms, and names into optimized phonetic representations
so that Edge-TTS (hi-IN-SwaraNeural / en-IN-NeerjaNeural) pronounces every word naturally
without robotic glitches or foreign accent distortion.
"""

import re

# Word-level replacements using word boundaries
PRONUNCIATION_MAP = {
    # 1. Names
    r"\bnoaman\b": "नोमान",
    r"\bnoman\b": "नोमान",
    r"\bnauman\b": "नोमान",
    r"\bmj\b": "एम.जे.",
    r"\bm\.j\.\b": "एम.जे.",

    # 2. Hardware, Telecom & Tech Acronyms (Crucial: prevents RAM being read as 'Lord Ram')
    r"\bram\b": "रैम",
    r"\brom\b": "रोम",
    r"\bcpu\b": "सी.पी.यू.",
    r"\bgpu\b": "जी.पी.यू.",
    r"\bpc\b": "पी.सी.",
    r"\bgb\b": "जी.बी.",
    r"\bmb\b": "एम.बी.",
    r"\bkb\b": "के.बी.",
    r"\btb\b": "टी.बी.",
    r"\bwifi\b|\bwi-fi\b": "वाई-फ़ाई",
    r"\bsms\b": "एस.एम.एस.",
    r"\burl\b": "यू.आर.एल.",
    r"\bid\b": "आई.डी.",
    r"\busb\b": "यू.एस.बी.",
    r"\bapi\b": "ए.पी.आई.",
    r"\bui\b": "यू.आई.",
    r"\bos\b": "ओ.एस.",
    r"\btts\b": "टी.टी.एस.",
    r"\bai\b": "ए.आई.",
    r"\bhd\b": "एच.डी.",
    r"\bfps\b": "एफ.पी.एस.",
    r"\bip\b": "आई.पी.",
    r"\bpwa\b": "पी.डब्ल्यू.ए.",

    # 3. Apps & Brand Names
    r"\bwhatsapp\b": "व्हाट्सएप",
    r"\byoutube\b": "यूट्यूब",
    r"\bchrome\b": "क्रोम",
    r"\bnotepad\b": "नोटपैड",
    r"\bgoogle\b": "गूगल",
    r"\binstagram\b": "इंस्टाग्राम",
    r"\bfacebook\b": "फ़ेसबुक",
    r"\btwitter\b": "ट्विटर",

    # 4. Pronouns & Addressing
    r"\bmain\b|\bmai\b": "मैं",
    r"\bmaine\b": "मैंने",
    r"\baap\b": "आप",
    r"\btum\b": "तुम",
    r"\baapne\b": "आपने",
    r"\btumne\b": "तुमने",
    r"\baapka\b": "आपका",
    r"\baapki\b": "आपकी",
    r"\baapke\b": "आपके",
    r"\btumhara\b": "तुम्हारा",
    r"\btumhari\b": "तुम्हारी",
    r"\btumhare\b": "तुम्हारे",
    r"\bmera\b": "मेरा",
    r"\bmeri\b": "मेरी",
    r"\bmere\b": "मेरे",
    r"\bmujhe\b": "मुझे",
    r"\bhume\b|\bhumein\b": "हमें",
    r"\bhum\b": "हम",
    r"\byeh\b|\bye\b": "यह",
    r"\bwoh\b|\bwo\b": "वो",
    r"\bkisi\b": "किसी",
    r"\bkisiko\b": "किसीको",
    r"\bsab\b": "सब",
    r"\bsabko\b": "सबको",
    r"\bsabka\b": "सबका",

    # 5. Auxiliaries, Modals & State
    r"\bhu\b|\bhoon\b|\bhun\b": "हूँ",
    r"\bhai\b": "है",
    r"\bhain\b": "हैं",
    r"\bho\b": "हो",
    r"\btha\b": "था",
    r"\bthi\b": "थी",
    r"\bthe\b": "थे",
    r"\bhoga\b": "होगा",
    r"\bhogi\b": "होगी",
    r"\bhonge\b": "होंगे",
    r"\braha\b": "रहा",
    r"\brahi\b": "रही",
    r"\brahe\b": "रहे",
    r"\btheek\b|\bthik\b": "ठीक",
    r"\bsahi\b": "सही",
    r"\bgalat\b": "गलत",
    r"\baccha\b|\bachha\b": "अच्छा",
    r"\bacchi\b|\bachhi\b": "अच्छी",
    r"\bacche\b|\bachhe\b": "अच्छे",
    r"\bkhatam\b": "खत्म",
    r"\bshuru\b": "शुरू",
    r"\bchalu\b": "चालू",
    r"\bband\b": "बंद",
    r"\bbilkul\b": "बिल्कुल",

    # 6. Common Verbs
    r"\bkaro\b|\bkro\b": "करो",
    r"\bkar\b": "कर",
    r"\bkarna\b": "करना",
    r"\bkarein\b|\bkare\b": "करें",
    r"\bkiya\b": "किया",
    r"\bkiye\b": "किए",
    r"\bdiya\b": "दिया",
    r"\bdiye\b": "दिए",
    r"\bdi\b": "दी",
    r"\bdo\b": "दो",
    r"\bde\b": "दे",
    r"\bdein\b": "दें",
    r"\ble\b": "ले",
    r"\bliya\b": "लिया",
    r"\bliye\b": "लिए",
    r"\bli\b": "ली",
    r"\bgaya\b": "गया",
    r"\bgayi\b": "गयी",
    r"\bgaye\b": "गए",
    r"\bhua\b": "हुआ",
    r"\bhui\b": "हुई",
    r"\bhuye\b": "हुए",
    r"\bmila\b": "मिला",
    r"\bmili\b": "मिली",
    r"\bmile\b": "मिले",
    r"\bbhejo\b": "भेजो",
    r"\bbhejna\b": "भेजना",
    r"\bbhej\b": "भेज",
    r"\bbheja\b": "भेजा",
    r"\bdekho\b": "देखो",
    r"\bdekh\b": "देख",
    r"\bdekha\b": "देखा",
    r"\bsuno\b": "सुनो",
    r"\bsun\b": "सुन",
    r"\bsunao\b": "सुनाओ",
    r"\bbolo\b": "बोलो",
    r"\bboliye\b": "बोलिए",
    r"\bbatao\b": "बताओ",
    r"\bbataiye\b": "बताइए",
    r"\bbataye\b": "बताएं",
    r"\bchalao\b": "चलाओ",
    r"\bchalaye\b": "चलाएं",
    r"\bchala\b": "चला",
    r"\bchal\b": "चल",
    r"\bchalta\b": "चलता",
    r"\bchalti\b": "चलती",
    r"\bchalte\b": "चलते",
    r"\bhona\b": "होना",
    r"\bhone\b": "होने",
    r"\baaya\b": "आया",
    r"\baaye\b": "आए",
    r"\baayi\b": "आयी",
    r"\bkuch\b": "कुछ",
    r"\broko\b": "रोको",
    r"\blagao\b": "लगाओ",
    r"\blaga\b": "लगा",
    r"\blagayi\b": "लगायी",
    r"\bkholo\b": "खोलो",
    r"\bkhol\b": "खोल",
    r"\bbanao\b": "बनाओ",
    r"\bbanaye\b": "बनाएं",
    r"\brakho\b": "रखो",
    r"\bdhundo\b|\bdhoondo\b": "ढूंढो",
    r"\bseekho\b|\bsikho\b": "सीखो",
    r"\bseekha\b|\bsikha\b": "सीखा",

    # 7. Particles, Conjunctions & Questions
    r"\bka\b": "का",
    r"\bki\b": "की",
    r"\bke\b": "के",
    r"\bko\b": "को",
    r"\bse\b": "से",
    r"\bpar\b|\bpe\b": "पर",
    r"\bme\b|\bmein\b": "में",
    r"\baur\b": "और",
    r"\bya\b": "या",
    r"\bnahi\b|\bnhi\b": "नहीं",
    r"\bmat\b": "मत",
    r"\bhaan\b|\bha\b": "हाँ",
    r"\bkya\b": "क्या",
    r"\bkyun\b|\bkyu\b": "क्यों",
    r"\bkaha\b|\bkahan\b": "कहाँ",
    r"\bkaise\b": "कैसे",
    r"\bkaisa\b": "कैसा",
    r"\bkaisi\b": "कैसी",
    r"\bkab\b": "कब",
    r"\bkitna\b": "कितना",
    r"\bkitni\b": "कितनी",
    r"\bkitne\b": "कितने",
    r"\bbohot\b|\bbahut\b": "बहुत",
    r"\bzyada\b|\bjyada\b": "ज़्यादा",
    r"\bkam\b": "कम",
    r"\bzara\b": "ज़रा",
    r"\bthoda\b": "थोड़ा",
    r"\bthodi\b": "थोड़ी",
    r"\bsirf\b": "सिर्फ",
    r"\bbas\b": "बस",
    r"\bbhi\b": "भी",
    r"\bhi\b": "ही",
    r"\btoh\b|\bto\b": "तो",
    r"\bjab\b": "जब",
    r"\btab\b": "तब",
    r"\bab\b": "अब",
    r"\bekdum\b|\bekdam\b": "एकदम",
    r"\bsaare\b|\bsaari\b|\bsaara\b": "सारे",
    r"\bkoi\b": "कोई",
    r"\bapna\b": "अपना",
    r"\bapni\b": "अपनी",
    r"\bapne\b": "अपने",
    r"\byahan\b|\byaha\b": "यहाँ",
    r"\bwahan\b|\bwaha\b": "वहाँ",
    r"\bturant\b|\bturrant\b": "तुरंत",
    r"\bhamesha\b": "हमेशा",
    r"\bkabhi\b": "कभी",
    r"\bpehle\b": "पहले",
    r"\bbaad\b": "बाद",
    r"\bsaath\b": "साथ",
    r"\bbina\b": "बिना",
    r"\bkripya\b|\bplease\b": "कृपया",
    r"\bshukriya\b|\bdhanyawad\b": "शुक्रिया",
    r"\balvida\b": "अलविदा",
    r"\bgaana\b|\bgana\b": "गाना",
    r"\baawaz\b|\bawaz\b": "आवाज़",
    r"\bkhud\b|\bkhude\b": "खुद",
    r"\bdikkat\b": "दिक्कत",
    r"\bmusibat\b": "मुसीबत",

    # 8. Feminine & Friendly Expressions
    r"\bdungi\b|\bdoongi\b": "दूँगी",
    r"\bsakti\b": "सकती",
    r"\bsamajh\b": "समझ",
    r"\byaar\b": "यार",
    r"\baccha\b|\bachha\b": "अच्छा",
    r"\bhaye\b|\bhey\b": "हे",
}

# Compile regex patterns once for optimal runtime speed
COMPILED_PATTERNS = [
    (re.compile(pattern, re.IGNORECASE), replacement)
    for pattern, replacement in PRONUNCIATION_MAP.items()
]

DIGIT_WORDS = {
    '0': 'zero', '1': 'one', '2': 'two', '3': 'three', '4': 'four',
    '5': 'five', '6': 'six', '7': 'seven', '8': 'eight', '9': 'nine'
}

ONES = ['', 'one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine']
TEENS = ['ten', 'eleven', 'twelve', 'thirteen', 'fourteen', 'fifteen', 'sixteen', 'seventeen', 'eighteen', 'nineteen']
TENS = ['', '', 'twenty', 'thirty', 'forty', 'fifty', 'sixty', 'seventy', 'eighty', 'ninety']

def int_to_english(n: int) -> str:
    """Converts any integer into its English word representation"""
    if n == 0:
        return 'zero'
    if n < 0:
        return 'minus ' + int_to_english(abs(n))

    parts = []
    if n >= 10000000:
        crore = n // 10000000
        parts.append(int_to_english(crore) + ' crore')
        n %= 10000000
    if n >= 100000:
        lakh = n // 100000
        parts.append(int_to_english(lakh) + ' lakh')
        n %= 100000
    if n >= 1000:
        thousand = n // 1000
        parts.append(int_to_english(thousand) + ' thousand')
        n %= 1000
    if n >= 100:
        hundred = n // 100
        parts.append(ONES[hundred] + ' hundred')
        n %= 100
    if n >= 20:
        tens_part = TENS[n // 10]
        rem = n % 10
        if rem > 0:
            parts.append(tens_part + ' ' + ONES[rem])
        else:
            parts.append(tens_part)
    elif n >= 10:
        parts.append(TEENS[n - 10])
    elif n > 0:
        parts.append(ONES[n])

    return ' '.join(parts)

def convert_numbers_to_english(text: str) -> str:
    """
    Converts all numbers, percentages, phone numbers, and decimals into English words
    so that numbers are always spoken in English by the female TTS voice.
    """
    if not text:
        return ""

    # Clean zip filenames with timestamps like mj_data_vault_20261016_111955.zip
    text = re.sub(r'mj_data_vault_\d+_\d+\.zip', 'mj data vault zip', text, flags=re.IGNORECASE)
    text = re.sub(r'tasks_history\.zip', 'tasks history zip', text, flags=re.IGNORECASE)
    text = re.sub(r'([a-zA-Z0-9_\-]+)\.zip', r'\1 zip', text)

    # Clean +91 phone prefix
    text = re.sub(r'\+91[\s\-]?', 'plus nine one ', text)

    # Separate attached units from numbers (e.g. 8GB -> 8 GB, 10min -> 10 min)
    text = re.sub(r'(\d+)\s*(GB|MB|KB|TB|FPS|G|M|K|min|sec|hr|p)\b', r'\1 \2', text, flags=re.IGNORECASE)

    # Continuous 10-digit phone numbers -> spell digit by digit in English
    def repl_phone(m):
        digits = m.group(0)
        return ' '.join(DIGIT_WORDS.get(d, d) for d in digits)

    text = re.sub(r'\b\d{10}\b', repl_phone, text)

    # Percentages (e.g. 72.7% or 73%)
    def repl_percent(m):
        num_str = m.group(1)
        if '.' in num_str:
            whole, frac = num_str.split('.', 1)
            whole_en = int_to_english(int(whole)) if whole.isdigit() else whole
            frac_en = ' '.join(DIGIT_WORDS.get(d, d) for d in frac)
            return f'{whole_en} point {frac_en} percent'
        else:
            return f'{int_to_english(int(num_str))} percent'

    text = re.sub(r'(\d+(?:\.\d+)?)\s*%', repl_percent, text)

    # Decimals (e.g. 10.9 or 3.1)
    def repl_decimal(m):
        whole = m.group(1)
        frac = m.group(2)
        whole_en = int_to_english(int(whole)) if whole.isdigit() else whole
        frac_en = ' '.join(DIGIT_WORDS.get(d, d) for d in frac)
        return f'{whole_en} point {frac_en}'

    text = re.sub(r'\b(\d+)\.(\d+)\b', repl_decimal, text)

    # Long sequences >= 7 digits
    text = re.sub(r'\b\d{7,}\b', repl_phone, text)

    # Remaining integers
    def repl_num(m):
        n = int(m.group(0))
        return int_to_english(n)

    text = re.sub(r'\b\d+\b', repl_num, text)
    return text

def normalize_hinglish(text: str) -> str:
    """
    Phonetically optimizes a Hinglish string for natural Hindi/Hinglish female TTS pronunciation.
    1. Converts all numbers into English words (as requested: English numbers only).
    2. Maps Hindi particles, names, and tech acronyms to natural phonetic representations.
    """
    if not text or not text.strip():
        return ""

    # Step 1: Convert all numbers into English words
    result = convert_numbers_to_english(text)

    # Step 2: Apply dictionary word replacements for natural phonetics
    for regex, replacement in COMPILED_PATTERNS:
        result = regex.sub(replacement, result)

    return result

if __name__ == "__main__":
    import sys
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass
    sample = "Hey Noaman, maine data compress kar diya hai! 73% memory bachi hai aur phone number 9876543210 hai. Option 1 try karo."
    print("BEFORE:", sample)
    print("AFTER :", normalize_hinglish(sample))

