import unittest
from pathlib import Path
from unittest.mock import patch
from app.rag import Handbook, answer, validate_answer, codes

class RagTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.book = Handbook((Path(__file__).resolve().parents[1]/'data/demo_handbook.pdf').read_bytes(), 'demo.pdf')
    def test_pages(self):
        self.assertEqual(self.book.page_count, 5)
    def test_prerequisite_retrieval(self):
        hits, _ = self.book.retrieve('What are the prerequisites for CS301?')
        self.assertEqual(hits[0]['chunk']['page'], 4)
        self.assertIn('BOTH CS201 and MATH102', hits[0]['chunk']['text'])
    def test_title_retrieval(self):
        hits, _ = self.book.retrieve('Artificial Intelligence prerequisites')
        self.assertEqual(hits[0]['chunk']['page'], 4)
    def test_unknown(self):
        result = answer(self.book, 'What is required for CS999?')
        self.assertEqual(result['status'], 'insufficient')
        self.assertEqual(result['claims'], [])
    def test_unrelated(self):
        self.assertEqual(answer(self.book, 'Explain volcanoes and lava')['status'], 'insufficient')
    def test_local_mode_not_generated(self):
        self.assertEqual(answer(self.book, 'CS301 prerequisites')['status'], 'evidence')
    def test_valid_citation(self):
        hits, _ = self.book.retrieve('CS301 prerequisites')
        chunk = hits[0]['chunk']
        data = {'status':'answered','claims':[{'text':'Both courses are required.','source_id':chunk['id'],'quote':'Prerequisites: BOTH CS201 and MATH102.'}],'missing':''}
        self.assertEqual(validate_answer(data, hits)['claims'][0]['page'], 4)
    def test_fabricated_quote_blocked(self):
        hits, _ = self.book.retrieve('CS301 prerequisites')
        with self.assertRaises(ValueError):
            validate_answer({'status':'answered','claims':[{'text':'No prerequisites.','source_id':hits[0]['chunk']['id'],'quote':'CS301 has no prerequisites.'}],'missing':''}, hits)
    def test_fabricated_source_blocked(self):
        with self.assertRaises(ValueError):
            validate_answer({'status':'answered','claims':[{'text':'X','source_id':'P999C1','quote':'A made up supporting quote.'}],'missing':''}, [])
    def test_no_uncited_answer(self):
        with self.assertRaises(ValueError):
            validate_answer({'status':'answered','claims':[],'missing':''}, [])
    def test_api_failure_fallback(self):
        with patch('app.rag.generate', side_effect=RuntimeError('API unavailable')):
            result = answer(self.book, 'CS301 prerequisites', 'test')
        self.assertEqual(result['status'], 'generation_error')
        self.assertTrue(result['hits'])
        self.assertFalse(result['claims'])
    def test_corrupt_pdf(self):
        with self.assertRaises(ValueError):
            Handbook(b'not a PDF', 'broken.pdf')
    def test_invalid_model_fallback(self):
        result = answer(self.book, 'CS301 prerequisites', 'test', 'invalid/model')
        self.assertEqual(result['status'], 'configuration_error')
    def test_lab_code(self):
        self.assertEqual(codes('CS203L'), {'CS203L'})
    def test_course_normalization(self):
        self.assertEqual(codes('cs 301 and MATH-102'), {'CS301','MATH102'})

if __name__ == '__main__':
    unittest.main()
