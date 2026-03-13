import React, { useState, useRef, useEffect } from 'react';
import './App.css';

function App() {
  const [conversations, setConversations] = useState(() => {
    const saved = localStorage.getItem('chatConversations');
    return saved ? JSON.parse(saved) : [];
  });
  const [currentConversationId, setCurrentConversationId] = useState(() => {
    const saved = localStorage.getItem('currentConversation');
    return saved ? parseInt(saved) : null;
  });
  
  const [messages, setMessages] = useState(() => {
    const saved = localStorage.getItem('chatConversations');
    if (saved) {
      const convs = JSON.parse(saved);
      const currentId = localStorage.getItem('currentConversation');
      if (currentId) {
        const conv = convs.find(c => c.id === parseInt(currentId));
        return conv ? conv.messages : [{ text: 'Bienvenue. Je suis l\'assistant 2iE. Comment puis-je vous aider ?', sender: 'bot' }];
      }
    }
    return [{ text: 'Bienvenue. Je suis l\'assistant 2iE. Comment puis-je vous aider ?', sender: 'bot' }];
  });
  
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef(null);

  // Sauvegarder les conversations dans localStorage
  useEffect(() => {
    localStorage.setItem('chatConversations', JSON.stringify(conversations));
    localStorage.setItem('currentConversation', currentConversationId);
  }, [conversations, currentConversationId]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSend = () => {
    if (input.trim()) {
      const userMessage = { text: input, sender: 'student' };
      const newMessages = [...messages, userMessage];
      setMessages(newMessages);
      setInput('');
      setIsLoading(true);
      
      // Créer ou mettre à jour la conversation
      let updatedConversations = [...conversations];
      let convId = currentConversationId;
      
      if (!convId) {
        // Nouvelle conversation
        convId = Date.now();
        const newConv = {
          id: convId,
          title: input.slice(0, 50) + (input.length > 50 ? '...' : ''),
          messages: newMessages,
          timestamp: new Date().toLocaleString('fr-FR'),
          createdAt: Date.now()
        };
        updatedConversations = [newConv, ...updatedConversations].slice(0, 20);
      } else {
        // Mettre à jour la conversation existante
        updatedConversations = updatedConversations.map(conv => 
          conv.id === convId ? { ...conv, messages: newMessages, timestamp: new Date().toLocaleString('fr-FR') } : conv
        );
      }
      
      setConversations(updatedConversations);
      setCurrentConversationId(convId);
      
      // Call vers l'API Backend via Fetch
      fetch('http://localhost:8000/api/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ message: input })
      })
      .then(res => res.json())
      .then(data => {
        const botMessage = { 
          text: data.answer || "Désolé, je n'ai pas pu générer de réponse.",
          sender: 'bot'
        };
        const finalMessages = [...newMessages, botMessage];
        setMessages(finalMessages);
        
        // Mettre à jour la conversation avec la réponse du bot
        setConversations(prev => prev.map(conv =>
          conv.id === convId ? { ...conv, messages: finalMessages } : conv
        ));
      })
      .catch(error => {
        console.error("Erreur avec l'API Backend:", error);
        const botMessage = { 
          text: "Erreur de connexion au serveur. Vérifiez que l'API est démarrée sur le port 8000.",
          sender: 'bot'
        };
        setMessages([...newMessages, botMessage]);
      })
      .finally(() => {
        setIsLoading(false);
      });
    }
  };

  const startNewChat = () => {
    setMessages([{ text: 'Bienvenue. Je suis l\'assistant 2iE. Comment puis-je vous aider ?', sender: 'bot' }]);
    setInput('');
    setCurrentConversationId(null);
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const loadConversation = (conversationId) => {
    const conv = conversations.find(c => c.id === conversationId);
    if (conv) {
      setMessages(conv.messages);
      setCurrentConversationId(conversationId);
    }
  };

  const deleteConversation = (conversationId) => {
    setConversations(prev => prev.filter(c => c.id !== conversationId));
    if (currentConversationId === conversationId) {
      startNewChat();
    }
  };

  const clearAllHistory = () => {
    if (confirm('Êtes-vous sûr de vouloir effacer tout l\'historique des conversations ?')) {
      setConversations([]);
      setCurrentConversationId(null);
      startNewChat();
    }
  };

  return (
    <div className="app-wrapper">
      <div className="history-panel">
        <div className="history-header">
          <button className="glow-button" onClick={startNewChat}>
            Nouveau chat
          </button>
        </div>
        <div className="history-header-title">
          <h3>Historique</h3>
          <p className="history-subtitle">{conversations.length} conversation{conversations.length > 1 ? 's' : ''}</p>
        </div>
        {conversations.length > 0 ? (
          <div className="history-content">
            {conversations.map((conv) => (
              <div 
                key={conv.id}
                className="history-item"
                onClick={() => loadConversation(conv.id)}
                title={conv.title}
              >
                {conv.title}
              </div>
            ))}
          </div>
        ) : (
          <div className="history-empty">
            Aucune conversation sauvegardée
          </div>
        )}
        <div className="history-actions">
          <button className="history-btn" onClick={clearAllHistory}>Effacer tout</button>
        </div>
      </div>

      <div className="chat-container">
        <header className="chat-header">
          <div className="header-content">
            <div className="header-icon">
              <img src="./logo/images.jpeg" alt="2iE Logo" className="logo-img" />
            </div>
            <div className="header-text">
              <h1>Assistant 2iE</h1>
              <p className="header-subtitle">Aide académique et administrative</p>
            </div>
          </div>
          <div className="header-status">
            <span className="status-dot"></span>
            <span className="status-text">En ligne</span>
          </div>
        </header>

        <div className="chat-messages">
          {messages.length === 1 ? (
            <div className="welcome-section">
              <div className="welcome-icon"></div>
              <h2>Assistant 2iE</h2>
              <p>Support académique et administratif pour les étudiants</p>
            </div>
          ) : null}
          
          {messages.map((msg, index) => (
            <div
              key={index}
              className={`chat-message-wrapper ${msg.sender === 'student' ? 'student-wrapper' : 'bot-wrapper'}`}
            >
              <div className={`chat-message ${msg.sender === 'student' ? 'student' : 'bot'}`}>
                <span className="message-text">{msg.text}</span>
              </div>
            </div>
          ))}
          {isLoading && (
            <div className="chat-message-wrapper bot-wrapper">
              <div className="loading-indicator">
                <div className="Strich1">
                  <div className="Strich2">
                    <div className="bubble"></div>
                    <div className="bubble1"></div>
                    <div className="bubble2"></div>
                    <div className="bubble3"></div>
                  </div>
                </div>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        <div className="chat-input-area">
          <div className="search-orb-container">
            <div className="gooey-background-layer">
              <div className="blob blob-1"></div>
              <div className="blob blob-2"></div>
              <div className="blob blob-3"></div>
              <div className="blob-bridge"></div>
            </div>

            <div className="input-overlay">
              <div className="search-icon-wrapper">
                <svg
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2.5"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  className="search-icon"
                >
                  <circle cx="11" cy="11" r="8"></circle>
                  <line x1="21" y1="21" x2="16.65" y2="16.65"></line>
                </svg>
              </div>
              <textarea
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder="Posez votre question ici..."
                className="modern-input"
                rows="1"
              />
              <button 
                onClick={handleSend}
                className="send-button-star"
                title="Envoyer le message"
              >
                <svg
                  className="star-icon"
                  stroke="none"
                  viewBox="0 0 24 24"
                  fill="currentColor"
                >
                  <path
                    fillRule="evenodd"
                    clipRule="evenodd"
                    d="M9 4.5a.75.75 0 01.721.544l.813 2.846a3.75 3.75 0 002.576 2.576l2.846.813a.75.75 0 010 1.442l-2.846.813a3.75 3.75 0 00-2.576 2.576l-.813 2.846a.75.75 0 01-1.442 0l-.813-2.846a3.75 3.75 0 00-2.576-2.576l-2.846-.813a.75.75 0 010-1.442l2.846-.813A3.75 3.75 0 007.466 7.89l.813-2.846A.75.75 0 019 4.5zM18 1.5a.75.75 0 01.728.568l.258 1.036c.236.94.97 1.674 1.91 1.91l1.036.258a.75.75 0 010 1.456l-1.036.258c-.94.236-1.674.97-1.91 1.91l-.258 1.036a.75.75 0 01-1.456 0l-.258-1.036a2.625 2.625 0 00-1.91-1.91l-1.036-.258a.75.75 0 010-1.456l1.036-.258a2.625 2.625 0 001.91-1.91l.258-1.036A.75.75 0 0118 1.5zM16.5 15a.75.75 0 01.712.513l.394 1.183c.15.447.5.799.948.948l1.183.395a.75.75 0 010 1.422l-1.183.395c-.447.15-.799.5-.948.948l-.395 1.183a.75.75 0 01-1.422 0l-.395-1.183a1.5 1.5 0 00-.948-.948l-1.183-.395a.75.75 0 010-1.422l1.183-.395c.447-.15.799-.5.948-.948l.395-1.183A.75.75 0 0116.5 15z"
                  ></path>
                </svg>
              </button>
              <div className="focus-indicator"></div>
            </div>

            <svg className="gooey-svg-filter" xmlns="http://www.w3.org/2000/svg">
              <defs>
                <filter id="enhanced-goo">
                  <feGaussianBlur
                    in="SourceGraphic"
                    stdDeviation="12"
                    result="blur"
                  ></feGaussianBlur>
                  <feColorMatrix
                    in="blur"
                    mode="matrix"
                    values="1 0 0 0 0  0 1 0 0 0  0 0 1 0 0  0 0 0 20 -10"
                    result="goo"
                  ></feColorMatrix>
                  <feComposite in="SourceGraphic" in2="goo" operator="atop"></feComposite>
                </filter>
              </defs>
            </svg>
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;
