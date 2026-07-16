import React from "react"

import { docsHref, docsPages, type DocsPage } from "../docsNavigation"

const FooterLink = ({ direction, page }: { direction: "Next" | "Previous"; page: DocsPage }) => (
  <a className="specx-footer-link" href={docsHref(page.path)} target="_top">
    <span className="specx-footer-direction">{direction}</span>
    <span className="specx-footer-title">{page.title}</span>
  </a>
)

export const NextPrev = ({ current }: { current: string }) => {
  const currentIndex = docsPages.findIndex((page) => page.path === current)

  if (currentIndex === -1) {
    throw new Error(`Unknown documentation path: ${current}`)
  }

  const previousPage = docsPages[currentIndex - 1]
  const nextPage = docsPages[currentIndex + 1]

  return (
    <nav aria-label="Documentation pages" className="specx-footer-nav">
      {previousPage ? <FooterLink direction="Previous" page={previousPage} /> : <span />}
      {nextPage ? <FooterLink direction="Next" page={nextPage} /> : <span />}
    </nav>
  )
}
