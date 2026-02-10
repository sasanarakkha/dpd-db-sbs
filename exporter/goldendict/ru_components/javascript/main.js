document.addEventListener("click", function (event) {
    var target = event.target;
    const classNames = ["button", "dpd-button"]
    if (classNames.some(className => target.classList.contains(className))) {
        button_click(target);
        event.preventDefault();
    }
});

function button_click(el) {
    const target_id = el.getAttribute("data-target");
    var target = document.getElementById(target_id);

    if (target) {
        if (target.textContent.includes("loading...")) {
            loadData()
        };

        target.classList.toggle("hidden");
        if (el.classList.contains("close")) {
            var target_control = document.querySelector('a.button[data-target="' + target_id.replace('ru_', '') + '"]');
            if (!target_control) {
                target_control = document.querySelector('a.dpd-button[data-target="' + target_id.replace('ru_', '') + '"]');
            }
            if (target_control) {
                target_control.classList.toggle("active");
            }
        } else {
            el.classList.toggle("active");
        }
    }
};

document.addEventListener('DOMContentLoaded', function () {
    loadData()
});

function loadData() {
    var metaTags = document.querySelectorAll("meta[data_key]");
    var metaArray = Array.from(metaTags);
    metaArray.forEach(tag => {
        var dataKey = tag.getAttribute("data_key");
        var data = window[dataKey];
        if (dataKey.startsWith("data_")) {
            loadButtonContent(data)
        } else if (dataKey.startsWith("rootdata_")) {
            loadRootButtonContent(data)
        }
    });
};

//// load json data into buttons 

function loadButtonContent(data) {
    const lemmaTag = data.lemma.replace(/ /g, "_").replace(".", "_") // a 1.1 > a_1_1

    //// feedback

    const feedbackHTML = makeFeedback(data);
    const feedbackElement = document.getElementById(`ru_feedback_${lemmaTag}`)
    feedbackElement.innerHTML = feedbackHTML

    // frequency

    if (data.CstFreq != undefined) {
        const frequencyHTML = makeFrequency(data);
        const frequencyElement = document.getElementById(`ru_frequency_${lemmaTag}`)
        frequencyElement.innerHTML = frequencyElement.innerHTML.replace("frequency loading...", frequencyHTML)
    };

    //// family compounds

    if (
        data.family_compounds
        && data.family_compounds.length > 0
        && typeof family_compound_json !== "undefined"
    ) {
        const familyCompoundHtml = makeFamilyCompoundHtml(data)
        const familyCompoundElement = document.getElementById(`ru_family_compound_${lemmaTag}`)
        familyCompoundElement.innerHTML = familyCompoundHtml
    };

    //// family root

    if (data.family_root != ""
        && typeof family_root_json !== "undefined"
    ) {
        const fr = family_root_json[data.family_root];
        const familyRootHtml = makeFamilyRootHtml(data, fr, "lemma");
        const familyRootElement = document.getElementById(`ru_family_root_${lemmaTag}`);
        familyRootElement.innerHTML = familyRootHtml;
    };

    //// family idioms

    if (
        data.family_idioms
        && data.family_idioms.length > 0
        && typeof family_idiom_json !== "undefined"
    ) {
        const familyIdiomHtml = makeFamilyIdioms(data)
        const familyIdiomElement = document.getElementById(`ru_family_idiom_${lemmaTag}`)
        familyIdiomElement.innerHTML = familyIdiomHtml
    };

    //// family sets

    if (
        data.family_sets
        && data.family_sets.length > 0
        && typeof family_set_json !== "undefined"
    ) {
        const familySetHtml = makeFamilySets(data)
        const familySetElement = document.getElementById(`ru_family_set_${lemmaTag}`)
        familySetElement.innerHTML = familySetHtml
    };

    //// family word

    if (
        data.family_word
        && typeof family_word_json !== "undefined"
    ) {
        const familyWordHtml = makeFamilyWordHtml(data);
        const familyWordElement = document.getElementById(`ru_family_word_${lemmaTag}`)
        familyWordElement.innerHTML = familyWordHtml
    };
};

function loadRootButtonContent(data) {
    const familyRootDivs = document.querySelectorAll('div[id^="ru_family_root_"]');
    var familyRootArray = Array.from(familyRootDivs);
    familyRootArray.forEach(item => {
        const key_id = item.id
        const key_clean = item.id.replace("ru_family_root_", "").replace(/_/g, " ")
        const fr = family_root_json[key_clean]
        const link = item.id.replace("ru_family_root_", "").replace(/_/g, "%20")
        if (fr !== undefined) {
            const familyRootHtml = makeFamilyRootHtml(data, fr, "root", link);
            const familyRootElement = document.getElementById(key_id)
            familyRootElement.innerHTML = familyRootHtml
        } else {
            console.log(`${key_clean} not found in family_root_json.js`)
        }
    })
};

function superScripter(text) {
    const regex = /\d/g;
    return text.replace(regex, match => `&hairsp;<sup>${match}</sup>`);
}

function playAudio(headword, buttonElement, gender) {
    const validGenders = ["male", "female", "male1", "male2", "female1"];
    if (!validGenders.includes(gender)) {
        gender = "male";
    }
    const baseUrl = "https://www.dpdict.net/audio/";
    var audio = new Audio(baseUrl + headword + "?gender=" + gender);

    audio.addEventListener("error", function () {
        if (buttonElement) {
            // Change icon to cross
            buttonElement.innerHTML = `
            <svg viewBox="0 0 24 24" width="16px" height="16px" fill="currentColor" stroke="currentColor" stroke-width="0">
                <path d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z"></path>
            </svg>
            `;
            // Disable button
            buttonElement.classList.add("disabled");
            buttonElement.style.pointerEvents = "none";
            buttonElement.title = "Аудио не найдено";
            buttonElement.removeAttribute("onclick");
        }
    });

    audio.play().catch(function (error) {
        console.log("Audio play failed: ", error);
    });
}