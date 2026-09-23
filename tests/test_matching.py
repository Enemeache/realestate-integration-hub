from app.matching import TfidfMatcher
from app.models import Property

PROPERTIES = [
    Property(
        id="p1",
        title="Casa con pileta y quincho",
        description="Casa familiar con jardín, pileta climatizada y quincho, cerca del colegio",
        neighborhood="Los Castores, Nordelta",
        price_usd=420000,
        bedrooms=4,
    ),
    Property(
        id="p2",
        title="Monoambiente a estrenar",
        description="Departamento de un ambiente con amenities y gimnasio, ideal soltero",
        neighborhood="Puertos, Escobar",
        price_usd=135000,
        bedrooms=1,
    ),
]


def test_top_matches_ranks_relevant_property_first():
    matcher = TfidfMatcher(PROPERTIES)

    results = matcher.top_matches("busco una casa con pileta para mi familia", k=2)

    assert results[0].property_id == "p1"
    assert results[0].score > results[1].score


def test_top_matches_with_empty_catalog_returns_empty_list():
    matcher = TfidfMatcher([])

    assert matcher.top_matches("cualquier cosa") == []
