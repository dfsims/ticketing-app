import { useState, useEffect } from 'react'
import './App.css'

interface Ticket {
  ticket_id: number
  title: string
  status: 'open' | 'in_progress' | 'resolved' | 'closed'
  created_by: string | null
  created_at: string
}

interface Message {
  message_id: number
  ticket_id: number
  message_text: string
  author: string | null
  created_at: string
}

function App() {
  const [tickets, setTickets] = useState<Ticket[]>([])
  const [selectedTicket, setSelectedTicket] = useState<Ticket | null>(null)
  const [messages, setMessages] = useState<Message[]>([])
  const [loading, setLoading] = useState(true)
  const [showNewTicket, setShowNewTicket] = useState(false)
  const [newMessage, setNewMessage] = useState('')
  const [author, setAuthor] = useState('Anonymous')
  
  // New ticket form
  const [newTicket, setNewTicket] = useState({
    title: '',
    created_by: 'Anonymous'
  })

  useEffect(() => {
    loadTickets()
  }, [])

  useEffect(() => {
    if (selectedTicket) {
      loadMessages(selectedTicket.ticket_id)
    }
  }, [selectedTicket])

  const loadTickets = async () => {
    try {
      const response = await fetch('/api/tickets')
      const data = await response.json()
      setTickets(data)
      setLoading(false)
    } catch (error) {
      console.error('Error loading tickets:', error)
      setLoading(false)
    }
  }

  const loadMessages = async (ticketId: number) => {
    try {
      const response = await fetch(`/api/tickets/${ticketId}/messages`)
      const data = await response.json()
      setMessages(data)
    } catch (error) {
      console.error('Error loading messages:', error)
    }
  }

  const createTicket = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      const response = await fetch('/api/tickets', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(newTicket)
      })
      const data = await response.json()
      setTickets([data, ...tickets])
      setNewTicket({ title: '', created_by: 'Anonymous' })
      setShowNewTicket(false)
    } catch (error) {
      console.error('Error creating ticket:', error)
    }
  }

  const addMessage = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!selectedTicket || !newMessage.trim()) return
    
    try {
      const response = await fetch(`/api/tickets/${selectedTicket.ticket_id}/messages`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: newMessage, author })
      })
      const data = await response.json()
      setMessages([...messages, data])
      setNewMessage('')
    } catch (error) {
      console.error('Error adding message:', error)
    }
  }

  const updateStatus = async (ticketId: number, status: string) => {
    try {
      const response = await fetch(`/api/tickets/${ticketId}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ status })
      })
      const updatedTicket = await response.json()
      setTickets(tickets.map(t => t.ticket_id === ticketId ? updatedTicket : t))
      if (selectedTicket?.ticket_id === ticketId) {
        setSelectedTicket(updatedTicket)
      }
    } catch (error) {
      console.error('Error updating status:', error)
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'open': return 'var(--status-open)'
      case 'in_progress': return 'var(--status-in-progress)'
      case 'resolved': return 'var(--status-resolved)'
      case 'closed': return 'var(--status-closed)'
      default: return 'var(--text-secondary)'
    }
  }

  const getPriorityColor = (priority: string) => {
    return 'var(--text-secondary)'
  }

  if (loading) {
    return (
      <div className="loading-container">
        <div className="loading-spinner"></div>
        <p>Loading tickets...</p>
      </div>
    )
  }

  return (
    <div className="app">
      <header className="app-header">
        <h1 className="app-title">
          <span className="neon-text">Support</span> Tickets
        </h1>
        <button className="btn-primary" onClick={() => setShowNewTicket(true)}>
          + New Ticket
        </button>
      </header>

      <div className="app-content">
        {/* Ticket List */}
        <aside className="ticket-list">
          <div className="ticket-list-header">
            <h2>All Tickets</h2>
            <span className="ticket-count">{tickets.length}</span>
          </div>
          <div className="tickets">
            {tickets.map(ticket => (
              <div
                key={ticket.ticket_id}
                className={`ticket-item ${selectedTicket?.ticket_id === ticket.ticket_id ? 'active' : ''}`}
                onClick={() => setSelectedTicket(ticket)}
              >
                <div className="ticket-item-header">
                  <h3>{ticket.title}</h3>
                </div>
                <div className="ticket-item-meta">
                  <span
                    className="status-badge"
                    style={{ color: getStatusColor(ticket.status) }}
                  >
                    {ticket.status.replace('_', ' ')}
                  </span>
                  <span className="ticket-id">#{ticket.ticket_id}</span>
                </div>
              </div>
            ))}
          </div>
        </aside>

        {/* Ticket Detail */}
        <main className="ticket-detail">
          {selectedTicket ? (
            <>
              <div className="ticket-detail-header">
                <div>
                  <h2>{selectedTicket.title}</h2>
                </div>
                <div className="ticket-actions">
                  <select
                    className="status-select"
                    value={selectedTicket.status}
                    onChange={(e) => updateStatus(selectedTicket.ticket_id, e.target.value)}
                    style={{ borderColor: getStatusColor(selectedTicket.status) }}
                  >
                    <option value="open">Open</option>
                    <option value="in_progress">In Progress</option>
                    <option value="resolved">Resolved</option>
                    <option value="closed">Closed</option>
                  </select>
                </div>
              </div>

              <div className="ticket-info">
                <div className="info-item">
                  <span className="info-label">Created:</span>
                  <span>{new Date(selectedTicket.created_at).toLocaleString()}</span>
                </div>
                <div className="info-item">
                  <span className="info-label">Created by:</span>
                  <span>{selectedTicket.created_by || 'Anonymous'}</span>
                </div>
              </div>

              <div className="messages-section">
                <h3>Messages</h3>
                <div className="messages">
                  {messages.map(msg => (
                    <div key={msg.message_id} className="message">
                      <div className="message-header">
                        <span className="message-author">{msg.author || 'Anonymous'}</span>
                        <span className="message-time">
                          {new Date(msg.created_at).toLocaleString()}
                        </span>
                      </div>
                      <p className="message-text">{msg.message_text}</p>
                    </div>
                  ))}
                </div>

                <form onSubmit={addMessage} className="message-form">
                  <input
                    type="text"
                    className="author-input"
                    placeholder="Your name"
                    value={author}
                    onChange={(e) => setAuthor(e.target.value)}
                  />
                  <div className="message-input-wrapper">
                    <textarea
                      className="message-input"
                      placeholder="Type your message..."
                      value={newMessage}
                      onChange={(e) => setNewMessage(e.target.value)}
                      rows={3}
                    />
                    <button type="submit" className="btn-send" disabled={!newMessage.trim()}>
                      Send
                    </button>
                  </div>
                </form>
              </div>
            </>
          ) : (
            <div className="empty-state">
              <div className="empty-icon">📋</div>
              <h2>Select a ticket</h2>
              <p>Choose a ticket from the list to view details and messages</p>
            </div>
          )}
        </main>
      </div>

      {/* New Ticket Modal */}
      {showNewTicket && (
        <div className="modal-overlay" onClick={() => setShowNewTicket(false)}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2>Create New Ticket</h2>
              <button className="modal-close" onClick={() => setShowNewTicket(false)}>
                ×
              </button>
            </div>
            <form onSubmit={createTicket} className="modal-form">
              <div className="form-group">
                <label>Title</label>
                <input
                  type="text"
                  required
                  value={newTicket.title}
                  onChange={(e) => setNewTicket({ ...newTicket, title: e.target.value })}
                  placeholder="Brief description of the issue"
                />
              </div>
              <div className="form-group">
                <label>Your Name</label>
                <input
                  type="text"
                  value={newTicket.created_by}
                  onChange={(e) => setNewTicket({ ...newTicket, created_by: e.target.value })}
                  placeholder="Your name"
                />
              </div>
              <div className="modal-actions">
                <button type="button" className="btn-secondary" onClick={() => setShowNewTicket(false)}>
                  Cancel
                </button>
                <button type="submit" className="btn-primary">
                  Create Ticket
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}

export default App 