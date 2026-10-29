"""
i18n.py — one-switch language change for the whole app.

How it works
------------
The app's original text is Hinglish. `install()` wraps the Streamlit widgets/text functions once, and at
call time looks up the label/body in TABLE for the language the *current session* picked
(st.session_state["ui_lang"]). Strings that are not in TABLE are shown as written, so nothing breaks.
Option lists are translated for display only (format_func) — their real values never change.

Add a language : add a code to LANGS and a column to every row in TABLE (or only the rows you care about).
Add a string   : append (hinglish_text, english_text, hindi_text) to TABLE. Use None for "same as source".
"""
import functools

import streamlit as st

LANGS = {"Hinglish": "hg", "English": "en", "हिन्दी": "hi"}
DEFAULT = "hg"

# (source text as written in app.py,  English,  Hindi)
TABLE = [
    # ── sidebar ──
    ("### ⚙️ Quiz Settings", None, "### ⚙️ क्विज़ सेटिंग्स"),
    ("Questions", None, "प्रश्नों की संख्या"),
    ("10 se zyada sawal batches me bante hain, thoda time lag sakta hai.", "Over 10 questions are made in batches, so it can take a little longer.", "10 से ज़्यादा प्रश्न बैच में बनते हैं, थोड़ा समय लग सकता है।"),
    ("Difficulty", None, "कठिनाई"),
    ("Easy", None, "आसान"),
    ("Medium", None, "मध्यम"),
    ("Hard", None, "कठिन"),
    ("🎚️ Adaptive difficulty", None, "🎚️ अनुकूल कठिनाई"),
    ("Sahi karte jao to sawal mushkil, galat par aasaan hote jayenge.", "Questions get harder when you answer right and easier when you miss.", "सही करते जाओगे तो प्रश्न कठिन, गलत पर आसान होते जाएँगे।"),
    ("Question types", None, "प्रश्नों के प्रकार"),
    ("Language", "Quiz language", "क्विज़ की भाषा"),
    ("Hindi", None, "हिन्दी"),
    ("Mode", None, "मोड"),
    ("Practice: har sawal ke baad turant answer.\nExam: result end me.\nSurvival: sirf 3 lives — 3 galat answer par game over!",
     "Practice: instant answer after every question.\nExam: result at the end.\nSurvival: only 3 lives — 3 wrong answers and it's game over!",
     "प्रैक्टिस: हर प्रश्न के बाद तुरंत उत्तर।\nएग्ज़ाम: परिणाम अंत में।\nसर्वाइवल: सिर्फ़ 3 जीवन — 3 गलत उत्तर पर गेम ओवर!"),
    ("Practice", None, "प्रैक्टिस"),
    ("Exam", None, "एग्ज़ाम"),
    ("Survival", None, "सर्वाइवल"),
    ("**⏱️ Timer**", None, "**⏱️ टाइमर**"),
    ("Timer type", None, "टाइमर का प्रकार"),
    ("Off", None, "बंद"),
    ("Har sawal par", "Per question", "हर प्रश्न पर"),
    ("Poore quiz ka", "Whole quiz", "पूरे क्विज़ का"),
    ("Seconds per sawal", "Seconds per question", "प्रति प्रश्न सेकंड"),
    ("Minutes (poore quiz ke)", "Minutes (whole quiz)", "मिनट (पूरे क्विज़ के)"),
    ("Custom", None, "कस्टम"),
    ("Custom seconds", None, "कस्टम सेकंड"),
    ("Custom minutes", None, "कस्टम मिनट"),
    ("Time khatam hote hi answer auto-submit ho jata hai.", "The answer is submitted automatically when time runs out.", "समय खत्म होते ही उत्तर अपने आप जमा हो जाता है।"),
    ("Timer ke liye Streamlit ≥ 1.37 chahiye.", "The timer needs Streamlit ≥ 1.37.", "टाइमर के लिए Streamlit ≥ 1.37 चाहिए।"),
    ("**🎯 Marking**", None, "**🎯 अंकन**"),
    ("Marks per sahi answer", "Marks per correct answer", "प्रति सही उत्तर अंक"),
    ("Negative marking (galat par)", "Negative marking (on wrong)", "नेगेटिव मार्किंग (गलत पर)"),
    ("Galat answer par sahi-marks ka itna hissa katega. Skip par 0. Short answer me partial marks milte hain, negative nahi.",
     "A wrong answer loses this fraction of the marks. Skipped = 0. Short answers get partial marks, never negative.",
     "गलत उत्तर पर सही-अंकों का इतना हिस्सा कटेगा। छोड़ने पर 0। छोटे उत्तर में आंशिक अंक मिलते हैं, नेगेटिव नहीं।"),
    ("Nahi", "None", "नहीं"),
    ("🔊 Awaaz & Look", "🔊 Sound & Look", "🔊 आवाज़ और लुक"),
    ("Sound effects", None, "साउंड इफ़ेक्ट"),
    ("Sawal khud padhkar sunao", "Read questions aloud automatically", "प्रश्न खुद पढ़कर सुनाओ"),
    ("Agar awaaz na aaye to pehle page par ek click karo ya 🔊 button dabao.", "If there's no sound, click once on the page or press the 🔊 button.", "अगर आवाज़ न आए तो पहले पेज पर एक क्लिक करो या 🔊 बटन दबाओ।"),
    ("Bolne ki speed", "Speaking speed", "बोलने की गति"),
    ("☀️ Light mode", None, "☀️ लाइट मोड"),
    ("Advanced", None, "उन्नत"),
    ("AI model", None, "AI मॉडल"),
    ("120b = sabse accurate. 8b-instant = sabse fast.", "120b = most accurate. 8b-instant = fastest.", "120b = सबसे सटीक। 8b-instant = सबसे तेज़।"),
    ("### 🔖 Saved questions", None, "### 🔖 सहेजे हुए प्रश्न"),
    ("Quiz ke dauran 🔖 dabao, sawal yahan save ho jayega.", "Press 🔖 during a quiz and the question is saved here.", "क्विज़ के दौरान 🔖 दबाओ, प्रश्न यहाँ सहेज जाएगा।"),
    ("📇 Flashcards se padho", "📇 Study with flashcards", "📇 फ़्लैशकार्ड से पढ़ो"),
    ("### 🏆 Meri History", "### 🏆 My History", "### 🏆 मेरी हिस्ट्री"),
    ("Clear history", None, "हिस्ट्री साफ़ करो"),
    ("Abhi koi quiz nahi diya. Pehla quiz banao!", "No quiz taken yet. Make your first one!", "अभी कोई क्विज़ नहीं दिया। पहला क्विज़ बनाओ!"),
    ("### 💾 Progress backup", None, "### 💾 प्रोग्रेस बैकअप"),
    ("Tumhara XP, history aur saved sawal account me apne aap save hote hain. Chaho to yahan file backup bhi rakh sakte ho.",
     "Your XP, history and saved questions are saved to your account automatically. You can also keep a file backup here.",
     "आपका XP, हिस्ट्री और सहेजे प्रश्न आपके अकाउंट में अपने आप सेव होते हैं। यहाँ फ़ाइल बैकअप भी रख सकते हैं।"),
    ("⬇️ Progress save karo", "⬇️ Download progress", "⬇️ प्रोग्रेस डाउनलोड करो"),
    ("Progress load karo", "Load progress", "प्रोग्रेस लोड करो"),
    # ── tabs / setup ──
    ("🧠 Quiz Arena", None, "🧠 क्विज़ एरीना"),
    ("🏛️ Govt Exam PYQs", None, "🏛️ सरकारी परीक्षा PYQ"),
    ("🔍 Doubt Solver", None, "🔍 डाउट सॉल्वर"),
    ("Content kahan se aayega?", "Where will the content come from?", "सामग्री कहाँ से आएगी?"),
    ("💡 Topic", None, "💡 टॉपिक"),
    ("📄 PDF", None, "📄 PDF"),
    ("🖼️ Photo / Camera", None, "🖼️ फ़ोटो / कैमरा"),
    ("📝 Notes", None, "📝 नोट्स"),
    ("Kis topic par quiz chahiye?", "Which topic do you want a quiz on?", "किस टॉपिक पर क्विज़ चाहिए?"),
    ("e.g. Machine Learning basics, Indian Constitution, Python lists…", None, "जैसे: मशीन लर्निंग बेसिक्स, भारतीय संविधान, Python lists…"),
    ("Quick picks", None, "त्वरित चुनाव"),
    ("PDF upload karo", "Upload a PDF", "PDF अपलोड करो"),
    ("Page range", None, "पेज रेंज"),
    ("Photo upload karo ya camera se seedha click karo.", "Upload a photo or click one directly with the camera.", "फ़ोटो अपलोड करो या कैमरे से सीधे क्लिक करो।"),
    ("Photo mode", None, "फ़ोटो मोड"),
    ("📁 Upload File", None, "📁 फ़ाइल अपलोड"),
    ("📸 Live Camera Click", None, "📸 लाइव कैमरा क्लिक"),
    ("Photo upload karo", "Upload a photo", "फ़ोटो अपलोड करो"),
    ("Live photo click karo", "Take a live photo", "लाइव फ़ोटो खींचो"),
    ("Apne notes / article yahan paste karo", "Paste your notes / article here", "अपने नोट्स / लेख यहाँ पेस्ट करो"),
    ("Chapter ka text, notes, ya koi bhi article…", "Chapter text, notes or any article…", "अध्याय का टेक्स्ट, नोट्स या कोई भी लेख…"),
    ("✨ Quiz banao", "✨ Make quiz", "✨ क्विज़ बनाओ"),
    ("Pehle topic likho, photo upload/click karo ya notes paste karo.", "First write a topic, upload/click a photo or paste notes.", "पहले टॉपिक लिखो, फ़ोटो अपलोड/क्लिक करो या नोट्स पेस्ट करो।"),
    ("AI sawal bana raha hai…", "AI is making questions…", "AI प्रश्न बना रहा है…"),
    ("Sawal ban rahe hain…", "Making questions…", "प्रश्न बन रहे हैं…"),
    ("Valid sawal nahi ban paye. Dobara try karo.", "Couldn't make valid questions. Please try again.", "सही प्रश्न नहीं बन पाए। दोबारा कोशिश करो।"),
    ("AI ka response samajh nahi aaya. Dobara try karo ya doosra model chuno.", "Couldn't understand the AI response. Try again or pick another model.", "AI का जवाब समझ नहीं आया। दोबारा कोशिश करो या दूसरा मॉडल चुनो।"),
    ("Is PDF se text nahi nikla (scanned lagta hai). Uske page ki **photo** lekar try karo.", "No text found in this PDF (looks scanned). Try a **photo** of the page.", "इस PDF से टेक्स्ट नहीं निकला (स्कैन लगता है)। उस पेज की **फ़ोटो** लेकर देखो।"),
    ("Photo 15 MB se badi hai. Chhoti photo use karo.", "The photo is over 15 MB. Use a smaller one.", "फ़ोटो 15 MB से बड़ी है। छोटी फ़ोटो इस्तेमाल करो।"),
    ("Photo compress hone ke baad bhi bahut badi hai. Kam resolution ki photo lo.", "Still too big after compression. Use a lower-resolution photo.", "कंप्रेस होने के बाद भी बहुत बड़ी है। कम रेज़ोल्यूशन की फ़ोटो लो।"),
    # ── govt exams ──
    ("### 🏛️ Govt & Entrance Exam Practice", None, "### 🏛️ सरकारी एवं प्रवेश परीक्षा अभ्यास"),
    ("SSC, RRB, Banking, UP Police, UPSC, UP CNET, NEET aur JEE. Marking har exam ke hisaab se lagti hai (galat par negative bhi). Apne dataset ke **asli purane sawal** par 📜 tag aata hai; AI ke sawal exam-pattern practice hote hain, asli paper ke nahi.",
     "SSC, RRB, Banking, UP Police, UPSC, UP CNET, NEET and JEE. Marking follows each exam (negative on wrong answers too). **Real past questions** from your dataset get a 📜 tag; AI questions are exam-pattern practice, not real papers.",
     "SSC, RRB, बैंकिंग, UP पुलिस, UPSC, UP CNET, NEET और JEE। अंकन हर परीक्षा के अनुसार लगता है (गलत पर नेगेटिव भी)। आपके डेटासेट के **असली पुराने प्रश्नों** पर 📜 टैग आता है; AI के प्रश्न परीक्षा-पैटर्न अभ्यास हैं, असली पेपर के नहीं।"),
    ("Target exam", None, "लक्ष्य परीक्षा"),
    ("Subject", None, "विषय"),
    ("Year (optional)", None, "वर्ष (वैकल्पिक)"),
    ("Is filter ke liye dataset me PYQ nahi hain — AI exam-pattern wale practice sawal banayega (asli paper ke nahi).", "No PYQs in your dataset for this filter — AI will make exam-pattern practice questions (not real paper questions).", "इस फ़िल्टर के लिए डेटासेट में PYQ नहीं हैं — AI परीक्षा-पैटर्न के अभ्यास प्रश्न बनाएगा (असली पेपर के नहीं)।"),
    ("Dataset me kam pade to AI se bharo", "Fill the rest with AI if the dataset runs short", "डेटासेट में कम पड़े तो AI से भरो"),
    ("Marking scheme", None, "अंकन योजना"),
    ("📋 Official (exam jaisi)", "📋 Official (as in the exam)", "📋 आधिकारिक (परीक्षा जैसी)"),
    ("⚙️ Sidebar wali", "⚙️ From sidebar", "⚙️ साइडबार वाली"),
    ("Is option me sidebar wali marking lagegi.", "This option uses the sidebar marking.", "इस विकल्प में साइडबार वाली मार्किंग लगेगी।"),
    ("Notification me alag ho to marking adjust karo", "Adjust marking if your notification differs", "नोटिफ़िकेशन में अलग हो तो मार्किंग बदलो"),
    ("Negative marking", None, "नेगेटिव मार्किंग"),
    ("Numerical questions par bhi negative lagao", "Apply negative marking to numerical questions too", "संख्यात्मक प्रश्नों पर भी नेगेटिव लगाओ"),
    ("📝 Full mock test (exam jaisa pattern + timer)", "📝 Full mock test (exam pattern + timer)", "📝 पूरा मॉक टेस्ट (परीक्षा जैसा पैटर्न + टाइमर)"),
    ("Mock size", None, "मॉक का आकार"),
    ("Full", None, "पूरा"),
    ("Half (50%)", None, "आधा (50%)"),
    ("Quarter (25%)", None, "चौथाई (25%)"),
    ("⏳ Itne sawal AI se banane me kuch minute lag sakte hain (rate limit lag jaye to Half/Quarter size try karo).", "⏳ Making this many questions with AI can take a few minutes (if you hit a rate limit, try Half/Quarter size).", "⏳ इतने प्रश्न AI से बनाने में कुछ मिनट लग सकते हैं (रेट लिमिट लगे तो आधा/चौथाई आकार आज़माओ)।"),
    ("➕ Apna PYQ dataset jodo (JSON / CSV)", "➕ Add your own PYQ dataset (JSON / CSV)", "➕ अपना PYQ डेटासेट जोड़ो (JSON / CSV)"),
    ("📄 Template (JSON)", None, "📄 टेम्पलेट (JSON)"),
    ("PYQ file", None, "PYQ फ़ाइल"),
    ("🗑️ Uploaded PYQ hatao", "🗑️ Remove uploaded PYQs", "🗑️ अपलोड किए PYQ हटाओ"),
    ("Sawal taiyaar ho rahe hain…", "Preparing questions…", "प्रश्न तैयार हो रहे हैं…"),
    # ── doubt solver ──
    ("### 🔍 AI Doubt Solver", None, "### 🔍 AI डाउट सॉल्वर"),
    ("Doubt poochho (text, photo, camera ya PDF). Jawab word-by-word aata hai, aur tum follow-up sawal bhi pooch sakte ho.",
     "Ask a doubt (text, photo, camera or PDF). The answer streams word by word and you can ask follow-ups.",
     "डाउट पूछो (टेक्स्ट, फ़ोटो, कैमरा या PDF)। जवाब शब्द-दर-शब्द आता है और फ़ॉलो-अप भी पूछ सकते हो।"),
    ("Jawab ki bhasha", "Answer language", "उत्तर की भाषा"),
    ("Style", None, "शैली"),
    ("Doubt kaise poochna hai?", "How do you want to ask?", "डाउट कैसे पूछना है?"),
    ("📝 Text", None, "📝 टेक्स्ट"),
    ("📸 Live Camera", None, "📸 लाइव कैमरा"),
    ("🖼️ Photo Upload", None, "🖼️ फ़ोटो अपलोड"),
    ("Apna doubt yahan likho", "Write your doubt here", "अपना डाउट यहाँ लिखो"),
    ("e.g. Binary Search Tree me insertion kaise hota hai? Example ke saath samjhao.", "e.g. How does insertion work in a Binary Search Tree? Explain with an example.", "जैसे: Binary Search Tree में insertion कैसे होता है? उदाहरण के साथ समझाओ।"),
    ("📸 Browser me camera allow karo, question ki saaf photo lo (seedhi, achhi roshni me). Phone me back camera chahiye to browser ka camera-switch use karo.",
     "📸 Allow the camera in your browser and take a clear, straight photo in good light. For the back camera on a phone, use the browser's camera switch.",
     "📸 ब्राउज़र में कैमरा अनुमति दो और अच्छी रोशनी में प्रश्न की सीधी, साफ़ फ़ोटो लो। फ़ोन में बैक कैमरा चाहिए तो ब्राउज़र का कैमरा-स्विच इस्तेमाल करो।"),
    ("Question ki live photo click karo", "Take a live photo of the question", "प्रश्न की लाइव फ़ोटो खींचो"),
    ("Koi extra instruction? (optional)", "Any extra instruction? (optional)", "कोई अतिरिक्त निर्देश? (वैकल्पिक)"),
    ("e.g. Sirf Q3 solve karo", "e.g. Solve only Q3", "जैसे: सिर्फ़ Q3 हल करो"),
    ("PDF me se kya poochna hai?", "What do you want to ask from the PDF?", "PDF में से क्या पूछना है?"),
    ("e.g. Is chapter ka summary do", "e.g. Summarise this chapter", "जैसे: इस अध्याय का सारांश दो"),
    ("PDF ke pehle 5 pages load ho gaye.", "The first 5 pages of the PDF are loaded.", "PDF के पहले 5 पेज लोड हो गए।"),
    ("PDF se text nahi nikla. Page ki photo upload karo.", "No text found in the PDF. Upload a photo of the page.", "PDF से टेक्स्ट नहीं निकला। पेज की फ़ोटो अपलोड करो।"),
    ("💡 Samjhao", "💡 Explain", "💡 समझाओ"),
    ("Pehle doubt likho ya photo do.", "First write a doubt or give a photo.", "पहले डाउट लिखो या फ़ोटो दो।"),
    ("🔁 Jawab dobara generate karo", "🔁 Regenerate answer", "🔁 उत्तर दोबारा बनाओ"),
    ("Follow-up poochho", "Ask a follow-up", "फ़ॉलो-अप पूछो"),
    ("e.g. Ek aur example se samjhao / Is step me ye kyun hua?", "e.g. Explain with another example / Why did this step happen?", "जैसे: एक और उदाहरण से समझाओ / इस स्टेप में ऐसा क्यों हुआ?"),
    ("Bhejo ➤", "Send ➤", "भेजो ➤"),
    ("🧹 Naya doubt", "🧹 New doubt", "🧹 नया डाउट"),
    ("📝 Is par quiz banao", "📝 Make a quiz on this", "📝 इस पर क्विज़ बनाओ"),
    ("⬇️ Notes (.md)", None, "⬇️ नोट्स (.md)"),
    ("Soch raha hoon…", "Thinking…", "सोच रहा हूँ…"),
    # ── quiz stage ──
    ("Apna answer chuno", "Choose your answer", "अपना उत्तर चुनो"),
    ("Ek se zyada sahi options chuno", "Choose all correct options", "एक से ज़्यादा सही विकल्प चुनो"),
    ("Numerical answer", None, "संख्यात्मक उत्तर"),
    ("Sirf number likho, jaise 12.5", "Write only a number, like 12.5", "सिर्फ़ संख्या लिखो, जैसे 12.5"),
    ("Khali jagah bharo", "Fill in the blank", "खाली जगह भरो"),
    ("Apna answer type karo…", "Type your answer…", "अपना उत्तर टाइप करो…"),
    ("Apna answer likho (1-3 line)", "Write your answer (1-3 lines)", "अपना उत्तर लिखो (1-3 पंक्तियाँ)"),
    ("✖ Quiz chhodo", "✖ Quit quiz", "✖ क्विज़ छोड़ो"),
    ("💡 Hint (−5 XP)", None, "💡 संकेत (−5 XP)"),
    ("🧠 Aur detail me samjhao", "🧠 Explain in more detail", "🧠 और विस्तार से समझाओ"),
    ("⬅️ Back", None, "⬅️ पीछे"),
    ("Check answer", None, "उत्तर जाँचो"),
    ("Skip ⏭️", None, "छोड़ो ⏭️"),
    ("💀 Saari lives khatam! Game over.", "💀 All lives are gone! Game over.", "💀 सारे जीवन खत्म! गेम ओवर।"),
    ("🧭 Question palette (kisi bhi sawal par jao)", "🧭 Question palette (jump to any question)", "🧭 प्रश्न पैलेट (किसी भी प्रश्न पर जाओ)"),
    ("✅ = answer diya hua · baaki khali. Neela button = abhi wala sawal.", "✅ = answered · the rest are empty. Blue button = current question.", "✅ = उत्तर दिया · बाकी खाली। नीला बटन = अभी वाला प्रश्न।"),
    ("⏰ Quiz ka total time khatam ho gaya — bache hue sawal skip maane gaye.", "⏰ The quiz time is over — remaining questions count as skipped.", "⏰ क्विज़ का कुल समय खत्म — बचे प्रश्न छोड़े हुए माने गए।"),
    ("AI tumhara answer check kar raha hai…", "AI is checking your answer…", "AI तुम्हारा उत्तर जाँच रहा है…"),
    ("Short answers check ho rahe hain…", "Checking short answers…", "छोटे उत्तर जाँचे जा रहे हैं…"),
    ("## 📇 Flashcards", None, "## 📇 फ़्लैशकार्ड"),
    ("⬅️ Pichhla", "⬅️ Previous", "⬅️ पिछला"),
    ("Agla ➡️", "Next ➡️", "अगला ➡️"),
    ("← Wapas jao", "← Go back", "← वापस जाओ"),
    ("Kitne aur sawal?", "How many more questions?", "और कितने प्रश्न?"),
    ("Naye sawal ban rahe hain…", "Making new questions…", "नए प्रश्न बन रहे हैं…"),
    ("Naye sawal nahi ban paye.", "Couldn't make new questions.", "नए प्रश्न नहीं बन पाए।"),
    ("Naye sawal nahi ban paye. Dobara try karo.", "Couldn't make new questions. Please try again.", "नए प्रश्न नहीं बन पाए। दोबारा कोशिश करो।"),
    ("🔁 Naya quiz", "🔁 New quiz", "🔁 नया क्विज़"),
    ("🎯 Sirf galat dobara", "🎯 Redo only wrong ones", "🎯 सिर्फ़ गलत दोबारा"),
    ("Sirf galat/skip kiye hue sawal phir se solve karo", "Solve only the wrong/skipped questions again", "सिर्फ़ गलत/छोड़े हुए प्रश्न फिर से हल करो"),
    ("🔄 Wahi quiz phir se", "🔄 Same quiz again", "🔄 वही क्विज़ फिर से"),
    ("🆕 Naye sawal (same source)", "🆕 New questions (same source)", "🆕 नए प्रश्न (वही स्रोत)"),
    ("📇 Is quiz ke flashcards", "📇 Flashcards of this quiz", "📇 इस क्विज़ के फ़्लैशकार्ड"),
    ("### 📊 Topic-wise performance", None, "### 📊 टॉपिक-वार प्रदर्शन"),
    ("🧭 AI study plan banao", "🧭 Make AI study plan", "🧭 AI स्टडी प्लान बनाओ"),
    ("Study plan ban raha hai…", "Making your study plan…", "स्टडी प्लान बन रहा है…"),
    ("### 🔍 Review", None, "### 🔍 समीक्षा"),
    ("Ye sawal skip hua / time khatam ho gaya / game over ho gaya.", "This question was skipped / time ran out / game over.", "यह प्रश्न छोड़ा गया / समय खत्म हो गया / गेम ओवर हो गया।"),
    ("### 📥 Download", None, "### 📥 डाउनलोड"),
    ("Report (HTML)", None, "रिपोर्ट (HTML)"),
    ("Results (CSV)", None, "परिणाम (CSV)"),
    ("Quiz (JSON)", None, "क्विज़ (JSON)"),
    ("API key nahi mili. Streamlit Cloud ke **Secrets** me `GROQ_API_KEY` add karein.", "API key not found. Add `GROQ_API_KEY` in your Streamlit Cloud **Secrets**.", "API key नहीं मिली। Streamlit Cloud के **Secrets** में `GROQ_API_KEY` जोड़ें।"),
]

