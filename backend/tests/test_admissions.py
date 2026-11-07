"""Synthetic regression fixtures, NOT actual UCP admission policy."""
import unittest
from unittest.mock import patch, MagicMock
from app.rag import Handbook, answer, normalize_model, search_text

QUESTION = 'i have 45 percent marks in intermediate can i eligible for bscs'

def book_from_pages(texts):
    reader = MagicMock()
    reader.is_encrypted = False
    reader.page_labels = [str(i + 1) for i in range(len(texts))]
    reader.pages = [MagicMock() for _ in texts]
    for page, text in zip(reader.pages, texts):
        page.extract_text.return_value = text
    with patch('app.rag.PdfReader', return_value=reader):
        return Handbook(b'fixture', 'synthetic-only.pdf')

NOISE = [
    'CALL DIRECTORY CALL DIRECTORY 45 | STUDENT HANDBOOK 2020',
    'FINANCIAL SUPPORT MERIT SCHOLARSHIPS FOR NEW UNDERGRADUATE ADMISSIONS. Students with 45 percent marks in intermediate are eligible for a scholarship. BSCS.',
]

class AdmissionTests(unittest.TestCase):
    def test_screenshot_noise_is_not_an_answer(self):
        book = book_from_pages(NOISE)
        result = answer(book, QUESTION)
        self.assertEqual(result['status'], 'insufficient')
        self.assertEqual(result['hits'], [])
    def test_full_program_name_found(self):
        book = book_from_pages(NOISE + ['Bachelor of Science in Computer Science admission eligibility: minimum 50% marks in Intermediate with Mathematics.'])
        hits, problem = book.retrieve(QUESTION)
        self.assertIsNone(problem)
        self.assertEqual([h['chunk']['page'] for h in hits], [3])
    def test_wrong_program_rejected(self):
        book = book_from_pages(NOISE + ['BBA admission eligibility requires minimum 45% marks in Intermediate.'])
        self.assertEqual(answer(book, QUESTION)['status'], 'insufficient')
    def test_number_only_overlap_removed(self):
        self.assertNotIn('45', search_text('45 STUDENT HANDBOOK 2020'))
        self.assertIn('cs301', search_text('CS301'))
    def test_model_prefix_and_spaces(self):
        self.assertEqual(normalize_model(' models/gemini-flash-latest '), 'gemini-flash-latest')
    def test_model_url_rejected(self):
        with self.assertRaises(ValueError):
            normalize_model('https://example.com/model')
    def test_invalid_model_not_passed_off_as_evidence(self):
        result = answer(book_from_pages(NOISE), QUESTION, 'dummy', 'Gemini Flash')
        self.assertEqual(result['status'], 'configuration_error')
        self.assertEqual(result['hits'], [])
    def test_scholarship_query_still_searchable(self):
        hits, _ = book_from_pages(NOISE).retrieve('BSCS scholarship marks requirements')
        self.assertTrue(hits)
        self.assertEqual(hits[0]['chunk']['page'], 2)
    def test_generation_uses_qualified_evidence_only(self):
        book = book_from_pages(NOISE + ['BSCS admission criteria require minimum 50 percent marks in Intermediate.'])
        with patch('app.rag.generate', return_value={'status':'insufficient','claims':[], 'missing':'Other requirements are not stated.'}) as gen:
            answer(book, QUESTION, 'dummy')
        self.assertEqual([h['chunk']['page'] for h in gen.call_args.args[1]], [3])

if __name__ == '__main__':
    unittest.main()
