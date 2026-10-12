from infra.planalto import split_articles

SAMPLE = """
<p align="center"><b>SEÇÃO I<br>Da Proteção</b></p>
<p>Art. 1&deg; Primeiro artigo <strike>texto revogado</strike> vigente.</p>
<p>Art. 15. (Vetado) .</p>
<p>Art. 54-A. Artigo com letra. Altera outra lei: &quot;Art. 15. Citado de outra lei.&quot;</p>
<p>Brasília, 11 de setembro de 1990; rodapé</p>
"""


def test_split():
    arts = split_articles(SAMPLE)
    assert [a.id for a in arts] == ["Art. 1", "Art. 54-A"], arts
    assert "revogado" not in arts[0].text, arts[0]
    assert "SEÇÃO" not in arts[0].text, arts[0]
    assert '"Art. 15. Citado de outra lei."' in arts[1].text, arts[1]
    assert "rodapé" not in arts[1].text, arts[1]


if __name__ == "__main__":
    test_split()
    print("ok")
