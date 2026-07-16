import React, { type ReactNode } from "react"

type DocsCardProps = {
  href: string
  icon: ReactNode
  title: string
  subtitle: string
}

export const DocsCard = ({ href, icon, title, subtitle }: DocsCardProps) => (
  <a className="specx-card" href={href} target="_top">
    <span className="specx-card-inner">
      <span aria-hidden="true" className="specx-card-icon">
        {icon}
      </span>
      <span className="specx-card-title">{title}</span>
      <span className="specx-card-subtitle">{subtitle}</span>
    </span>
  </a>
)