# New strings used by the login / account UI (looked up by key with t()).
KEYS = {
    "app_tag": {
        "hg": "Topic, PDF ya notes ki photo do — AI turant quiz banata hai. Awaaz, timer, lives, XP aur badges ke saath seekho.",
        "en": "Give a topic, PDF or a photo of your notes — AI makes a quiz instantly. Learn with sound, timers, lives, XP and badges.",
        "hi": "टॉपिक, PDF या नोट्स की फ़ोटो दो — AI तुरंत क्विज़ बनाता है। आवाज़, टाइमर, जीवन, XP और बैज के साथ सीखो।",
    },
    "step1": {"hg": "Content chuno", "en": "Pick content", "hi": "सामग्री चुनो"},
    "step2": {"hg": "Quiz khelo", "en": "Play quiz", "hi": "क्विज़ खेलो"},
    "step3": {"hg": "Result dekho", "en": "See result", "hi": "परिणाम देखो"},
    "login_title": {"hg": "🔐 Login karo", "en": "🔐 Log in", "hi": "🔐 लॉगिन करो"},
    "login_sub": {
        "hg": "Email ya mobile number se OTP lo. Tumhari history, XP aur saved sawal tumhare account me save rahenge.",
        "en": "Get an OTP on your email or mobile number. Your history, XP and saved questions stay in your account.",
        "hi": "ईमेल या मोबाइल नंबर पर OTP लो। आपकी हिस्ट्री, XP और सहेजे प्रश्न आपके अकाउंट में सुरक्षित रहेंगे।",
    },
    "via_email": {"hg": "📧 Email", "en": "📧 Email", "hi": "📧 ईमेल"},
    "via_phone": {"hg": "📱 Mobile", "en": "📱 Mobile", "hi": "📱 मोबाइल"},
    "email_lbl": {"hg": "Email address", "en": "Email address", "hi": "ईमेल पता"},
    "phone_lbl": {"hg": "Mobile number (India ke liye 10 digit)", "en": "Mobile number (10 digits for India)", "hi": "मोबाइल नंबर (भारत के लिए 10 अंक)"},
    "send_otp": {"hg": "OTP bhejo", "en": "Send OTP", "hi": "OTP भेजो"},
    "otp_lbl": {"hg": "6 digit OTP", "en": "6-digit OTP", "hi": "6 अंकों का OTP"},
    "verify": {"hg": "Verify karke login karo", "en": "Verify and log in", "hi": "सत्यापित करके लॉगिन करो"},
    "change_id": {"hg": "← Doosra email/number", "en": "← Use a different email/number", "hi": "← दूसरा ईमेल/नंबर"},
    "resend": {"hg": "OTP dobara bhejo", "en": "Resend OTP", "hi": "OTP दोबारा भेजो"},
    "sent_to": {"hg": "OTP bheja gaya: {to}", "en": "OTP sent to: {to}", "hi": "OTP भेजा गया: {to}"},
    "m_bad_id": {"hg": "Sahi email / mobile number daalo.", "en": "Enter a valid email / mobile number.", "hi": "सही ईमेल / मोबाइल नंबर डालो।"},
    "m_wait": {"hg": "Thoda ruko — naya OTP 30 second baad hi mil sakta hai.", "en": "Please wait — a new OTP can be sent after 30 seconds.", "hi": "थोड़ा रुको — नया OTP 30 सेकंड बाद ही मिलेगा।"},
    "m_too_many": {"hg": "Bahut zyada OTP request ho gayi. 1 ghante baad try karo.", "en": "Too many OTP requests. Try again in an hour.", "hi": "बहुत ज़्यादा OTP अनुरोध हो गए। 1 घंटे बाद कोशिश करो।"},
    "m_not_configured": {"hg": "OTP service abhi set nahi hai. App admin ko SMTP / SMS settings Secrets me daalni hongi.", "en": "OTP service isn't set up yet. The app admin must add SMTP / SMS settings in Secrets.", "hi": "OTP सेवा अभी सेट नहीं है। ऐप एडमिन को Secrets में SMTP / SMS सेटिंग डालनी होंगी।"},
    "m_send_failed": {"hg": "OTP bhej nahi paye. Thodi der baad dobara try karo.", "en": "Couldn't send the OTP. Please try again shortly.", "hi": "OTP भेज नहीं पाए। थोड़ी देर बाद दोबारा कोशिश करो।"},
    "m_expired": {"hg": "OTP expire ho gaya ya mila nahi. Naya OTP mangao.", "en": "The OTP expired or wasn't found. Request a new one.", "hi": "OTP की समय-सीमा खत्म हो गई या मिला नहीं। नया OTP मँगाओ।"},
    "m_wrong": {"hg": "OTP galat hai. Dobara dekho.", "en": "Wrong OTP. Please check again.", "hi": "OTP गलत है। दोबारा देखो।"},
    "m_locked": {"hg": "Bahut galat koshish. Naya OTP mangao.", "en": "Too many wrong attempts. Request a new OTP.", "hi": "बहुत गलत कोशिशें। नया OTP मँगाओ।"},
    "dev_otp": {"hg": "🛠️ DEV mode — OTP: {code} (production me ye band rakho)", "en": "🛠️ DEV mode — OTP: {code} (turn this off in production)", "hi": "🛠️ DEV मोड — OTP: {code} (प्रोडक्शन में इसे बंद रखो)"},
    "app_language": {"hg": "🌐 App ki bhasha", "en": "🌐 App language", "hi": "🌐 ऐप की भाषा"},
    "account": {"hg": "### 👤 Mera account", "en": "### 👤 My account", "hi": "### 👤 मेरा अकाउंट"},
    "logout": {"hg": "🚪 Logout", "en": "🚪 Log out", "hi": "🚪 लॉगआउट"},
    "synced": {"hg": "☁️ History account me save ho rahi hai.", "en": "☁️ History is being saved to your account.", "hi": "☁️ हिस्ट्री आपके अकाउंट में सेव हो रही है।"},
    "toggle_tip": {"hg": "Sidebar kholo / band karo", "en": "Open / close sidebar", "hi": "साइडबार खोलो / बंद करो"},
}

