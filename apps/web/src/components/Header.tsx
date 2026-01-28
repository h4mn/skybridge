import { Navbar, Nav, Container } from 'react-bootstrap'
import { Link } from 'react-router-dom'

/**
 * Header/Navbar principal do Skybridge WebUI.
 * Dividido em 2 linhas: brand em cima, links em baixo (sempre visíveis).
 */
export default function Header() {
  return (
    <Navbar bg="dark" variant="dark" className="mb-4">
      <Container fluid>
        <div style={{ display: 'grid', gridTemplateRows: 'auto auto', gap: '0.25rem', width: '100%' }}>
          {/* Linha 1: Brand */}
          <div>
            <Navbar.Brand as={Link} to="/">
              <strong>Skybridge</strong> WebUI
            </Navbar.Brand>
          </div>

          {/* Linha 2: Links */}
          <Nav className="me-auto">
            <Nav.Link as={Link} to="/">Dashboard</Nav.Link>
            <Nav.Link as={Link} to="/jobs">Jobs</Nav.Link>
            <Nav.Link as={Link} to="/worktrees">Worktrees</Nav.Link>
            <Nav.Link as={Link} to="/logs">Logs</Nav.Link>
            <Nav.Link as={Link} to="/settings">Settings</Nav.Link>
          </Nav>
        </div>
      </Container>
    </Navbar>
  )
}
