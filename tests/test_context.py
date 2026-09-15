from types import SimpleNamespace
from backend.context import generation_history


def test_prior_artifact_is_available_and_citations_are_remapped():
    message = SimpleNamespace(id='m', role='assistant', content='Your document is ready.', details={})
    artifact = SimpleNamespace(message_id='m', content='Interview weekly [S1]. Compare pricing [S2].',
                               sources=[{'label':'S1','chunk_id':'a'}, {'label':'S2','chunk_id':'b'}])
    result = generation_history([message], artifact, [{'label':'S4','chunk_id':'a'}])
    assert 'Interview weekly [S4]' in result[0].content
    assert '[S2]' not in result[0].content
    assert 'not evidence' in result[0].content


def test_unrelated_artifact_is_not_included_and_history_is_bounded():
    messages = [SimpleNamespace(id=str(i), role='user', content='x'*1000, details={}) for i in range(8)]
    artifact = SimpleNamespace(message_id='other-session', content='Private unrelated document')
    result = generation_history(messages, artifact, [])
    assert len(result) == 6
    assert all(len(m.content) < 700 for m in result)
    assert all('Private' not in m.content for m in result)
