function ru_makeFamilyWordHtml(data) {
    fw = ru_family_word_json[data.family_word]
    const lemmaLink = data.lemma.replace(/ /g, "%20")

    //// header

    var html = `
        <p class="heading">
            <b>${fw.count}</b> 
            слов(а), которые принадлежат к семье 
            <b>${ru_superScripter(data.family_word)}</b> 
        </p>
    `;

    //// table

    html += `<table class="family"><tbody>`;

    fw.data.forEach(item => {
        html += `
            <tr>
            <th>${ru_superScripter(item[0])}</th>
            <td><b>${item[1]}</b></td>
            <td>${item[2]}</td>
            <td><span class="gray">${item[3]}</span></td>
            </tr>
        `;
    });

    html += `</tbody></table>`;

    //// footer

    html += `
        <p class="dpd-footer">
        Что-то не на месте?
        <a class="dpd-link" 
        href="https://docs.google.com/forms/d/1iMD9sCSWFfJAFCFYuG9HRIyrr9KFRy0nAOVApM998wM/viewform?usp=pp_url&amp;entry.438735500=${lemmaLink}&amp;entry.326955045=Семья+слова&amp;entry.1433863141=GoldenDict+${data.date}" 
        target="_blank">
        Пожалуйста сообщите
        </a>.
        </p>
    `;

    return html
}