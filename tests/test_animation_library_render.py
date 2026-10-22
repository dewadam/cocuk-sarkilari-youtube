import sys, unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"app"))
from render_from_animation_library import choose_playlist

class TestAnimationLibraryRender(unittest.TestCase):
    def test_matches_lyric_keywords(self):
        catalog={"clips":[
          {"clip_id":"ANIM_RABBIT","approved":True,"duration_seconds":30,"asset_url":"https://example.com/rabbit.mp4","keywords":["tavşan zıplıyor"],"tags":["tavşan"],"category":"hayvan","actions":["zıplama"],"characters":["tavşan"],"environments":["çiftlik"],"moods":["neşeli"]},
          {"clip_id":"ANIM_SPACE","approved":True,"duration_seconds":30,"asset_url":"https://example.com/space.mp4","keywords":["roket uzay"],"tags":["roket"],"category":"uzay","actions":["uçma"],"characters":["astronot"],"environments":["uzay"],"moods":["neşeli"]}]}
        playlist=choose_playlist("Minik tavşan çiftlikte zıplıyor.\nTavşan havuca bakıyor.",catalog,55)
        self.assertTrue(playlist)
        self.assertTrue(all(x["clip_id"]=="ANIM_RABBIT" for x in playlist))
    def test_no_random_fallback(self):
        catalog={"clips":[{"clip_id":"ANIM_SPACE","approved":True,"duration_seconds":30,"asset_url":"https://example.com/space.mp4","keywords":["roket uzay"],"tags":["roket"],"category":"uzay","actions":["uçma"],"characters":["astronot"],"environments":["uzay"],"moods":["neşeli"]}]}
        with self.assertRaises(RuntimeError): choose_playlist("Kırmızı elma ağaçta durur",catalog,30)
if __name__=="__main__": unittest.main()
