from types import SimpleNamespace

from app.services.rag import build_prompt, cited_numbers, make_sources


def chunk(page, content):
    return SimpleNamespace(page=page, content=content)


def test_prompt_numbers_sources_with_pages():
    prompt = build_prompt("How long is the warranty?", [chunk(2, "24 months"), chunk(5, "Six months")], [])
    assert "[1] (page 2)\n24 months" in prompt
    assert "[2] (page 5)\nSix months" in prompt
    assert prompt.endswith("QUESTION: How long is the warranty?")


def test_prompt_includes_recent_history_only():
    history = [SimpleNamespace(role="user", content=f"q{i}") for i in range(10)]
    prompt = build_prompt("next?", [chunk(1, "x")], history)
    assert "USER: q9" in prompt and "USER: q5" not in prompt


def test_sources_only_include_cited_passages():
    chunks = [chunk(1, "alpha"), chunk(4, "beta"), chunk(7, "gamma")]
    sources = make_sources("Answer [3] and also [1].", chunks)
    assert [(s["number"], s["page"]) for s in sources] == [(1, 1), (3, 7)]


def test_long_excerpts_are_trimmed_on_a_word_boundary():
    sources = make_sources("[1]", [chunk(1, "word " * 200)], excerpt_len=50)
    assert sources[0]["excerpt"].endswith("…") and len(sources[0]["excerpt"]) <= 51


def test_cited_numbers():
    assert cited_numbers("a [1][2] b [10]") == {1, 2, 10}
