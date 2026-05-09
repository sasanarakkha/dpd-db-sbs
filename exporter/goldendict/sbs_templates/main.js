//// listen for button clicks

document.addEventListener("click", function (event) {
  var target = event.target;
  const classNames = ["dpd-button"];
  if (classNames.some((className) => target.classList.contains(className))) {
    const target_id = target.getAttribute("data-target");
    if (target_id && target_id.startsWith("sbs_")) {
        sbs_button_click(target);
        event.preventDefault();
        event.stopImmediatePropagation();
    }
  }
});

//// handle button clicks

function sbs_button_click(el) {
  const target_id = el.getAttribute("data-target");
  var target = document.getElementById(target_id);

  if (target) {
    if (target.textContent.includes("loading...")) {
      sbs_loadData();
    }

    target.classList.toggle("hidden");
    if (el.classList.contains("close")) {
      var target_control = document.querySelector(
         'a.dpd-button[data-target="' + target_id + '"]'
      );
      if (target_control) {
        target_control.classList.toggle("active");
      }
    } else {
      el.classList.toggle("active");
    }
  }
}

//// get the data to load into buttons

function sbs_init() {
  sbs_loadData();
  const gdParams = new URLSearchParams(window.location.search);
  const gdWord = gdParams.get("word");
  if (gdWord) {
    highlightInflections(gdWord.trim());
  }
}
if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", sbs_init);
} else {
  sbs_init();
}

function sbs_loadData() {
  var metaTags = document.querySelectorAll("meta[data_key]");
  var metaArray = Array.from(metaTags);
  metaArray.forEach((tag) => {
    var dataKey = tag.getAttribute("data_key");
    var data = window[dataKey];
    if (dataKey.startsWith("sbsdata_")) {
      sbs_loadButtonContent(data);
    } else if (dataKey.startsWith("rootdata_sbs_")) {
      sbs_loadRootButtonContent(data);
    }
  });
}

//// load json data into buttons

function sbs_loadButtonContent(data) {
  const lemmaTag = data.lemma.replace(/ /g, "_").replace(".", "_"); // a 1.1 > a_1_1

  //// feedback

  const feedbackHTML = sbs_makeFeedback(data);
  const feedbackElement = document.getElementById(`sbs_feedback_${lemmaTag}`);
  if (feedbackElement) feedbackElement.innerHTML = feedbackHTML;

  // frequency

  if (data.CstFreq != undefined) {
    const frequencyHTML = sbs_makeFrequency(data);
    const frequencyElement = document.getElementById(`sbs_frequency_${lemmaTag}`);
    if (frequencyElement) frequencyElement.innerHTML = frequencyElement.innerHTML.replace(
      "frequency loading...",
      frequencyHTML
    );
  }

  //// family compounds

  if (
    data.family_compounds &&
    data.family_compounds.length > 0 &&
    typeof family_compound_json !== "undefined"
  ) {
    const familyCompoundHtml = sbs_makeFamilyCompoundHtml(data);
    const familyCompoundElement = document.getElementById(
      `sbs_family_compound_${lemmaTag}`
    );
    if (familyCompoundElement) familyCompoundElement.innerHTML = familyCompoundHtml;
  }

  //// family root

  if (data.family_root != "" && typeof family_root_json !== "undefined") {
    const fr = family_root_json[data.family_root];
    if (fr !== undefined) {
      const familyRootHtml = sbs_makeFamilyRootHtml(data, fr, "lemma");
      const familyRootElement = document.getElementById(
        `sbs_family_root_${lemmaTag}`
      );
      if (familyRootElement) familyRootElement.innerHTML = familyRootHtml;
    }
  }

  //// family idioms

  if (
    data.family_idioms &&
    data.family_idioms.length > 0 &&
    typeof family_idiom_json !== "undefined"
  ) {
    const familyIdiomHtml = sbs_makeFamilyIdioms(data);
    const familyIdiomElement = document.getElementById(
      `sbs_family_idiom_${lemmaTag}`
    );
    if (familyIdiomElement) familyIdiomElement.innerHTML = familyIdiomHtml;
  }

  //// family sets

  if (
    data.family_sets &&
    data.family_sets.length > 0 &&
    typeof family_set_json !== "undefined"
  ) {
    const familySetHtml = sbs_makeFamilySets(data);
    const familySetElement = document.getElementById(`sbs_family_set_${lemmaTag}`);
    if (familySetElement) familySetElement.innerHTML = familySetHtml;
  }

  //// family word

  if (data.family_word && typeof family_word_json !== "undefined") {
    const familyWordHtml = sbs_makeFamilyWordHtml(data);
    const familyWordElement = document.getElementById(
      `sbs_family_word_${lemmaTag}`
    );
    if (familyWordElement) familyWordElement.innerHTML = familyWordHtml;
  }
}

//// load root dictionary button content

function sbs_loadRootButtonContent(data) {
  const familyRootDivs = document.querySelectorAll('div[id^="sbs_root_family_"]');
  var familyRootArray = Array.from(familyRootDivs);
  familyRootArray.forEach((item) => {
    const key_id = item.id;
    const key_clean = item.id.replace("sbs_root_family_", "").replace(/_/g, " ");
    const fr = family_root_json[key_clean];
    const link = item.id.replace("sbs_root_family_", "").replace(/_/g, "%20");
    if (fr !== undefined) {
      const familyRootHtml = sbs_makeFamilyRootHtml(data, fr, "root", link);
      const familyRootElement = document.getElementById(key_id);
      familyRootElement.innerHTML = familyRootHtml;
    } else {
      console.log(`${key_clean} not found in family_root_json.js`);
    }
  });
}

//// highlight the searched word in the inflection table

function highlightInflections(searchTerm) {
  if (!searchTerm) return;

  const tempDiv = document.createElement("div");
  tempDiv.textContent = searchTerm;
  const normalizedSearch = tempDiv.textContent;

  const inflectionTables = document.querySelectorAll("table.inflection");

  inflectionTables.forEach(function (table) {
    const cells = table.querySelectorAll("td");

    cells.forEach(function (cell) {
      const parts = cell.innerHTML.split(/<br\s*\/?>/i);
      let modified = false;

      const newParts = parts.map(function (part) {
        const tempElement = document.createElement("div");
        tempElement.innerHTML = part;
        const partText = tempElement.textContent || "";

        if (partText === normalizedSearch) {
          const span = document.createElement("span");
          span.className = "inflection-highlight";
          span.textContent = partText;
          modified = true;
          return span.outerHTML;
        }
        return part;
      });

      if (modified) {
        cell.innerHTML = newParts.join("<br>");
      }
    });
  });
}

function superScripter(text) {
  const regex = /\d/g;
  return text.replace(regex, (match) => `&hairsp;<sup>${match}</sup>`);
}

function sbs_playAudio(headword, buttonElement, gender) {
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
                <svg viewBox="0 0 24 24" width="16px" height="16px" fill="currentColor" stroke="currentColor" stroke-width="2">
                    <line x1="18" y1="6" x2="6" y2="18"></line>
                    <line x1="6" y1="6" x2="18" y2="18"></line>
                </svg>
            `;
      // Disable button
      buttonElement.classList.add("disabled");
      buttonElement.style.pointerEvents = "none";
      buttonElement.title = "Audio not found";
      buttonElement.removeAttribute("onclick");
    }
  });

  audio.play().catch(function (error) {
    console.log("Audio play failed: ", error);
  });
}
