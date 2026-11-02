"use client";

import { type ReactNode } from "react";
import { cn } from "@/lib/utils";

interface MarkdownMessageProps {
  content: string;
  className?: string;
}

/**
 * Parses inline markdown:
 * - **bold** or __bold__
 * - *italic* or _italic_
 * - `code`
 * - [label](url)
 */
function renderInline(text: string): ReactNode[] {
  // Regex matches:
  // 1. `code`
  // 2. **bold** or __bold__
  // 3. *italic* or _italic_
  // 4. [text](url)
  const regex = /(`[^`]+`|\*\*[^*]+\*\*|__[^_]+__|\*[^*]+\*|_[^_]+_|\[[^\]]+\]\([^)]+\))/g;
  const parts = text.split(regex);

  return parts.map((part, index) => {
    if (!part) return null;

    // Inline code: `code`
    if (part.startsWith("`") && part.endsWith("`") && part.length >= 2) {
      return (
        <code
          key={index}
          className="rounded bg-muted/80 px-1.5 py-0.5 font-mono text-xs text-foreground font-medium border border-border/40"
        >
          {part.slice(1, -1)}
        </code>
      );
    }

    // Bold: **text** or __text__
    if (
      (part.startsWith("**") && part.endsWith("**") && part.length >= 4) ||
      (part.startsWith("__") && part.endsWith("__") && part.length >= 4)
    ) {
      return (
        <strong key={index} className="font-semibold text-foreground">
          {part.slice(2, -2)}
        </strong>
      );
    }

    // Italic: *text* or _text_
    if (
      (part.startsWith("*") && part.endsWith("*") && part.length >= 2) ||
      (part.startsWith("_") && part.endsWith("_") && part.length >= 2)
    ) {
      return (
        <em key={index} className="italic text-foreground/90">
          {part.slice(1, -1)}
        </em>
      );
    }

    // Link: [text](url)
    const linkMatch = part.match(/^\[([^\]]+)\]\(([^)]+)\)$/);
    if (linkMatch) {
      const [, label, url] = linkMatch;
      return (
        <a
          key={index}
          href={url}
          target="_blank"
          rel="noopener noreferrer"
          className="text-primary font-medium underline underline-offset-2 hover:text-primary/80 transition-colors"
        >
          {label}
        </a>
      );
    }

    return <span key={index}>{part}</span>;
  });
}

type Block =
  | { type: "header"; level: number; text: string }
  | { type: "bold-header"; text: string }
  | { type: "code"; code: string; language?: string }
  | { type: "list"; ordered: boolean; items: string[] }
  | { type: "blockquote"; text: string }
  | { type: "paragraph"; text: string };

function parseBlocks(raw: string): Block[] {
  const lines = raw.split(/\r?\n/);
  const blocks: Block[] = [];
  let i = 0;

  while (i < lines.length) {
    const line = lines[i];
    const trimmed = line.trim();

    // Skip empty lines
    if (!trimmed) {
      i++;
      continue;
    }

    // Code block
    if (trimmed.startsWith("```")) {
      const language = trimmed.slice(3).trim();
      const codeLines: string[] = [];
      i++;
      while (i < lines.length && !lines[i].trim().startsWith("```")) {
        codeLines.push(lines[i]);
        i++;
      }
      if (i < lines.length) i++; // consume closing ```
      blocks.push({ type: "code", code: codeLines.join("\n"), language });
      continue;
    }

    // Headings: #, ##, ###, ####
    const headerMatch = trimmed.match(/^(#{1,6})\s+(.*)$/);
    if (headerMatch) {
      blocks.push({
        type: "header",
        level: headerMatch[1].length,
        text: headerMatch[2],
      });
      i++;
      continue;
    }

    // Standalone bold line acting as a section header: e.g. **Noticia en foco** or **Catálogo reciente:**
    const boldHeaderMatch = trimmed.match(/^\*\*([^*]+)\*\*[:]?$/);
    if (boldHeaderMatch) {
      blocks.push({
        type: "bold-header",
        text: boldHeaderMatch[1],
      });
      i++;
      continue;
    }

    // Blockquote
    if (trimmed.startsWith(">")) {
      const quoteLines: string[] = [];
      while (i < lines.length && lines[i].trim().startsWith(">")) {
        quoteLines.push(lines[i].trim().replace(/^>\s?/, ""));
        i++;
      }
      blocks.push({ type: "blockquote", text: quoteLines.join(" ") });
      continue;
    }

    // Unordered List (- or *)
    if (/^[-*]\s+/.test(trimmed)) {
      const items: string[] = [];
      while (i < lines.length && /^[-*]\s+/.test(lines[i].trim())) {
        items.push(lines[i].trim().replace(/^[-*]\s+/, ""));
        i++;
      }
      blocks.push({ type: "list", ordered: false, items });
      continue;
    }

    // Ordered List (1., 2., etc.)
    if (/^\d+\.\s+/.test(trimmed)) {
      const items: string[] = [];
      while (i < lines.length && /^\d+\.\s+/.test(lines[i].trim())) {
        items.push(lines[i].trim().replace(/^\d+\.\s+/, ""));
        i++;
      }
      blocks.push({ type: "list", ordered: true, items });
      continue;
    }

    // Standard paragraph: accumulate until empty line or block starter
    const paragraphLines: string[] = [trimmed];
    i++;
    while (
      i < lines.length &&
      lines[i].trim() &&
      !lines[i].trim().startsWith("#") &&
      !lines[i].trim().startsWith("```") &&
      !lines[i].trim().startsWith(">") &&
      !/^[-*]\s+/.test(lines[i].trim()) &&
      !/^\d+\.\s+/.test(lines[i].trim()) &&
      !/^\*\*([^*]+)\*\*[:]?$/.test(lines[i].trim())
    ) {
      paragraphLines.push(lines[i].trim());
      i++;
    }
    blocks.push({ type: "paragraph", text: paragraphLines.join(" ") });
  }

  return blocks;
}