_LOOKUP = {}
for _src, _en, _hi in TABLE:
    _LOOKUP[_src] = {"en": _en if _en is not None else _src, "hi": _hi if _hi is not None else _src}


def cur():
    try:
        return st.session_state.get("ui_lang", DEFAULT)
    except Exception:
        return DEFAULT


def tr(s):
    """Translate a source string for the current session language (unknown strings pass through)."""
    if not isinstance(s, str):
        return s
    lang = cur()
    if lang == DEFAULT:
        return s
    row = _LOOKUP.get(s)
    return row[lang] if row and lang in row else s


def t(key, **fmt):
    row = KEYS[key]
    txt = row.get(cur()) or row["hg"]
    return txt.format(**fmt) if fmt else txt


# ───────────────────────── installing the wrappers ─────────────────────────
_TEXT_FIRST = (
    "markdown", "caption", "success", "info", "warning", "error", "subheader", "header", "title",
    "button", "download_button", "form_submit_button", "toggle", "checkbox", "slider", "select_slider",
    "selectbox", "radio", "multiselect", "text_input", "text_area", "number_input", "file_uploader",
    "camera_input", "expander", "spinner", "progress",
)
_OPTION_WIDGETS = ("selectbox", "radio", "multiselect", "select_slider")
_STR_KWARGS = ("help", "placeholder", "text", "label")


