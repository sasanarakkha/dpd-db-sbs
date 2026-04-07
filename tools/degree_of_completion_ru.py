from db.models import DpdHeadword
from tools.degree_of_completion import degree_of_completion


def degree_of_completion_ru(i: DpdHeadword, html=True):
    """
    Return html styled symbol of a word data degree of completion with normal color for those having ru_meaning.
    the rest is the same as in original degree_of_completion
    Return plain or HTML styled symbol of a word data degree of completion.
    ✔ = complete = meaning_1 and source_1
    ◑ = half-complete = meaning_1 and no source_1
    ✘ = incomplete = no meaning_1
    """
    if i.ru:
        if i.ru.ru_meaning:
            result = degree_of_completion(i, html).replace(' class="gray"', "")
            return result
        else:
            return degree_of_completion(i, html)
    else:
        return degree_of_completion(i, html)