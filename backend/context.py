"""Bounded conversation context with source labels remapped for the current turn."""
import re
from types import SimpleNamespace


def generation_history(messages, artifact, sources):
    current = {s.get('chunk_id'): s['label'] for s in sources if s.get('chunk_id')}
    result = []
    for message in messages[-6:]:
        content = message.content
        previous = (getattr(message, 'details', None) or {}).get('sources', [])
        budget = 600
        if artifact is not None and artifact.message_id == message.id:
            content = 'Previously created document (draft, not evidence):\n' + artifact.content
            previous = artifact.sources
            budget = 2400
        labels = {s['label']: current.get(s.get('chunk_id')) for s in previous}
        # Old S1 can refer to a different passage in a new turn.
        content = re.sub(r'\[(S\d+)\]', lambda m: '[' + labels[m[1]] + ']'
                         if labels.get(m[1]) else '(previous citation; verify against current evidence)', content)
        if len(content) > budget:
            content = content[:budget] + '\n[Earlier content truncated to fit model context.]'
        result.append(SimpleNamespace(role=message.role, content=content))
    return result
