# coding=utf-8
"""Test keyword functionality
"""

import unittest

from safe.keywords.keywords_management import Keywords
#from safe.keywords.keywords_management import KeywordsLayerImpact


class Test_Keywords(unittest.TestCase):
    """Tests for Keywords management.
    """

    def test_import(self):
        """Impact functions are filtered correctly
        """

        keywords = Keywords("""{
    "VERSION": 1.0,
    "publisher": "",
    "attribution": "",
    "primary_layer": {
        "title": "People affected by flood prone areas",
        "layer_type": "impact",
        "function_details": {
            "impact_function_id": "",
            "impact_function_name": "FloodEvacuationFunction",
            "author" : "AIFDR",
            "synopsis": "Impact function for flood evacuation",
            "rating" : "4",
            "parameters": "layers",
            "description": "Risk plugin for flood population evacuation",
            "citation": "",
            "limitation": "The default threshold of 1 meter was selected \
based on consensus, not hard evidence.",
            "hazard": "A hazard raster layer where each cell represents \
flood depth (in meters).",
            "exposure": "An exposure raster layer where each cell represent \
population count."
        },
        "impact_assessment": {
            "exposure_subcategory": "population",
            "hazard_subcategory": "flood",
            "hazard_units": "wet/dry",
            "total_population": 355487000,
            "affected_population": 134953000,
            "evacuated_population": 134953000
        },
        "minimum_needs": {
            "food": {
                "type": "Rice",
                "quantity": 377868400,
                "units": "kilogram",
                "plural": "kilograms",
                "unit_abbreviation": "kg",
                "per_time_period": "week",
                "per_population_unit": "person"
            },
            "drinking_water": {
                "type": "Drinking water",
                "quantity":  2361677500,
                "units": "litre",
                "plural": "litres",
                "unit_abbreviation": "l",
                "per_time_period": "week",
                "per_population_unit": "person"
            },
            "clean_water": {
                "type": "Clean water",
                "quantity":  9041851000,
                "units": "litre",
                "plural": "litres",
                "unit_abbreviation": "l",
                "per_time_period": "week",
                "per_population_unit": "person"
            },
            "hygine_pack": {
                "type": "Hygiene packs",
                "quantity":  26990600,
                "units": "pack",
                "plural": "packs",
                "per_time_period": "week",
                "per_population_unit": "family"
            },
            "toilet": {
                "type": "Toilet",
                "quantity": "6747650",
                "units": "toilet",
                "plural": "toilets",
                "per_time_period": "week",
                "per_population_unit": "person"
            }
        },
        "post_processing": {
        }
    },
    "provenance": {
        "impact_layer": {
             "path": "impact_layer.shp",
             "attribution": ""
        },
        "exposure_layer": {
             "path": "exposure_layer.shp",
             "attribution": ""
        },
        "aggregation_layer": {
             "path": "aggregation_layer.shp",
             "attribution": ""
        }
    },
    "metrics": {
        "analysis_date": "16-10-2013 08:43.23",
        "analysis_duration": 2133
    }
}
""")
        self.assertEqual(keywords.metrics['analysis_duration'], 2133)


if __name__ == '__main__':
    suite = unittest.makeSuite(Test_Keywords, 'test')
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(suite)
