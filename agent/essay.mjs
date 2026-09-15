export function cleanSection(text, position) {
 let blocks=text.trim().split(/\n\s*\n/);
 blocks=blocks.filter(b=>!/^SECTION TASK:|^Continue the (?:SAME )?essay\.|^Write ONLY|^For this turn ONLY/i.test(b.trim()));
 if(position===0) {
  return blocks.join('\n\n').replace(/^#{1,6}\s*Headline\s*\n+/i,'# ').replace(/^#{1,6}\s*Opening Hook\s*\n+/gim,'').trim();
 }
 const cleaned=[];
 for(let i=0;i<blocks.length;i++) {
  if(/^#{1,6}\s*Headline\s*$/i.test(blocks[i].trim())){i++;continue;}
  const block=blocks[i].replace(/^#{1,6}\s*Headline\s*\n[^\n]*(?:\n|$)/i,'').replace(/^#{1,6}[^\n]*(?:\n|$)/gm,'').trim();
  if(block)cleaned.push(block);
 }
 const headings=['','Start with the evidence','Apply it to one decision','Understand the trade-off','Try a small experiment','Review what you learn','One implementation constraint'];
 return '## '+(headings[position]||'Your next step')+'\n\n'+cleaned.join('\n\n');
}
export function countWords(text) {
 return (text.replace(/\[S\d+\]/g,' ').match(/\b[\p{L}\p{N}]+(?:['ÃƒÂ¢Ã¢â€šÂ¬Ã¢â€žÂ¢-][\p{L}\p{N}]+)*/gu)||[]).length;
}
export async function composeEssay(generate, inputPrompt) {
 const parts=[];
 async function add(instruction) {
  const outline=parts.map(p=>p.split('\n')[0]).join('\n');
  const content=cleanSection(await generate(inputPrompt+'\n\nExisting section headings (for continuity, not evidence):\n'+outline+'\n\n'+instruction),instruction.startsWith('Finish the essay')?99:parts.length);
  if(countWords(content)<45)throw new Error('The model returned an incomplete essay section.');
  parts.push(content);
  console.log(JSON.stringify({event:'essay_section',section:parts.length,words:countWords(content),total_words:countWords(parts.join('\n\n'))}));
 }
 await add('We will compose this essay in sections. For this turn ONLY write the headline and a 100-word opening hook, with a clear central argument. Do not write the body or conclusion yet. Cite the supplied evidence. Episode titles are not book titles. Never invent a book, personal anecdote or quotation.');
 const angles=[
 'Develop the central idea using the strongest supplied evidence. Explain what the guest actually says and why it matters. Bold the central idea once.',
 'Explain how the idea changes an everyday product decision. Label your suggested application explicitly; keep it separate from the guestÃƒÂ¢Ã¢â€šÂ¬Ã¢â€žÂ¢s actual advice.',
 'Explore a trade-off or limitation. Identify what the evidence does and does not support. Avoid repeating the opening or prior section.',
 'Offer a concrete, proposed experiment with steps and an observable outcome. Label it as your suggested application, not a guest quotation. Use a three-item bullet list with bold step labels.',
 'Explain how a team could review the experiment and decide its next action, without inventing results or promising success.'
 ];
 for(let i=0;i<angles.length;i++) {
  const remaining=1180-countWords(parts.join('\n\n'));
  const target=Math.max(80,Math.min(290,Math.round(remaining/(angles.length-i))));
  await add('Continue the SAME essay. Write ONLY the next body section, about '+target+' words, with its own descriptive ## heading and 3ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Å“4 developed paragraphs. '+angles[i]+' Use exact [S#] citations for evidence-based claims. No fabricated quotes, numbers, book titles or attribution. No conclusion yet. Do not reproduce earlier sections.');
 }
 if(countWords(parts.join('\n\n'))<1030) {
  await add('Write one additional, non-repetitive body section of '+(1130-countWords(parts.join('\n\n')))+' words. Explain a useful implementation constraint as a proposed application, clearly separated from the supplied evidence. Give a descriptive ## heading. Cite any guest-specific claims. Return only this section.');
 }
 await add('Finish the essay with ONLY a ## Your next step section of about '+Math.max(70,Math.min(140,1250-countWords(parts.join('\n\n'))))+' words. End with one concrete action the reader can take. Do not summarize every section or introduce new factual claims. Return only the closing section.');
 return parts.join('\n\n');
}
