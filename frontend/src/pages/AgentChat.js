import React, { useState, useRef, useEffect } from 'react';
import { 
  Card, 
  Input, 
  Button, 
  Select, 
  Avatar, 
  List, 
  Space, 
  Spin, 
  Tag,
  message as antMessage 
} from 'antd';
import {
  RobotOutlined,
  UserOutlined,
  SendOutlined,
  ClockCircleOutlined,
  CheckSquareOutlined,
  FileTextOutlined,
  TeamOutlined,
} from '@ant-design/icons';
import { agentAPI } from '../services/api';
import { useAuth } from '../contexts/AuthContext';
import moment from 'moment';
import './AgentChat.css';

const { TextArea } = Input;
const { Option } = Select;

const AgentChat = () => {
  const { user } = useAuth();
  const [messages, setMessages] = useState([]);
  const [inputValue, setInputValue] = useState('');
  const [selectedAgent, setSelectedAgent] = useState('clock');
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef(null);

  const agentInfo = {
    clock: {
      name: 'Clock Management Agent',
      icon: <ClockCircleOutlined />,
      color: '#1890ff',
      examples: [
        'Clock me in',
        'Clock me out',
        'Am I clocked in?',
        'Show my hours this week',
      ],
    },
    task: {
      name: 'Task Management Agent',
      icon: <CheckSquareOutlined />,
      color: '#52c41a',
      examples: [
        'Show my tasks',
        'Create a task for updating the website',
        'Mark task #5 as completed',
        'What tasks are due this week?',
      ],
    },
    report: {
      name: 'Report Generation Agent',
      icon: <FileTextOutlined />,
      color: '#722ed1',
      examples: [
        'Generate my weekly summary',
        'Create attendance report for last week',
        'Show task completion report',
        'Email me the monthly report',
      ],
    },
  };

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSend = async () => {
    if (!inputValue.trim()) return;

    const userMessage = {
      id: Date.now(),
      type: 'user',
      content: inputValue,
      timestamp: new Date(),
    };

    setMessages(prev => [...prev, userMessage]);
    setInputValue('');
    setLoading(true);

    try {
      const response = await agentAPI.execute({
        agent_type: selectedAgent,
        action: 'process_natural_language',
        parameters: { 
          query: inputValue,
          user_id: user.id,
        },
        context: {
          conversation_history: messages.slice(-10), // Last 10 messages
        },
      });

      const agentMessage = {
        id: Date.now() + 1,
        type: 'agent',
        agent: selectedAgent,
        content: response.data.output,
        timestamp: new Date(),
        success: response.data.success,
        executionTime: response.data.execution_time_ms,
      };

      setMessages(prev => [...prev, agentMessage]);

      if (!response.data.success) {
        antMessage.error('Agent encountered an error');
      }
    } catch (error) {
      console.error('Error sending message:', error);
      antMessage.error('Failed to communicate with agent');
      
      const errorMessage = {
        id: Date.now() + 1,
        type: 'agent',
        agent: selectedAgent,
        content: 'Sorry, I encountered an error processing your request. Please try again.',
        timestamp: new Date(),
        success: false,
      };
      
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setLoading(false);
    }
  };

  const handleExampleClick = (example) => {
    setInputValue(example);
  };

  const renderMessage = (message) => {
    if (message.type === 'user') {
      return (
        <div className="message user-message">
          <Avatar icon={<UserOutlined />} />
          <div className="message-content">
            <div className="message-bubble">{message.content}</div>
            <div className="message-time">
              {moment(message.timestamp).format('HH:mm')}
            </div>
          </div>
        </div>
      );
    } else {
      const agent = agentInfo[message.agent];
      return (
        <div className="message agent-message">
          <Avatar 
            icon={agent?.icon || <RobotOutlined />} 
            style={{ backgroundColor: agent?.color }}
          />
          <div className="message-content">
            <div className="message-header">
              <span className="agent-name">{agent?.name}</span>
              {message.executionTime && (
                <Tag color="default" size="small">
                  {message.executionTime}ms
                </Tag>
              )}
            </div>
            <div className={`message-bubble ${!message.success ? 'error' : ''}`}>
              {message.content}
            </div>
            <div className="message-time">
              {moment(message.timestamp).format('HH:mm')}
            </div>
          </div>
        </div>
      );
    }
  };

  return (
    <div className="agent-chat">
      <Card className="chat-container">
        <div className="chat-header">
          <Select
            value={selectedAgent}
            onChange={setSelectedAgent}
            style={{ width: 250 }}
          >
            {Object.entries(agentInfo).map(([key, info]) => (
              <Option key={key} value={key}>
                <Space>
                  {info.icon}
                  {info.name}
                </Space>
              </Option>
            ))}
          </Select>
        </div>

        <div className="messages-container">
          {messages.length === 0 ? (
            <div className="welcome-message">
              <Avatar 
                size={64} 
                icon={agentInfo[selectedAgent].icon}
                style={{ backgroundColor: agentInfo[selectedAgent].color }}
              />
              <h3>Hi {user?.full_name}! I'm your {agentInfo[selectedAgent].name}</h3>
              <p>Try asking me something like:</p>
              <Space direction="vertical" className="examples">
                {agentInfo[selectedAgent].examples.map((example, index) => (
                  <Button
                    key={index}
                    type="dashed"
                    onClick={() => handleExampleClick(example)}
                  >
                    "{example}"
                  </Button>
                ))}
              </Space>
            </div>
          ) : (
            <>
              {messages.map(message => (
                <div key={message.id}>
                  {renderMessage(message)}
                </div>
              ))}
              {loading && (
                <div className="message agent-message">
                  <Avatar 
                    icon={agentInfo[selectedAgent].icon}
                    style={{ backgroundColor: agentInfo[selectedAgent].color }}
                  />
                  <div className="message-content">
                    <div className="message-bubble">
                      <Spin size="small" /> Thinking...
                    </div>
                  </div>
                </div>
              )}
              <div ref={messagesEndRef} />
            </>
          )}
        </div>

        <div className="input-container">
          <TextArea
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onPressEnter={(e) => {
              if (!e.shiftKey) {
                e.preventDefault();
                handleSend();
              }
            }}
            placeholder="Type your message..."
            autoSize={{ minRows: 1, maxRows: 4 }}
            disabled={loading}
          />
          <Button
            type="primary"
            icon={<SendOutlined />}
            onClick={handleSend}
            loading={loading}
            disabled={!inputValue.trim()}
          >
            Send
          </Button>
        </div>
      </Card>
    </div>
  );
};

export default AgentChat;