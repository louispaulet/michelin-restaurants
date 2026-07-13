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

    def test_skips_a_borough_even_when_it_also_has_a_city_type(self):
        entities = {
            "Q11299": {"claims": {"P131": [claim("Q60")], "P31": [claim("Q408804"), claim("Q3301053")]}},
            "Q60": {"claims": {"P31": [claim("Q515")]}},
        }
        types = {
            "Q408804": {"claims": {}},
            "Q3301053": {"claims": {"P279": [claim("Q515")]}},
            "Q515": {"claims": {}},
        }

        cities = city_entity_ids(entities, types)

        self.assertNotIn("Q11299", cities)
        self.assertEqual(nearest_city(["Q11299"], entities, cities), "Q60")

    def test_skips_a_special_ward_and_resolves_its_parent_city(self):
        entities = {
            "Q179645": {"claims": {"P131": [claim("Q1490")], "P31": [claim("Q5327704"), claim("Q900")]}},
            "Q1490": {"claims": {"P31": [claim("Q515")]}},
        }
        types = {
            "Q5327704": {"claims": {}},
            "Q900": {"claims": {"P279": [claim("Q515")]}},
            "Q515": {"claims": {}},
        }

        cities = city_entity_ids(entities, types)

        self.assertEqual(nearest_city(["Q179645"], entities, cities), "Q1490")

    def test_skips_an_exact_neighborhood_classification(self):
        entities = {
            "Q10": {"claims": {"P131": [claim("Q20")], "P31": [claim("Q123705"), claim("Q904")]}},
            "Q20": {"claims": {"P31": [claim("Q515")]}},
        }
        types = {
            "Q123705": {"claims": {}},
            "Q904": {"claims": {"P279": [claim("Q515")]}},
            "Q515": {"claims": {}},
        }

        cities = city_entity_ids(entities, types)

        self.assertNotIn("Q10", cities)
        self.assertEqual(nearest_city(["Q10"], entities, cities), "Q20")

    def test_leaves_a_rejected_subcity_without_a_parent_city_unassigned(self):
        entities = {
            "Q179351": {"claims": {"P131": [claim("Q23306")], "P31": [claim("Q211690"), claim("Q515")]}},
            "Q23306": {"claims": {"P31": [claim("Q901")]}},
        }
        types = {
            "Q211690": {"claims": {}},
            "Q515": {"claims": {}},
            "Q901": {"claims": {}},
        }

        cities = city_entity_ids(entities, types)

        self.assertNotIn("Q179351", cities)
        self.assertEqual(nearest_city(["Q179351"], entities, cities), "")

    def test_keeps_a_genuine_city_even_when_its_parent_is_city_like(self):
        entities = {
            "Q456": {"claims": {"P131": [claim("Q16665897")], "P31": [claim("Q902")]}},
            "Q16665897": {"claims": {"P31": [claim("Q903")]}},
        }
        types = {
            "Q902": {"claims": {"P279": [claim("Q515")]}},
            "Q903": {"claims": {"P279": [claim("Q515")]}},
            "Q515": {"claims": {}},
        }

        cities = city_entity_ids(entities, types)

        self.assertEqual(nearest_city(["Q456"], entities, cities), "Q456")

    def test_preserves_restaurant_identity_coordinates_and_locality_when_regrouping(self):
        aggregated = aggregate_bindings(
            [
                {
                    "restaurant": {"value": "http://www.wikidata.org/entity/Q1"},
                    "restaurantLabel": {"value": "Manhattan Table"},
                    "location": {"value": "http://www.wikidata.org/entity/Q11299"},
                    "locationLabel": {"value": "Manhattan"},
                    "coord": {"value": "Point(-73.98 40.76)"},
                }
            ]
        )
        entities = {
            "Q11299": {
                "claims": {"P131": [claim("Q60")], "P31": [claim("Q408804"), claim("Q3301053")]},
                "labels": {"en": {"value": "Manhattan"}},
            },
            "Q60": {
                "claims": {"P31": [claim("Q515")]},
                "labels": {"en": {"value": "New York City"}},
            },
        }
        types = {
            "Q408804": {"claims": {}},
            "Q3301053": {"claims": {"P279": [claim("Q515")]}},
            "Q515": {"claims": {}},
        }

        rows = finalize_rows(aggregated, entities, types)

        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["wikidata_id"], "Q1")
        self.assertEqual(rows[0]["id"], "manhattan-table")
        self.assertEqual((rows[0]["latitude"], rows[0]["longitude"]), ("40.76", "-73.98"))
        self.assertEqual((rows[0]["locality"], rows[0]["locality_wikidata_id"]), ("Manhattan", "Q11299"))
        self.assertEqual((rows[0]["city"], rows[0]["city_wikidata_id"]), ("New York City", "Q60"))
        validate_rows(rows, {"Q1"})

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
