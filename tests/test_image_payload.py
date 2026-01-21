import unittest

from app.openai_client import build_image_payload


class TestImagePayload(unittest.TestCase):
    def test_gpt_image_payload_omits_extra_keys(self) -> None:
        payload, _, _ = build_image_payload("gpt-image-1", "prompt")

        for key in ("output_format", "quality", "background", "response_format"):
            with self.subTest(key=key):
                self.assertNotIn(key, payload)

    def test_non_gpt_payload_includes_response_format(self) -> None:
        payload, _, _ = build_image_payload("dall-e-3", "prompt")

        self.assertEqual(payload.get("response_format"), "b64_json")


if __name__ == "__main__":
    unittest.main()
