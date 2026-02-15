EN = {
    "the","a","an","and","or","but","if","then","else","so","to","of","in","on","at","for","with","as","by",
    "is","are","was","were","be","been","being","it","this","that","these","those","i","you","we","they","he","she",
    "my","your","our","their","from","not","do","does","did","can","could","should","would","will","just","more","most",
    "about","into","over","under","than","also", "okay","ok","dear","students","student","guys","let","lets","see","now","so","well",
    "like","actually","basically","literally","right","maybe","kind","sort","thing","things",
    "what","why","how","when","where","question","very","just","yeah","uh","um"
}

RU = {
    "и","а","но","или","если","то","это","эти","тот","та","те","в","на","у","к","по","из","для","с","со","как","что",
    "я","ты","мы","вы","они","он","она","оно","мой","твой","наш","ваш","их","не","да","нет","бы","же","ли","будет",
    "можно","нужно","надо","очень","тоже","ещё", "ну","так","вот","значит","короче","типа","сейчас","вообще","просто","очень","вопрос"
}

# very small basic list; expand later if you want
KK = {
    "және","мен","сен","сіз","біз","ол","олар","бұл","сол","осы","бір","үшін","сияқты","жоқ","иә","өте","да","де", 
    "туралы","ішінде","үстінде","астында", "енді","сонда","міне","жалпы","өте","сұрақ"
}

def get_stopwords(lang: str) -> set[str]:
    lang = (lang or "en").lower()
    if lang.startswith("ru"):
        return RU
    if lang.startswith("kk") or lang.startswith("kz"):
        return KK
    return EN
