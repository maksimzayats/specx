import React, { useLayoutEffect } from "react"

export const HideTableOfContents = () => {
  useLayoutEffect(() => {
    document.documentElement.setAttribute("data-docs-toc", "hidden")

    return () => document.documentElement.removeAttribute("data-docs-toc")
  }, [])

  return (
    <style>
      {`.sbdocs-wrapper > div:has(div > .toc-wrapper) { display: none; }`}
    </style>
  )
}
