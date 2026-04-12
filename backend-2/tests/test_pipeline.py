from datetime import date, datetime, timezone
import unittest

from src.pipeline import analyze_field


class PipelineTestCase(unittest.TestCase):
    def test_analysis_payload_shape(self) -> None:
        request = {
            "field_id": "talhao_01",
            "property_name": "Fazenda Exemplo",
            "culture": "soja",
            "sowing_date": date(2026, 10, 15),
            "crop_stage": None,
            "irrigated": False,
            "analysis_timestamp": datetime(2026, 4, 11, 20, 30, tzinfo=timezone.utc),
            "geometry": {
                "type": "Polygon",
                "coordinates": [
                    [
                        [-55.8126, -12.4321],
                        [-55.7421, -12.4321],
                        [-55.7421, -12.4888],
                        [-55.8126, -12.4888],
                        [-55.8126, -12.4321],
                    ]
                ],
            },
        }

        result = analyze_field(request)

        self.assertIn("field_info", result)
        self.assertIn("summary", result)
        self.assertIn("metrics", result)
        self.assertIn("risk_flags", result)
        self.assertIn("forecast_timeseries", result)
        self.assertIn("map_layer", result)
        self.assertIn("copilot_response", result)

        self.assertGreater(result["field_info"]["area_ha"], 0)
        self.assertGreaterEqual(result["summary"]["risk_score"], 0)
        self.assertLessEqual(result["summary"]["risk_score"], 100)
        self.assertEqual(len(result["forecast_timeseries"]), 14)

    def test_analysis_accepts_iso_string_dates(self) -> None:
        payload = {
            "field_id": "talhao_02",
            "property_name": "Fazenda Teste",
            "culture": "milho",
            "sowing_date": "2026-01-20",
            "crop_stage": None,
            "irrigated": True,
            "analysis_timestamp": "2026-04-11T20:30:00Z",
            "geometry": {
                "type": "Polygon",
                "coordinates": [
                    [
                        [-55.8126, -12.4321],
                        [-55.7421, -12.4321],
                        [-55.7421, -12.4888],
                        [-55.8126, -12.4888],
                        [-55.8126, -12.4321],
                    ]
                ],
            },
        }

        result = analyze_field(payload)
        self.assertIn(result["summary"]["risk_level"], {"baixo", "moderado", "alto", "crítico"})
        self.assertEqual(result["field_info"]["uf"], "MT")


if __name__ == "__main__":
    unittest.main()
