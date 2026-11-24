"""Verify the browser reading path on a bus with simultaneous native and preview traffic."""
from unittest.mock import MagicMock

import pytest
from ovos_utils.fakebus import FakeBus

from conftest import (COMMON_READING_FETCH_CONTENT, COMMON_READING_FETCH_CONTENT_RESPONSE,
                      COMMON_READING_SEARCH, COMMON_READING_SEARCH_RESPONSE, session_message)


@pytest.mark.parametrize(("lang", "utterance", "collection", "title", "text"), [
    ("en-CA", "Tell me a story.", "andrew lang", "Cinderella", "Once there was a gentleman."),
    ("fr-CA", "Raconte-moi une histoire.", "cosquin", "Jean de l'Ours", "Il était une fois un roi."),
    ("de-DE", "Erzähl mir ein Märchen.", "bechstein", "Aschenbrödel", "Es war einmal eine Frau."),
])
def test_preview_returns_real_excerpt_and_specific_source(plugin, monkeypatch, lang, utterance, collection, title, text):
    bus = plugin._bus = FakeBus()
    monkeypatch.setattr("time.sleep", lambda *_: None)
    message = session_message("visitor", data={"utterance": utterance, "lang": lang}, lang=lang,
                              source="skills", destination="preview-client",
                              thalovant_story_preview=True, thalovant_preview_request_id="original")
    skill = "provider.andlo"
    url = ("https://gutenberg.pglaf.org/1/2/123/123-h/story.htm#tale" if lang == "en-CA" else
           "https://www.gutenberg.org/files/123/story.htm#tale")
    def search(req):
        assert req.data["lang"] == lang and req.data["collection_hint"] == collection
        bus.emit(req.reply(COMMON_READING_SEARCH_RESPONSE,
                           {"title":title,"content_id":"tale","skill_id":skill,"confidence":1.0}))
    def fetch(req):
        assert req.data["lang"] == lang and req.data["content_id"] == "tale"
        wrong = req.reply(COMMON_READING_FETCH_CONTENT_RESPONSE, {"paragraphs":["Another visitor's tale."]})
        wrong.context["thalovant_preview_request_id"] = "different"
        bus.emit(wrong)
        bus.emit(req.reply(COMMON_READING_FETCH_CONTENT_RESPONSE,
                           {"paragraphs":[text],"source":{"title":title,"url":url}}))
    bus.on(COMMON_READING_SEARCH, search)
    bus.on(f"{COMMON_READING_FETCH_CONTENT}.{skill}", fetch)
    replies = []
    bus.on("speak", replies.append)
    match = plugin.match([utterance], lang, message)
    assert match.match_type == f"{plugin.skill_id}:story_preview"
    plugin.handle_story_preview(message)
    [reply] = replies
    assert reply.context["destination"] == "preview-client"
    assert reply.context["source"] == "skills"
    assert reply.context["thalovant_preview_request_id"] == "original"
    assert reply.data == {"utterance":text,"meta":{
        "thalovant_story_preview":True, "provenance":"source", "sources":[{"title":title,"url":url}]}}
    assert not plugin._readings and not plugin.settings

@pytest.mark.parametrize(("intent", "sources"), [
    ("read_any_story", None),
    ("read_any_story", {"title":"Book","url":"https://gutenberg.pglaf.org/unrelated/page.html#chapter"}),
    ("read_any_story", {"title":"Book","url":"https://www.gutenberg.org.evil.example/files/123/book.htm#story"}), ("read_any_story", {"title":"Book","url":"https://www.gutenberg.org/"}),
    ("continue", {"title":"Book","url":"https://www.gutenberg.org/edition#chapter"}),
])
def test_preview_fails_without_a_source_or_a_reading_request(plugin, intent, sources):
    message = session_message("visitor", data={"utterance":"Raconte-moi une histoire.", "lang":"fr-CA"},
                              source="skills", destination="preview-client",
                              thalovant_story_preview=True, thalovant_preview_request_id="r")
    plugin._get_intent_container = MagicMock()
    plugin._get_intent_container.return_value.calc_intent.return_value = {"name":intent,"conf":1}
    plugin._search_providers = MagicMock(return_value=[{"skill_id":"skill","confidence":1}])
    plugin._fetch_record = MagicMock(return_value={"paragraphs":["Le texte."],"source":sources})
    plugin.handle_story_preview(message)
    speech = plugin.bus.emit.call_args.args[0]
    assert speech.context["destination"] == "preview-client"
    assert speech.context["thalovant_preview_request_id"] == "r"
    reply = speech.data
    assert "conte" in reply["utterance"]
    assert reply["meta"]["provenance"] == "platform" and reply["meta"]["sources"] == []
