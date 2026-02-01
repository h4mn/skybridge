import { Container } from 'react-bootstrap'
import EventStream from '../components/EventStream'

export default function Events() {
  return (
    <Container fluid>
      <h2 className="mb-4">🎭 Eventos de Domínio</h2>

      <p className="text-muted mb-4">
        Monitoramento em tempo real dos eventos de domínio do Skybridge.
        JobCreatedEvent, JobStartedEvent, JobCompletedEvent, JobFailedEvent, etc.
      </p>

      <EventStream />
    </Container>
  )
}
