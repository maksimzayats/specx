import React, { type ReactNode } from "react"

type DocsCardProps = {
  href: string
  icon: ReactNode
  title: string
  subtitle: string
}

export const DocsCard = ({ href, icon, title, subtitle }: DocsCardProps) => (
  <a className="specx-card" href={href}>
    <span className="specx-card-icon">{icon}</span>
    <h3 className="specx-card-title">{title}</h3>
    <p className="specx-card-subtitle">{subtitle}</p>
  </a>
)
