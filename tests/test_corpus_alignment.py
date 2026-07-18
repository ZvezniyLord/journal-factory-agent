from journal_factory.corpus_extract import ExtractedDocument
from journal_factory.corpus_match import align_articles, profile_raw
from journal_factory.corpus_pdf import GoldenArticle, parse_golden_pages


def test_front_matter_udc_is_not_an_article():
    pages = [
        "PUBLISHER",
        "UDC 001.3\nISBN 978-1\nhttps://doi.org/10.1234/conf-95",
        "TABLE OF CONTENTS\n1. Author\nTITLE\n6",
        "6\nECONOMIC THEORY\nUDC 330.1\nIvan Petrenko\nUniversity\nARTICLE TITLE\nAbstract. Body",
    ]
    _, articles, warnings = parse_golden_pages(pages, 95)
    assert len(articles) == 1
    assert articles[0].printed_start_page == 6
    assert not warnings


def test_high_confidence_unique_match():
    golden = GoldenArticle(
        article_id="c095-a001",
        ordinal=1,
        physical_start_page=8,
        physical_end_page=12,
        printed_start_page=6,
        section="ECONOMIC THEORY",
        udc="330.1",
        authors=("Іван Петренко",),
        title="ЦИФРОВА ТРАНСФОРМАЦІЯ ПІДПРИЄМСТВ",
        header_lines=(),
        body_preview="Анотація. Досліджено цифрову трансформацію підприємств.",
    )
    document = ExtractedDocument(
        path="petrenko.docx",
        sha256="a" * 64,
        size=1000,
        extension=".docx",
        extraction_method="OOXML_XML",
        text=(
            "УДК 330.1\nІван Петренко\nаспірант\nУніверситет\n"
            "ЦИФРОВА ТРАНСФОРМАЦІЯ ПІДПРИЄМСТВ\n"
            "Анотація. Досліджено цифрову трансформацію підприємств."
        ),
        word_count=200,
        is_article_candidate=True,
        rejection_reasons=(),
    )
    result = align_articles([golden], [profile_raw(document)])[0]
    assert result.status == "MATCHED_HIGH"
    assert result.selected_raw_path == "petrenko.docx"
