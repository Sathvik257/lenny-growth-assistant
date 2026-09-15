from backend.editing import fit_essay
from backend.service import word_count

def paragraph(prefix, size):
    return prefix+' '+('customer interviews product decisions feedback '*size).strip()+'.'

def test_short_essay_is_unchanged():
    source='# A title\n\nA useful opening.\n\n## Your next step\n\nDo one thing.'
    assert fit_essay(source)==(source,0)

def test_edit_preserves_sections_and_takeaway_without_cutting_sentences():
    blocks=['# A title',paragraph('Opening',20)]
    for i in range(5):
        blocks += [f'## Section {i}',paragraph(f'Lead{i}',20),paragraph(f'Detail{i}',50)]
    blocks += ['## Your next step',paragraph('Takeaway',20)]
    source='\n\n'.join(blocks)
    edited, removed=fit_essay(source)
    assert removed>0 and 1100<=word_count(edited)<=1400
    assert all(f'## Section {i}' in edited and f'Lead{i}' in edited for i in range(5))
    assert edited.endswith(blocks[-1])
    assert all(block in blocks for block in edited.split('\n\n'))
