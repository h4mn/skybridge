import { NavLink } from 'react-router-dom'
import { Badge } from 'react-bootstrap'

interface SidebarItemProps {
  label: string
  icon: string
  path: string
  collapsed?: boolean
  badge?: string
}

export default function SidebarItem({ label, icon, path, collapsed, badge }: SidebarItemProps) {
  return (
    <NavLink
      to={path}
      className={({ isActive }) => `
        sidebar-item d-flex align-items-center px-3 py-2 mx-2 rounded
        ${isActive ? 'active' : ''}
        ${collapsed ? 'justify-content-center' : ''}
      `}
    >
      <span className="sidebar-icon">{icon}</span>
      {!collapsed && <span className="sidebar-label ms-3">{label}</span>}
      {badge && !collapsed && (
        <Badge bg="danger" className="ms-auto">{badge}</Badge>
      )}
    </NavLink>
  )
}