def _fmt_func(o):
    return tr(str(o))


def _wrap(fn, name, is_method):
    @functools.wraps(fn)
    def inner(*args, **kwargs):
        if cur() != DEFAULT:
            args = list(args)
            pos = 1 if is_method else 0
            if name == "tabs":
                if len(args) > pos and isinstance(args[pos], (list, tuple)):
                    args[pos] = [tr(x) for x in args[pos]]
            else:
                if len(args) > pos:
                    args[pos] = tr(args[pos])
                for k in _STR_KWARGS:
                    if isinstance(kwargs.get(k), str):
                        kwargs[k] = tr(kwargs[k])
                if name in _OPTION_WIDGETS and "format_func" not in kwargs and len(args) <= pos + 3:
                    kwargs["format_func"] = _fmt_func
        return fn(*args, **kwargs)

    inner._qf_wrapped = True
    return inner


def install():
    """Wrap Streamlit once per process. Safe to call on every rerun."""
    if getattr(st, "_qf_i18n_installed", False):
        return
    try:
        from streamlit.delta_generator import DeltaGenerator
    except Exception:
        DeltaGenerator = None
    for name in _TEXT_FIRST + ("tabs",):
        # module level (st.button, st.markdown …)
        try:
            f = getattr(st, name)
            if not getattr(f, "_qf_wrapped", False):
                setattr(st, name, _wrap(f, name, False))
        except Exception:
            pass
        # DeltaGenerator methods (col.button, st.sidebar.button, container.markdown …)
        if DeltaGenerator is not None:
            try:
                m = getattr(DeltaGenerator, name)
                if not getattr(m, "_qf_wrapped", False):
                    setattr(DeltaGenerator, name, _wrap(m, name, True))
            except Exception:
                pass
    st._qf_i18n_installed = True
