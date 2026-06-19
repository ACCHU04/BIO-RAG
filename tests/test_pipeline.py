"""
Basic unit tests for tools and retriever.
Run: pytest tests/ -v
"""
import pytest
from unittest.mock import patch, MagicMock


def test_pubmed_search_returns_list():
    from app.tools.biomedical_tools import search_pubmed
    with patch("app.tools.biomedical_tools.Entrez.esearch") as mock_search, \
         patch("app.tools.biomedical_tools.Entrez.read") as mock_read, \
         patch("app.tools.biomedical_tools.Entrez.efetch") as mock_fetch:
        mock_read.side_effect = [{"IdList": []}, {}]
        result = search_pubmed("BRCA1 cancer", max_results=3)
        assert isinstance(result, list)


def test_uniprot_search_handles_failure():
    from app.tools.biomedical_tools import search_uniprot
    with patch("requests.get") as mock_get:
        mock_get.side_effect = Exception("Network error")
        result = search_uniprot("BRCA1")
        assert result == []


def test_open_targets_handles_failure():
    from app.tools.biomedical_tools import search_open_targets
    with patch("requests.post") as mock_post:
        mock_post.side_effect = Exception("Network error")
        result = search_open_targets("breast cancer")
        assert result == []


def test_retrieve_returns_list():
    from app.rag.retriever import retrieve
    with patch("app.rag.retriever.get_vectorstore") as mock_vs:
        mock_vs.return_value.similarity_search_with_relevance_scores.return_value = []
        result = retrieve("test query")
        assert isinstance(result, list)


def test_api_health(client=None):
    """Integration test — requires running server."""
    pass


def test_agent_reasoning_steps_no_duplication():
    from unittest.mock import patch, MagicMock
    
    mock_llm = MagicMock()
    mock_eval = MagicMock()
    mock_eval.content = '{"evaluation": "sufficient", "reason": "enough data"}'
    mock_synth = MagicMock()
    mock_synth.content = "synth answer"
    mock_llm.invoke.side_effect = [mock_eval, mock_synth]
    
    with patch("app.agent.graph.llm", mock_llm), \
         patch("app.agent.graph.retrieve_and_rerank") as mock_retrieve:
        mock_retrieve.return_value = [{"content": "Alzheimer is genetic", "source": "paper1.pdf", "score": 0.9}]
        
        from app.agent.graph import run_agent
        result = run_agent("Alzheimer genes")
        
        steps = result["reasoning_steps"]
        assert len(steps) == 3
        assert len(set(steps)) == len(steps)
        assert "Retrieved 1 chunks" in steps[0]
        assert "Evaluation: sufficient" in steps[1]
        assert "Synthesized" in steps[2]
        
        assert result["pubmed_articles_used"] == 0
        assert result["local_docs_used"] == 1

