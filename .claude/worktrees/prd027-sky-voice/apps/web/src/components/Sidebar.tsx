import { useState } from 'react'
import SidebarItem from './SidebarItem'

export interface SidebarItemData {
  id: string
  label: string
  icon: string
  path: string
  badge?: string
  disabled?: boolean
}

export interface SidebarSection {
  title?: string
  items: SidebarItemData[]
}

interface SidebarProps {
  sections: SidebarSection[]
}

export default function Sidebar({ sections }: SidebarProps) {
  const [collapsed, setCollapsed] = useState(false)

  return (
    <aside className={`sidebar ${collapsed ? 'collapsed' : ''}`}>
      {/* Toggle Button */}
      <button
        className="sidebar-toggle btn btn-link text-white"
        onClick={() => setCollapsed(!collapsed)}
        aria-label={collapsed ? 'Expandir sidebar' : 'Colapsar sidebar'}
      >
        {collapsed ? '▶' : '◀'}
      </button>

      {/* Items */}
      <nav className="sidebar-nav">
        {sections.map((section, idx) => (
          <div key={idx} className="sidebar-section">
            {section.title && !collapsed && (
              <h6 className="sidebar-section-title px-3 mt-4 mb-2 text-uppercase text-muted">
                {section.title}
              </h6>
            )}
            {section.items.map(item => (
              <SidebarItem
                key={item.id}
                {...item}
                collapsed={collapsed}
              />
            ))}
          </div>
        ))}
      </nav>
    </aside>
  )
}