export default function MarkdownMessage({ content, className }: MarkdownMessageProps) {
  if (!content) return null;

  const blocks = parseBlocks(content);

  return (
    <div className={cn("text-sm leading-relaxed space-y-2.5", className)}>
      {blocks.map((block, index) => {
        switch (block.type) {
          case "header": {
            if (block.level === 1) {
              return (
                <h1 key={index} className="text-lg font-bold text-foreground mt-3 mb-1 font-display">
                  {renderInline(block.text)}
                </h1>
              );
            }
            if (block.level === 2) {
              return (
                <h2 key={index} className="text-base font-bold text-foreground mt-3 mb-1 font-display">
                  {renderInline(block.text)}
                </h2>
              );
            }
            return (
              <h3 key={index} className="text-sm font-bold text-foreground mt-2.5 mb-1 tracking-wide uppercase text-xs text-primary">
                {renderInline(block.text)}
              </h3>
            );
          }

          case "bold-header":
            return (
              <div
                key={index}
                className="pt-2 pb-1 text-xs font-bold uppercase tracking-wider text-primary border-b border-border/40 first:pt-0"
              >
                {block.text}
              </div>
            );

          case "list":
            if (block.ordered) {
              return (
                <ol key={index} className="list-decimal pl-5 space-y-1.5 text-foreground/90 my-1.5">
                  {block.items.map((item, itemIdx) => (
                    <li key={itemIdx} className="pl-1">
                      {renderInline(item)}
                    </li>
                  ))}
                </ol>
              );
            }
            return (
              <ul key={index} className="list-disc pl-5 space-y-1.5 text-foreground/90 my-1.5 marker:text-primary">
                {block.items.map((item, itemIdx) => (
                  <li key={itemIdx} className="pl-1">
                    {renderInline(item)}
                  </li>
                ))}
              </ul>
            );

          case "blockquote":
            return (
              <blockquote
                key={index}
                className="border-l-2 border-primary/40 bg-muted/30 pl-3 py-1 italic text-muted-foreground my-2"
              >
                {renderInline(block.text)}
              </blockquote>
            );

          case "code":
            return (
              <pre
                key={index}
                className="overflow-x-auto rounded-lg bg-muted p-3 font-mono text-xs text-foreground border border-border/60 my-2"
              >
                <code>{block.code}</code>
              </pre>
            );

          case "paragraph":
          default:
            return (
              <p key={index} className="text-foreground/90 leading-relaxed">
                {renderInline(block.text)}
              </p>
            );
        }
      })}
    </div>
  );
}
