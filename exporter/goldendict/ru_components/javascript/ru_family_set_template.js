function ru_makeFamilySets(data) {
    const familySetList = data.family_sets
    const familySetLen = familySetList.length
    const lemma = data.lemma
    const lemmaTag = data.lemma.replace(/ /g, "_")
    const lemmaLink = data.lemma.replace(/ /g, "%20")
    var html = "";

    //// header

    if (familySetLen > 1) {
        html += `<p class="heading" id="${lemmaTag}_fs_top">перейти к: `; 
        familySetList.forEach(item => {
            itemTag = item.replace(/ /g, "_")
            html += `<a class="jump" href="#${lemmaTag}_fs_${itemTag}">${item}</a> `;
        });
        html += `</p>`;
    };

    familySetList.forEach(item => {
        fs = ru_family_set_json[item]
        itemTag = item.replace(/ /g, "_")

        if (familySetLen > 1) {
            html += `<p class="heading underlined overlined" `
            html += `id=${lemmaTag}_fs_${itemTag}>`;
            html += `<b>${fs.count}</b> слов в группе `;
            html += `<b>${item}</b>`;
            html += `<a class="jump" href="#${lemmaTag}_fs_top"> ⤴</a></p>`;
        } else if (familySetLen == 1) {
            html += `<p class="heading underlined" `
            html += `id=${lemmaTag}_fs_top>`;
            html += `<b>${fs.count}</b> слов в группе `;
            html += `<b>${item}</b>`;
        };
        
        //// table

        html += `<table class="family"><tbody>`;
        fs.data.forEach(data => {
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
        href="https://docs.google.com/forms/d/1iMD9sCSWFfJAFCFYuG9HRIyrr9KFRy0nAOVApM998wM/viewform?usp=pp_url&amp;entry.438735500=${lemmaLink}&amp;entry.326955045=Группа&amp;entry.1433863141=GoldenDict+${data.date}" 
        target="_blank">
        Пожалуйста, сообщите об ошибке</a>.`; 
    
    html += `<a class="jump" href="#${lemmaTag}_fs_top"> ⤴</a></p>`

    return html
}
