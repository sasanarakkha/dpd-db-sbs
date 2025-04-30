function makeFamilyIdioms(data) {
    const familyIdiomList = data.family_idioms
    const lemmaTag = data.lemma.replace(/ /g, "_")
    const lemmaLink = data.lemma.replace(/ /g, "%20")
    var html = "";

    //// header

    if (familyIdiomList.length > 1) {
        html += `<p class="heading" id="${lemmaTag}_idiom_top">перейти к: `; 
        familyIdiomList.forEach(item => {
            itemTag = item.replace(/ /g, "_")
            html += `<a class="jump" href="#${lemmaTag}_idiom_${itemTag}">${item}</a> `;
        });
        html += `</p>`;
    };

    familyIdiomList.forEach(item => {
        fi = family_idiom_json[item]
        itemTag = item.replace(/ /g, "_")

        if (familyIdiomList.length > 1) {
            html += `<p class="heading underlined overlined" `
            html += `id=${lemmaTag}_idiom_${itemTag}>`;
            html += `<b>${fi.count}</b> идиоматических выражений, содержащих <b>${superScripter(item)}</b>`;
            html += `<a class="jump" href="#${lemmaTag}_idiom_top"> ⤴</a></p>`;
        } else if (familyIdiomList.length == 1) {
            html += `<p class="heading underlined" `
            html += `id=${lemmaTag}_idiom_top>`;
            html += `<b>${fi.count}</b> идиоматическое выражение, содержащее <b>${superScripter(item)}</b>`;
        };
        
        //// table

        html += `<table class="family"><tbody>`;
        fi.data.forEach(data => {
            const [word, pos, meaning, complete] = data
            html += `
                <tr>
                <th>${word}</th>
                <td><b>${pos}</b></td>
                <td>${meaning}</td>
                <td><span class="gray">${complete}</span></td>
                </tr>`;
        });

        html += `</tbody></table>`;
    });

    //// footer

    html += `
        <p class="footer">
        Пожалуйста, добавьте больше идиом  
        <a class="link" 
        href="https://docs.google.com/forms/d/1iMD9sCSWFfJAFCFYuG9HRIyrr9KFRy0nAOVApM998wM/viewform?usp=pp_url&amp;entry.438735500=${lemmaLink}&amp;entry.326955045=Идиомы&amp;entry.1433863141=GoldenDict+${data.date}" 
        target="_blank">
        здесь</a>.`; 
    
    html += `<a class="jump" href="#${lemmaTag}_idiom_top"> ⤴</a></p>`

    return html
}
