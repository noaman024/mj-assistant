package com.mj.assistant.core

/**
 * Ported Hinglish Pronunciation Normalizer for Android
 * Converts Roman Hinglish, technical acronyms, and names into natural phonetics
 * for Android TTS and Edge-TTS synthesis.
 */
object HinglishNormalizer {

    private val REPLACEMENTS = listOf(
        // Names & Assistant
        Regex("\\bnoaman\\b", RegexOption.IGNORE_CASE) to "नोमान",
        Regex("\\bnoman\\b", RegexOption.IGNORE_CASE) to "नोमान",
        Regex("\\bmj\\b", RegexOption.IGNORE_CASE) to "एम.जे.",

        // Tech Acronyms (Crucial: prevents RAM being read as 'Lord Ram')
        Regex("\\bram\\b", RegexOption.IGNORE_CASE) to "रैम",
        Regex("\\bcpu\\b", RegexOption.IGNORE_CASE) to "सी.पी.यू.",
        Regex("\\bgpu\\b", RegexOption.IGNORE_CASE) to "जी.पी.यू.",
        Regex("\\bpc\\b", RegexOption.IGNORE_CASE) to "पी.सी.",
        Regex("\\bgb\\b", RegexOption.IGNORE_CASE) to "जी.बी.",
        Regex("\\bmb\\b", RegexOption.IGNORE_CASE) to "एम.बी.",
        Regex("\\bwifi\\b|\\bwi-fi\\b", RegexOption.IGNORE_CASE) to "वाई-फ़ाई",
        Regex("\\bsms\\b", RegexOption.IGNORE_CASE) to "एस.एम.एस.",
        Regex("\\bwhatsapp\\b", RegexOption.IGNORE_CASE) to "व्हाट्सएप",
        Regex("\\byoutube\\b", RegexOption.IGNORE_CASE) to "यूट्यूब",

        // Pronouns & Modals
        Regex("\\bmain\\b|\\bmai\\b", RegexOption.IGNORE_CASE) to "मैं",
        Regex("\\bmaine\\b", RegexOption.IGNORE_CASE) to "मैंने",
        Regex("\\baap\\b", RegexOption.IGNORE_CASE) to "आप",
        Regex("\\btum\\b", RegexOption.IGNORE_CASE) to "तुम",
        Regex("\\baapka\\b", RegexOption.IGNORE_CASE) to "आपका",
        Regex("\\baapki\\b", RegexOption.IGNORE_CASE) to "आपकी",
        Regex("\\baapke\\b", RegexOption.IGNORE_CASE) to "आपके",
        Regex("\\bmera\\b", RegexOption.IGNORE_CASE) to "मेरा",
        Regex("\\bmeri\\b", RegexOption.IGNORE_CASE) to "मेरी",
        Regex("\\bmere\\b", RegexOption.IGNORE_CASE) to "मेरे",
        Regex("\\bmujhe\\b", RegexOption.IGNORE_CASE) to "मुझे",

        // Auxiliaries & Verbs
        Regex("\\bhu\\b|\\bhoon\\b|\\bhun\\b", RegexOption.IGNORE_CASE) to "हूँ",
        Regex("\\bhai\\b", RegexOption.IGNORE_CASE) to "है",
        Regex("\\bhain\\b", RegexOption.IGNORE_CASE) to "हैं",
        Regex("\\bho\\b", RegexOption.IGNORE_CASE) to "हो",
        Regex("\\btheek\\b|\\bthik\\b", RegexOption.IGNORE_CASE) to "ठीक",
        Regex("\\bkaro\\b|\\bkro\\b", RegexOption.IGNORE_CASE) to "करो",
        Regex("\\bkarna\\b", RegexOption.IGNORE_CASE) to "करना",
        Regex("\\bkar\\b", RegexOption.IGNORE_CASE) to "कर",
        Regex("\\bkiya\\b", RegexOption.IGNORE_CASE) to "किया",
        Regex("\\bdiya\\b", RegexOption.IGNORE_CASE) to "दिया",
        Regex("\\bdi\\b", RegexOption.IGNORE_CASE) to "दी",
        Regex("\\bli\\b", RegexOption.IGNORE_CASE) to "ली",
        Regex("\\bgaya\\b", RegexOption.IGNORE_CASE) to "गया",
        Regex("\\bgayi\\b", RegexOption.IGNORE_CASE) to "गयी",
        Regex("\\braha\\b", RegexOption.IGNORE_CASE) to "रहा",
        Regex("\\brahi\\b", RegexOption.IGNORE_CASE) to "रही",
        Regex("\\bbhejo\\b", RegexOption.IGNORE_CASE) to "भेजो",
        Regex("\\bbhejna\\b", RegexOption.IGNORE_CASE) to "भेजना",
        Regex("\\bnahi\\b|\\bnhi\\b", RegexOption.IGNORE_CASE) to "नहीं",
        Regex("\\bhaan\\b|\\bha\\b", RegexOption.IGNORE_CASE) to "हाँ",
        Regex("\\bkya\\b", RegexOption.IGNORE_CASE) to "क्या",
        Regex("\\bchal\\b", RegexOption.IGNORE_CASE) to "चल",
        Regex("\\bka\\b", RegexOption.IGNORE_CASE) to "का",
        Regex("\\bki\\b", RegexOption.IGNORE_CASE) to "की",
        Regex("\\bke\\b", RegexOption.IGNORE_CASE) to "के",
        Regex("\\bko\\b", RegexOption.IGNORE_CASE) to "को",
        Regex("\\bse\\b", RegexOption.IGNORE_CASE) to "से",
        Regex("\\bpar\\b|\\bpe\\b", RegexOption.IGNORE_CASE) to "पर",
        Regex("\\bme\\b|\\bmein\\b", RegexOption.IGNORE_CASE) to "में",
        Regex("\\baur\\b", RegexOption.IGNORE_CASE) to "और",
        Regex("\\bekdum\\b", RegexOption.IGNORE_CASE) to "एकदम"
    )

    fun normalize(text: String): String {
        var result = text
        // Convert percentages: 90% -> 90 प्रतिशत
        result = result.replace(Regex("(\\d+)\\s*%"), "$1 प्रतिशत")

        for ((regex, replacement) in REPLACEMENTS) {
            result = result.replace(regex, replacement)
        }
        return result
    }
}
