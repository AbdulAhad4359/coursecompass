import unittest
from pathlib import Path
from unittest.mock import patch
from fastapi.testclient import TestClient
from app.main import app, sessions

class ApiTests(unittest.TestCase):
    def setUp(self):
        sessions.clear()
        self.client = TestClient(app)
        self.doc = self.client.post('/api/handbooks/demo').json()
        self.headers = {'X-Session-ID': self.doc['session_id']}
    def test_demo_metadata(self):
        self.assertEqual(self.doc['pages'], 5)
        self.assertTrue(self.doc['demo'])
    def test_chat(self):
        r=self.client.post('/api/chat',headers=self.headers,json={'question':'CS301 prerequisites'})
        self.assertEqual(r.status_code,200)
        self.assertEqual(r.json()['hits'][0]['chunk']['page'],4)
    def test_admission_abstains(self):
        r=self.client.post('/api/chat',headers=self.headers,json={'question':'45 percent in intermediate am I eligible for BSCS?'})
        self.assertEqual(r.json()['status'],'insufficient')
        self.assertEqual(r.json()['hits'],[])
    def test_session_required(self):
        self.assertEqual(self.client.post('/api/chat',json={'question':'CS301'}).status_code,404)
    def test_upload(self):
        data=(Path(__file__).resolve().parents[1]/'data/demo_handbook.pdf').read_bytes()
        r=self.client.post('/api/handbooks/upload',files={'file':('handbook.pdf',data,'application/pdf')})
        self.assertEqual(r.status_code,200)
        self.assertFalse(r.json()['demo'])
        self.assertNotEqual(r.json()['session_id'],self.doc['session_id'])
    def test_invalid_upload(self):
        self.assertEqual(self.client.post('/api/handbooks/upload',files={'file':('bad.pdf',b'no pdf')}).status_code,422)
    def test_page_range(self):
        self.assertEqual(self.client.get('/api/handbooks/pages/99',headers=self.headers).status_code,404)
        self.assertIn('CS301',self.client.get('/api/handbooks/pages/4',headers=self.headers).json()['passages'][0]['text'])
    def test_pdf(self):
        r=self.client.get('/api/handbooks/pdf',headers=self.headers)
        self.assertEqual(r.headers['content-type'],'application/pdf')
        self.assertTrue(r.content.startswith(b'%PDF-'))
    def test_delete_isolated(self):
        second=self.client.post('/api/handbooks/demo').json()
        self.client.delete('/api/session',headers=self.headers)
        self.assertEqual(self.client.get('/api/handbooks/current',headers=self.headers).status_code,404)
        self.assertEqual(self.client.get('/api/handbooks/current',headers={'X-Session-ID':second['session_id']}).status_code,200)
    def test_key_never_exposed(self):
        with patch.dict('os.environ',{'GEMINI_API_KEY':'secret-value'}):
            r=self.client.get('/api/health')
        self.assertNotIn('secret-value',r.text)
        self.assertTrue(r.json()['ai_configured'])
    def test_ai_without_key(self):
        with patch.dict('os.environ',{'GEMINI_API_KEY':''}):
            r=self.client.post('/api/chat',headers=self.headers,json={'question':'CS301','use_ai':True})
        self.assertEqual(r.status_code,409)
    def test_empty_question(self):
        self.assertEqual(self.client.post('/api/chat',headers=self.headers,json={'question':'  '}).status_code,422)
    def test_cors(self):
        r=self.client.options('/api/chat',headers={'Origin':'http://localhost:5173','Access-Control-Request-Method':'POST','Access-Control-Request-Headers':'content-type,x-session-id'})
        self.assertEqual(r.headers['access-control-allow-origin'],'http://localhost:5173')

if __name__=='__main__': unittest.main()
