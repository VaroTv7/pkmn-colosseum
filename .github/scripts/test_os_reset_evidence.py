"""Keep the reset-assembly exception scoped to its evidenced SDK body."""
import unittest
from pathlib import Path
import quality_scan

PATH = 'src/dolphin/os/OSReset_exact.c'
FUNCTION = 'Reset_8009FF50'

class ResetEvidenceTests(unittest.TestCase):
    def setUp(self):
        source = (quality_scan.REPO_ROOT / PATH).read_text()
        regions = quality_scan.find_asm_regions(source)
        self.body = next(r['body'] for r in regions if r['func'] == FUNCTION)

    def test_registry_evidence_complete(self):
        entry = quality_scan.AUTHENTIC_ASM[(PATH, FUNCTION)]
        self.assertEqual(quality_scan.evidence_problems(entry), [])

    def test_original_body_allowed(self):
        self.assertTrue(quality_scan.asm_body_ok(self.body, PATH, FUNCTION))

    def test_extra_function_call_rejected(self):
        self.assertFalse(quality_scan.asm_body_ok(self.body+'\n bl arbitrary_function', PATH, FUNCTION))

    def test_game_path_cannot_reuse_exception(self):
        self.assertFalse(quality_scan.asm_body_ok(self.body, 'src/game/reset.c', FUNCTION))

if __name__ == '__main__':
    unittest.main()
