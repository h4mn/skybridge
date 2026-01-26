import { Navbar, Nav, Container } from 'react-bootstrap'
import { Link } from 'react-router-dom'

/**
 * Header/Navbar principal do Skybridge WebUI.
 */
export default function Header() {
  return (
    <Navbar bg="dark" variant="dark" expand="lg" className="mb-4">
      <Container fluid>
        <Navbar.Brand as={Link} to="/">
          <strong>Skybridge</strong> WebUI
        </Navbar.Brand>
        <Navbar.Toggle aria-controls="navbar-nav" />
        <Navbar.Collapse id="navbar-nav">
          <Nav className="me-auto">
            <Nav.Link as={Link} to="/">Dashboard</Nav.Link>
            <Nav.Link as={Link} to="/jobs">Jobs</Nav.Link>
            <Nav.Link as={Link} to="/worktrees">Worktrees</Nav.Link>
            <Nav.Link as={Link} to="/logs">Logs</Nav.Link>
            <Nav.Link as={Link} to="/settings">Settings</Nav.Link>
          </Nav>
        </Navbar.Collapse>
      </Container>
    </Navbar>
  )
}
