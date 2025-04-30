
function makeFamilyRootHtml(data, fr, source, link) {

    if (link == undefined) {
        const link = data.lemma.replace(" ", "%20")
    }

    //// header
    
    var html = `
        <p class="heading underlined">
            <b>${fr.count}</b> слов(а) принадлежат к семье корня 
            <b>${fr.root_family}</b> 
            (${fr.root_meaning})
        </p>
    `;

    //// table

    html += `<table class="family"><tbody>`;

    fr.data.forEach(item => {
        html += `
            <tr>
            <th>${item[0]}</th>
            <td><b>${item[1]}</b></td>
            <td>${item[2]}</td>
            <td><span class="gray">${item[3]}</span></td>
            </tr>
        `;
    });

    html += `
        </tbody>
        </table>
    `;

    //// footer

    if (source == "root") {
        html += `
        <p class="footer">
        Что-то не на месте? 
        <a class="link" 
        href="https://docs.google.com/forms/d/1iMD9sCSWFfJAFCFYuG9HRIyrr9KFRy0nAOVApM998wM/viewform?usp=pp_url&amp;entry.438735500=${data.root}&amp;entry.326955045=Семья+корня&amp;entry.1433863141=GoldenDict+${data.date}" 
        target="_blank">
        Пожалуйста сообщите
        </a>.
        </p>
    `;
    } else {
        html += `
        <p class="footer">
        Что-то не на месте? 
        <a class="link" 
        href="https://docs.google.com/forms/d/1iMD9sCSWFfJAFCFYuG9HRIyrr9KFRy0nAOVApM998wM/viewform?usp=pp_url&amp;entry.438735500=${data.root}&amp;entry.326955045=Семья+корня&amp;entry.1433863141=GoldenDict+${data.date}"
        target="_blank">
        Пожалуйста сообщите
        </a>.
        </p>
    `;
    }

    return html
}
