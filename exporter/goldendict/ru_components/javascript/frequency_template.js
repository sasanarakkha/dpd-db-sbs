function frequencyTemplate(data) {
    const lemmaLink = data.lemma.replace(/ /g, "%20")
    var html = `
    <div class="tertiary">
        ${data.FreqHeading
            .replace('There are no matches of', 'Нет совпадений со словом')
            .replace('in any corpus.', 'ни в одной из версий текста')
            .replace('Frequency of', 'График частоты совпадений слова')
            .replace('and its', 'и его форм')
            .replace('declensions', 'склонений')
            .replace('conjugations', 'спряжений')
        }
    <br><br>
`
if (data.CstFreq[0] != undefined) {
    html += `
        <table class="frequency">
            <tr>
            <th></th>
            <th colspan="3" title="Chaṭṭha Saṅgāyana Tipiṭaka (Мьянма)">
                CST
            </th>
            <th class="gap"></th>
            <th colspan="2" title="Buddha Jayanti Tipiṭaka (Шри Ланка)">
                BJT
            </th>
            <th class="gap"></th>
            <th colspan="2" title="Syāmaraṭṭha 1927 Royal Edition (Таиланд)">
                SYA
            </th>
            <th class="gap"></th>
            <th colspan="2" title="SuttaCentral">
                SC
            </th>
            </tr>

            <tr>
            <th>Mūla</th>
            <td class="gr${data.CstGrad[0]}">${data.CstFreq[0]}</td>
            <td class="gr${data.CstGrad[1]}">${data.CstFreq[1]}</td>
            <td class="gr${data.CstGrad[2]}">${data.CstFreq[2]}</td>
            <td class="gap"></td>
            <td class="gr${data.BjtGrad[0]}">${data.BjtFreq[0]}</td>
            <td class="gr${data.BjtGrad[1]}">${data.BjtFreq[1]}</td>
            <td class="gap"></td>
            <td class="gr${data.SyaGrad[0]}">${data.SyaFreq[0]}</td>
            <td class="gr${data.SyaGrad[1]}">${data.SyaFreq[1]}</td>
            <td class="gap"></td>
            <td class="gr${data.ScGrad[0]}">${data.ScFreq[0]}</td>
            <td class="gr${data.ScGrad[1]}">${data.ScFreq[1]}</td>
            </tr>

            <tr>
            <th>Aṭṭh.</th>
            <td class="gr${data.CstGrad[3]}">${data.CstFreq[3]}</td>
            <td class="gr${data.CstGrad[4]}">${data.CstFreq[4]}</td>
            <td class="gr${data.CstGrad[5]}">${data.CstFreq[5]}</td>
            <td class="gap"></td>
            <td class="gr${data.BjtGrad[2]}">${data.BjtFreq[2]}</td>
            <td class="gr${data.BjtGrad[3]}">${data.BjtFreq[3]}</td>
            <td class="gap"></td>
            <td class="gr${data.SyaGrad[2]}">${data.SyaFreq[2]}</td>
            <td class="gr${data.SyaGrad[3]}">${data.SyaFreq[3]}</td>
            <td class="gap"></td>
            <td class="void"></td>
            <td class="void"></td>
            </tr>

            <tr>
            <th>Ṭīkā</th>
            <td class="gr${data.CstGrad[6]}">${data.CstFreq[6]}</td>
            <td class="gr${data.CstGrad[7]}">${data.CstFreq[7]}</td>
            <td class="gr${data.CstGrad[8]}">${data.CstFreq[8]}</td>
            <td class="gap"></td>
            <td class="gr${data.BjtGrad[4]}">${data.BjtFreq[4]}</td>
            <td class="gr${data.BjtGrad[5]}">${data.BjtFreq[5]}</td>
            <td class="gap"></td>
            <td class="gr${data.SyaGrad[4]}">${data.SyaFreq[4]}</td>
            <td class="gr${data.SyaGrad[5]}">${data.SyaFreq[5]}</td>
            <td class="gap"></td>
            <td class="void"></td>
            <td class="void"></td>
            </tr>

            <tr>
            <th>Other</th>
            <td class="gr${data.CstGrad[9]}">${data.CstFreq[9]}</td>
            <td class="gr${data.CstGrad[10]}">${data.CstFreq[10]}</td>
            <td class="gr${data.CstGrad[11]}">${data.CstFreq[11]}</td>
            <td class="gap"></td>
            <td class="gr${data.BjtGrad[6]}">${data.BjtFreq[6]}</td>
            <td class="gr${data.BjtGrad[7]}">${data.BjtFreq[7]}</td>
            <td class="gap"></td>
            <td class="gr${data.SyaGrad[6]}">${data.SyaFreq[6]}</td>
            <td class="gr${data.SyaGrad[7]}">${data.SyaFreq[7]}</td>
            <td class="gap"></td>
            <td class="void"></td>
            <td class="void"></td>
            </tr>

            <tr><td class="void"></td></tr>

            <tr>
            <th>Vinaya</th>
            <td class="gr${data.CstGrad[12]}">${data.CstFreq[12]}</td>
            <td class="void"></td>
            <td class="void"></td>
            <td class="gap"></td>
            <td class="gr${data.BjtGrad[8]}">${data.BjtFreq[8]}</td>
            <td class="void"></td>
            <td class="gap"></td>
            <td class="gr${data.SyaGrad[8]}">${data.SyaFreq[8]}</td>
            <td class="void"></td>
            <td class="gap"></td>
            <td class="gr${data.ScGrad[2]}">${data.ScFreq[2]}</td>
            <td class="void"></td>
            </tr>

            <tr>
            <th>Dīgha</th>
            <td class="gr${data.CstGrad[13]}">${data.CstFreq[13]}</td>
            <td class="void"></td>
            <td class="void"></td>
            <td class="gap"></td>
            <td class="gr${data.BjtGrad[9]}">${data.BjtFreq[9]}</td>
            <td class="void"></td>
            <td class="gap"></td>
            <td class="gr${data.SyaGrad[9]}">${data.SyaFreq[9]}</td>
            <td class="void"></td>
            <td class="gap"></td>
            <td class="gr${data.ScGrad[3]}">${data.ScFreq[3]}</td>
            <td class="void"></td>
            </tr>

            <tr>
            <th>Majjh.</th>
            <td class="gr${data.CstGrad[14]}">${data.CstFreq[14]}</td>
            <td class="void"></td>
            <td class="void"></td>
            <td class="gap"></td>
            <td class="gr${data.BjtGrad[10]}">${data.BjtFreq[10]}</td>
            <td class="void"></td>
            <td class="gap"></td>
            <td class="gr${data.SyaGrad[10]}">${data.SyaFreq[10]}</td>
            <td class="void"></td>
            <td class="gap"></td>
            <td class="gr${data.ScGrad[4]}">${data.ScFreq[4]}</td>
            <td class="void"></td>
            </tr>

            <tr>
            <th>Saṃy.</th>
            <td class="gr${data.CstGrad[15]}">${data.CstFreq[15]}</td>
            <td class="void"></td>
            <td class="void"></td>
            <td class="gap"></td>
            <td class="gr${data.BjtGrad[11]}">${data.BjtFreq[11]}</td>
            <td class="void"></td>
            <td class="gap"></td>
            <td class="gr${data.SyaGrad[11]}">${data.SyaFreq[11]}</td>
            <td class="void"></td>
            <td class="gap"></td>
            <td class="gr${data.ScGrad[5]}">${data.ScFreq[5]}</td>
            <td class="void"></td>
            </tr>

            <tr>
            <th>Aṅgut.</th>
            <td class="gr${data.CstGrad[16]}">${data.CstFreq[16]}</td>
            <td class="void"></td>
            <td class="void"></td>
            <td class="gap"></td>
            <td class="gr${data.BjtGrad[12]}">${data.BjtFreq[12]}</td>
            <td class="void"></td>
            <td class="gap"></td>
            <td class="gr${data.SyaGrad[12]}">${data.SyaFreq[12]}</td>
            <td class="void"></td>
            <td class="gap"></td>
            <td class="gr${data.ScGrad[6]}">${data.ScFreq[6]}</td>
            <td class="void"></td>
            </tr>

            <tr>
            <th>Khudd.</th>
            <td class="gr${data.CstGrad[17]}">${data.CstFreq[17]}</td>
            <td class="void"></td>
            <td class="void"></td>
            <td class="gap"></td>
            <td class="gr${data.BjtGrad[13]}">${data.BjtFreq[13]}</td>
            <td class="void"></td>
            <td class="gap"></td>
            <td class="gr${data.SyaGrad[13]}">${data.SyaFreq[13]}</td>
            <td class="void"></td>
            <td class="gap"></td>
            <td class="gr${data.ScGrad[7]}">${data.ScFreq[7]}</td>
            <td class="void"></td>
            </tr>

            <tr><td class="void"></td></tr>

            <tr>
            <th>Dhamm.</th>
            <td class="gr${data.CstGrad[18]}">${data.CstFreq[18]}</td>
            <td class="void"></td>
            <td class="void"></td>
            <td class="gap"></td>
            <td class="gr${data.BjtGrad[14]}">${data.BjtFreq[14]}</td>
            <td class="void"></td>
            <td class="gap"></td>
            <td class="gr${data.SyaGrad[14]}">${data.SyaFreq[14]}</td>
            <td class="void"></td>
            <td class="gap"></td>
            <td class="gr${data.ScGrad[8]}">${data.ScFreq[8]}</td>
            <td class="void"></td>
            </tr>

            <tr>
            <th>Vibhaṅ.</th>
            <td class="gr${data.CstGrad[19]}">${data.CstFreq[19]}</td>
            <td class="void"></td>
            <td class="void"></td>
            <td class="gap"></td>
            <td class="gr${data.BjtGrad[15]}">${data.BjtFreq[15]}</td>
            <td class="void"></td>
            <td class="gap"></td>
            <td class="gr${data.SyaGrad[15]}">${data.SyaFreq[15]}</td>
            <td class="void"></td>
            <td class="gap"></td>
            <td class="gr${data.ScGrad[9]}">${data.ScFreq[9]}</td>
            <td class="void"></td>
            </tr>

            <tr>
            <th>Dhātuk.</th>
            <td class="gr${data.CstGrad[20]}">${data.CstFreq[20]}</td>
            <td class="void"></td>
            <td class="void"></td>
            <td class="gap"></td>
            <td class="gr${data.BjtGrad[16]}">${data.BjtFreq[16]}</td>
            <td class="void"></td>
            <td class="gap"></td>
            <td class="gr${data.SyaGrad[16]}">${data.SyaFreq[16]}</td>
            <td class="void"></td>
            <td class="gap"></td>
            <td class="void"></td>
            <td class="void"></td>
            </tr>

            <tr>
            <th>Puggala.</th>
            <td class="gr${data.CstGrad[21]}">${data.CstFreq[21]}</td>
            <td class="void"></td>
            <td class="void"></td>
            <td class="gap"></td>
            <td class="gr${data.BjtGrad[17]}">${data.BjtFreq[17]}</td>
            <td class="void"></td>
            <td class="gap"></td>
            <td class="gr${data.SyaGrad[17]}">${data.SyaFreq[17]}</td>
            <td class="void"></td>
            <td class="gap"></td>
            <td class="void"></td>
            <td class="void"></td>
            </tr>

            <tr>
            <th>Kathāv.</th>
            <td class="gr${data.CstGrad[22]}">${data.CstFreq[22]}</td>
            <td class="void"></td>
            <td class="void"></td>
            <td class="gap"></td>
            <td class="gr${data.BjtGrad[18]}">${data.BjtFreq[18]}</td>
            <td class="void"></td>
            <td class="gap"></td>
            <td class="gr${data.SyaGrad[18]}">${data.SyaFreq[18]}</td>  
            <td class="gap"></td>          
            <td class="void"></td>
            <td class="void"></td>
            </tr>

            <tr>
            <th>Yamaka</th>
            <td class="gr${data.CstGrad[23]}">${data.CstFreq[23]}</td>
            <td class="void"></td>
            <td class="void"></td>
            <td class="gap"></td>
            <td class="gr${data.BjtGrad[19]}">${data.BjtFreq[19]}</td>
            <td class="void"></td>
            <td class="gap"></td>
            <td class="gr${data.SyaGrad[19]}">${data.SyaFreq[19]}</td>   
            <td class="gap"></td>         
            <td class="void"></td>
            <td class="void"></td>
            </tr>

            <tr>
            <th>Paṭṭhāna</th>
            <td class="gr${data.CstGrad[24]}">${data.CstFreq[24]}</td>
            <td class="void"></td>
            <td class="void"></td>
            <td class="gap"></td>
            <td class="gr${data.BjtGrad[20]}">${data.BjtFreq[20]}</td>
            <td class="void"></td>
            <td class="gap"></td>
            <td class="gr${data.SyaGrad[20]}">${data.SyaFreq[20]}</td>  
            <td class="gap"></td>          
            <td class="void"></td>
            <td class="void"></td>
            </tr>

            <tr><td class="void"></td></tr>

            <tr>
            <th>Paramat.</th>
            <td class="gr${data.CstGrad[25]}">${data.CstFreq[25]}</td>
            <td class="void"></td>
            <td class="void"></td>
            <td class="gap"></td>
            <td class="gr${data.BjtGrad[21]}">${data.BjtFreq[21]}</td>
            <td class="void"></td>
            <td class="gap"></td>
            <td class="gr${data.SyaGrad[21]}">${data.SyaFreq[21]}</td>      
            <td class="gap"></td>      
            <td class="void"></td>
            <td class="void"></td>
            </tr>

            <tr><td class="void"></td></tr>

            <tr>
            <th>Leḍī</th>
            <td class="gr${data.CstGrad[26]}">${data.CstFreq[26]}</td>
            <td class="void"></td>
            <td class="void"></td>
            <td class="gap"></td>
            <td class="gr${data.BjtGrad[22]}">${data.BjtFreq[22]}</td>
            <td class="void"></td>
            <td class="gap"></td>
            <td class="gr${data.SyaGrad[22]}">${data.SyaFreq[22]}</td>  
            <td class="gap"></td>          
            <td class="void"></td>
            <td class="void"></td>
            </tr>

            <tr>
            <th>Buddha.</th>
            <td class="gr${data.CstGrad[27]}">${data.CstFreq[27]}</td>
            <td class="void"></td>
            <td class="void"></td>
            <td class="gap"></td>
            <td class="gr${data.BjtGrad[23]}">${data.BjtFreq[23]}</td>
            <td class="void"></td>
            <td class="gap"></td>
            <td class="gr${data.SyaGrad[23]}">${data.SyaFreq[23]}</td>   
            <td class="gap"></td>         
            <td class="void"></td>
            <td class="void"></td>
            </tr>

            <tr><td class="void"></td></tr>

            <tr>
            <th>Other</th>
            <td class="gr${data.CstGrad[28]}">${data.CstFreq[28]}</td>
            <td class="void"></td>
            <td class="void"></td>
            <td class="gap"></td>
            <td class="gr${data.BjtGrad[24]}">${data.BjtFreq[24]}</td>
            <td class="void"></td>
            <td class="gap"></td>
            <td class="void"></td>
            <td class="void"></td>
            <td class="gap"></td>
            <td class="void"></td>
            <td class="void"></td>
            </tr>

        </table>

        <p>
            <b>CST</b>: Chaṭṭha Saṅgāyana Tipiṭaka (Мьянма)<br>
            <b>BJT</b>: Buddha Jayanti Tipiṭaka (Шри Ланка)<br>
            <b>SYA</b>: Syāmaraṭṭha 1927 Royal Edition (Таиланд)<br>    
        </p>
`
} else {
    html += `
    <p>
    Вероятно, слово встречается только в составе сложных слов. Или, возможно, это ошибка.
    </p>
`
}
html += `
    <p>
    Для подробного объяснения того, как рассчитывается этот график частоты слов, его точности и неточности, обратитесь, пожалуйста, к <a class="dpd-link" href="https://devamitta.github.io/dpd.rus/features/frequency/">этой веб-странице</a>.
    </p>
<p class='dpd-footer'>
    Что-то не на месте? <a class="dpd-link" href="https://docs.google.com/forms/d/1iMD9sCSWFfJAFCFYuG9HRIyrr9KFRy0nAOVApM998wM/viewform?usp=pp_url&amp;entry.438735500=${lemmaLink}&amp;entry.326955045=Частота&amp;entry.1433863141=GoldenDict+${data.date}" target="_blank">Сообщите здесь.</a>
</p>
</div>
`
    return html
}