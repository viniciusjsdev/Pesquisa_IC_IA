import { Fragment } from 'react';

function inline(text: string) {
  return text.split(/(\*\*[^*]+\*\*|`[^`]+`)/g).map((part, index) => {
    if (part.startsWith('**') && part.endsWith('**')) return <strong key={index}>{part.slice(2, -2)}</strong>;
    if (part.startsWith('`') && part.endsWith('`')) return <code key={index}>{part.slice(1, -1)}</code>;
    return <Fragment key={index}>{part}</Fragment>;
  });
}

export function ReadableAnswer({ text }: { text: string }) {
  return <div className="bench-readable-answer">{text.trim().split(/\n\s*\n/).map((block, index) => {
    const lines = block.split('\n');
    return lines.every(line => /^[-*]\s/.test(line))
      ? <ul key={index}>{lines.map((line, itemIndex) => <li key={itemIndex}>{inline(line.replace(/^[-*]\s/, ''))}</li>)}</ul>
      : <p key={index}>{inline(block)}</p>;
  })}</div>;
}
