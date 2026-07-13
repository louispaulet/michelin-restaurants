import unittest

from generate_restaurants_csv import (
    aggregate_bindings,
    city_entity_ids,
    finalize_rows,
    nearest_city,
    parse_point,
    unique_slugs,
    validate_rows,
)


def claim(entity_id):
    return {"mainsnak": {"datavalue": {"value": {"id": entity_id}}}}


class GeneratorTests(unittest.TestCase):
    def test_aggregates_every_restaurant_without_requiring_michelin_id(self):
        bindings = [
            {
                "restaurant": {"value": "http://www.wikidata.org/entity/Q1"},
                "restaurantLabel": {"value": "One"},
            },
            {
                "restaurant": {"value": "http://www.wikidata.org/entity/Q2"},
                "restaurantLabel": {"value": "Two"},
                "michelinId": {"value": "region/city/restaurant/two"},
            },
        ]

        rows = aggregate_bindings(bindings)

        self.assertEqual({row["wikidata_id"] for row in rows}, {"Q1", "Q2"})
        self.assertEqual(next(row for row in rows if row["wikidata_id"] == "Q1")["michelin_ids"], set())

    def test_resolves_the_nearest_city_from_wikidata_hierarchy(self):
        entities = {
            "Q10": {"claims": {"P131": [claim("Q20")], "P31": [claim("Q100")]}},
            "Q20": {"claims": {"P131": [claim("Q30")], "P31": [claim("Q101")]}},
            "Q30": {"claims": {"P31": [claim("Q102")]}},
        }
        types = {
            "Q100": {"claims": {}},
            "Q101": {"claims": {"P279": [claim("Q515")]}},
            "Q102": {"claims": {"P279": [claim("Q515")]}},
            "Q515": {"claims": {}},
        }

        cities = city_entity_ids(entities, types)

        self.assertEqual(nearest_city(["Q10"], entities, cities), "Q20")

    def test_disambiguates_duplicate_readable_slugs(self):
        self.assertEqual(
            unique_slugs({"Q1": "Springfield", "Q2": "Springfield"}),
            {"Q1": "springfield-q1", "Q2": "springfield-q2"},
        )

    def test_keeps_missing_metadata_empty_and_disambiguates_duplicate_names(self):
        aggregated = aggregate_bindings(
            [
                {"restaurant": {"value": "http://www.wikidata.org/entity/Q1"}, "restaurantLabel": {"value": "Same"}},
                {"restaurant": {"value": "http://www.wikidata.org/entity/Q2"}, "restaurantLabel": {"value": "Same"}},
            ]
        )

        rows = finalize_rows(aggregated, {}, {})

        self.assertEqual({row["id"] for row in rows}, {"same-q1", "same-q2"})
        self.assertTrue(all(row["description"] == "" and row["country"] == "" for row in rows))
        self.assertTrue(all(row["michelin_id"] == "" and row["michelin_url"] == "" for row in rows))
        validate_rows(rows, {"Q1", "Q2"})

    def test_parses_and_rejects_coordinates(self):
        self.assertEqual(parse_point("Point(2.35 48.85)"), ("48.85", "2.35"))
        self.assertEqual(parse_point("not a point"), ("", ""))

    def test_validation_rejects_silent_drops_and_bad_coordinates(self):
        row = {
            "id": "one",
            "wikidata_id": "Q1",
            "name": "One",
            "latitude": "200",
            "longitude": "2",
            "city": "",
            "city_wikidata_id": "",
            "country": "",
            "country_wikidata_id": "",
        }
        with self.assertRaisesRegex(ValueError, "expected 2 rows"):
            validate_rows([row], {"Q1", "Q2"})
        with self.assertRaisesRegex(ValueError, "coordinates out of range"):
            validate_rows([row], {"Q1"})


if __name__ == "__main__":
    unittest.main()
