function ru_makeFamilyIdioms(data) {
    const familyIdiomList = data.family_idioms
    const lemmaTag = data.lemma.replace(/ /g, "_")
    const lemmaLink = data.lemma.replace(/ /g, "%20")
    var html = "";

    //// header

    if (familyIdiomList.length > 1) {
        html += `<p class="heading" id="${lemmaTag}_fi_top">перейти к: `; 
        familyIdiomList.forEach(item => {
            itemTag = item.replace(/ /g, "_")
            html += `<a class="jump" href="#${lemmaTag}_fi_${itemTag}">${item}</a> `;
        });
        html += `</p>`;
    };

    familyIdiomList.forEach(item => {
        fi = ru_family_idiom_json[item]
        itemTag = item.replace(/ /g, "_")

        if (familyIdiomList.length > 1) {
            html += `<p class="heading underlined overlined" `
            html += `id=${lemmaTag}_fi_${itemTag}>`;
            html += `<b>${fi.count}</b> идиом(ы) содержат `;
            html += `<b>${ru_superScripter(item)}</b>`;
            html += `<a class="jump" href="#${lemmaTag}_fi_top"> ⤴</a></p>`;
        } else if (familyIdiomList.length == 1) {
            html += `<p class="heading underlined" `
            html += `id=${lemmaTag}_fi_top>`;
            html += `<b>${fi.count}</b> идиома содержащая `;
            html += `<b>${ru_superScripter(item)}</b>`;
        };
        
        
        //// table

        html += `<table class="family"><tbody>`;
        fi.data.forEach(data => {
            const [word, pos, meaning, complete] = data
            html += `
            <tr>
            <th>${ru_superScripter(word)}</th>
            <td><b>${pos}</b></td>
            <td>${meaning}</td>
            <td><span class="gray">${complete}</span></td>
            </tr>
            `;
        });

        html += `</tbody></table>`;
    });

    //// footer

    html += `
        <p class="dpd-footer">
        <a class="dpd-link" 
        href="https://docs.google.com/forms/d/1iMD9sCSWFfJAFCFYuG9HRIyrr9KFRy0nAOVApM998wM/viewform?usp=pp_url&amp;entry.438735500=${lemmaLink}&amp;entry.326955045=Идиомы&amp;entry.1433863141=GoldenDict+${data.date}" 
        target="_blank">
        Пожалуйста, сообщите об ошибке</a>.`; 
    
    html += `<a class="jump" href="#${lemmaTag}_fi_top"> ⤴</a></p>`

    return html
}
