import sys

sys.path.insert(0, ".")

from agent import get_direct_answer
from search_router import build_search_query, needs_search


def test_direct_answers_are_small():
    assert get_direct_answer("Salam") is not None
    assert get_direct_answer("slt") is not None
    assert get_direct_answer("Kat 3rf Dofus Touch ?") is None
    assert get_direct_answer("Chr7 lia chno hwa") is None


def test_current_info_requires_search():
    assert needs_search("Chno ljaw lyoum f Casa ?") is True
    assert needs_search("Ch7al taman dyal iPhone daba ?") is True
    assert needs_search("Chno kayn match lyoum ?") is True


def test_general_knowledge_does_not_require_search():
    assert needs_search("Chno hwa Dofus Touch ?") is False
    assert needs_search("Wach nta mred ?") is False
    assert needs_search("Rasy ki darni liom") is False


def test_query_builder_uses_current_context():
    assert "Casablanca Morocco" in build_search_query("Chno ljaw lyoum f Casa ?")
    assert "today" in build_search_query("Chno ljaw lyoum f Casa ?")
    assert "Botola Pro" in build_search_query("Chno les matchs dial botola pro had simana ?")


def test_contextual_followups():
    msg = "Chr7 lia chno hwa"
    history = [
        {"role": "user", "content": "Kat 3rf Dofus Touch ?"},
        {"role": "assistant", "content": "Eya, Dofus Touch hiya..."},
    ]
    assert needs_search(msg, history) is False


if __name__ == "__main__":
    test_direct_answers_are_small()
    test_current_info_requires_search()
    test_general_knowledge_does_not_require_search()
    test_query_builder_uses_current_context()
    test_contextual_followups()
    print("All Darija context tests passed.")
