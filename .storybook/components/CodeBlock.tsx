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
import { oneDark, oneLight } from "react-syntax-highlighter/dist/esm/styles/prism"

import type { Theme } from "../addon-theme/constants"

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

type CodeBlockProps = ComponentPropsWithoutRef<"pre"> & {
  theme: Theme
}

export const CodeBlock = ({ children, theme, ...preProps }: CodeBlockProps) => {
  const [copied, setCopied] = useState(false)
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
    await navigator.clipboard.writeText(code)
    setCopied(true)
    window.setTimeout(() => setCopied(false), 1600)
  }

  return (
    <div className="docblock-source specx-code-block">
      <SyntaxHighlighter
        codeTagProps={{ className: requestedLanguage ? `language-${requestedLanguage}` : undefined }}
        customStyle={{ background: "transparent", margin: 0, padding: "20px 20px 32px" }}
        language={language}
        style={theme === "dark" ? oneDark : oneLight}
        wrapLongLines={false}
      >
        {code}
      </SyntaxHighlighter>
      <button
        aria-label="Copy code"
        className="specx-code-copy"
        onClick={copyCode}
        type="button"
      >
        {copied ? "Copied" : "Copy"}
      </button>
    </div>
  )
}
