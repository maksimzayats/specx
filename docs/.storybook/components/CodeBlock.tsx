import { Children, isValidElement, useState, type ComponentPropsWithoutRef, type ReactNode } from "react"
import { PrismLight as SyntaxHighlighter } from "react-syntax-highlighter"
import bash from "react-syntax-highlighter/dist/esm/languages/prism/bash"
import http from "react-syntax-highlighter/dist/esm/languages/prism/http"
import ini from "react-syntax-highlighter/dist/esm/languages/prism/ini"
import json from "react-syntax-highlighter/dist/esm/languages/prism/json"
import markup from "react-syntax-highlighter/dist/esm/languages/prism/markup"
import properties from "react-syntax-highlighter/dist/esm/languages/prism/properties"
import python from "react-syntax-highlighter/dist/esm/languages/prism/python"
import toml from "react-syntax-highlighter/dist/esm/languages/prism/toml"
import tsx from "react-syntax-highlighter/dist/esm/languages/prism/tsx"
import typescript from "react-syntax-highlighter/dist/esm/languages/prism/typescript"
import yaml from "react-syntax-highlighter/dist/esm/languages/prism/yaml"

SyntaxHighlighter.registerLanguage("bash", bash)
SyntaxHighlighter.registerLanguage("http", http)
SyntaxHighlighter.registerLanguage("ini", ini)
SyntaxHighlighter.registerLanguage("json", json)
SyntaxHighlighter.registerLanguage("markup", markup)
SyntaxHighlighter.registerLanguage("properties", properties)
SyntaxHighlighter.registerLanguage("python", python)
SyntaxHighlighter.registerLanguage("toml", toml)
SyntaxHighlighter.registerLanguage("tsx", tsx)
SyntaxHighlighter.registerLanguage("typescript", typescript)
SyntaxHighlighter.registerLanguage("yaml", yaml)

const languageAliases: Record<string, string | undefined> = {
  dotenv: "properties",
  html: "markup",
  md: "markup",
  sh: "bash",
  shell: "bash",
  text: undefined,
  ts: "typescript",
  yml: "yaml",
}

type CodeElementProps = {
  children?: ReactNode
  className?: string
}

type CodeBlockProps = ComponentPropsWithoutRef<"pre">

export const CodeBlock = ({ children, ...preProps }: CodeBlockProps) => {
  const [copyStatus, setCopyStatus] = useState<"idle" | "copied" | "error">("idle")
  const codeElement = Children.toArray(children).find(isValidElement)

  if (!codeElement) {
    return <pre {...preProps}>{children}</pre>
  }

  const codeProps = codeElement.props as CodeElementProps
  const requestedLanguage = codeProps.className?.match(/language-([\w-]+)/)?.[1]
  const language = requestedLanguage
    ? (languageAliases[requestedLanguage] ?? requestedLanguage)
    : undefined
  const code = String(codeProps.children ?? "").replace(/\n$/, "")

  const copyCode = async () => {
    try {
      await navigator.clipboard.writeText(code)
      setCopyStatus("copied")
    } catch {
      setCopyStatus("error")
    }
    window.setTimeout(() => setCopyStatus("idle"), 1600)
  }

  const copyLabel =
    copyStatus === "copied" ? "Copied code" : copyStatus === "error" ? "Copy failed" : "Copy code"
  const HighlightedPre = ({
    children: highlightedChildren,
    className,
    style,
    ...highlightedProps
  }: ComponentPropsWithoutRef<"pre">) => (
    <pre
      {...preProps}
      {...highlightedProps}
      className={[preProps.className, className].filter(Boolean).join(" ") || undefined}
      style={{ ...preProps.style, ...style }}
      tabIndex={preProps.tabIndex ?? 0}
    >
      {highlightedChildren}
    </pre>
  )

  return (
    <div className="docblock-source specx-code-block">
      <SyntaxHighlighter
        PreTag={HighlightedPre}
        codeTagProps={{ className: requestedLanguage ? `language-${requestedLanguage}` : undefined }}
        language={language}
        showInlineLineNumbers={false}
        showLineNumbers={false}
        useInlineStyles={false}
        wrapLongLines={false}
      >
        {code}
      </SyntaxHighlighter>
      <button
        aria-label={copyLabel}
        aria-live="polite"
        className="specx-code-copy"
        onClick={copyCode}
        type="button"
      >
        {copyStatus === "copied" ? "Copied" : copyStatus === "error" ? "Retry" : "Copy"}
      </button>
    </div>
  )
}
