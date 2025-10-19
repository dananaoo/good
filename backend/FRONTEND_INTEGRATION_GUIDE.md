# 🎯 Frontend Integration Guide for AI Interview System

## 📋 **Overview**

This guide explains how to integrate the AI interview system with your frontend application. The system provides real-time chat functionality with AI evaluation and data storage.

## 🌐 **API Endpoints**

### **1. Create Interview**
```http
POST /api/interviews/
Content-Type: application/json
Authorization: Bearer <token>

{
  "vacancy_id": "uuid-of-vacancy",
  "candidate_id": "uuid-of-candidate"
}
```

**Response:**
```json
{
  "id": "interview-uuid",
  "status": "pending",
  "current_stage": "resume_fit",
  "started_at": "2024-01-20T10:00:00Z",
  "final_score": null,
  "summary_json": null
}
```

### **2. WebSocket Connection**
```javascript
const ws = new WebSocket('ws://localhost:8000/interviews/ws/{interview_id}');
```

**WebSocket Messages:**

**Send to AI:**
```json
{
  "type": "candidate_message",
  "message": "Yes, I am open to relocating to Almaty."
}
```

**Receive from AI:**
```json
{
  "type": "message",
  "sender": "bot",
  "message": "That's great to hear! Now let's talk about your technical skills...",
  "stage": "hard_skills",
  "message_type": "question"
}
```

**Interview Complete:**
```json
{
  "type": "interview_complete",
  "final_score": 87.5,
  "summary": {
    "overall_score": 87.5,
    "breakdown": {
      "resume_fit": 85,
      "hard_skills": 90,
      "soft_skills": 88
    },
    "reasoning": [
      "Strong alignment with job requirements",
      "Excellent technical competency"
    ],
    "ai_confidence": 0.9
  },
  "evaluation_saved": true
}
```

### **3. Get Interview Data**
```http
GET /api/interviews/{interview_id}/complete-evaluation
Authorization: Bearer <token>
```

**Response:**
```json
{
  "interview": {
    "id": "uuid",
    "status": "completed",
    "current_stage": "finished",
    "final_score": 87.5,
    "started_at": "2024-01-20T10:00:00Z",
    "ended_at": "2024-01-20T10:15:00Z"
  },
  "evaluation_scores": [
    {
      "id": "uuid",
      "category": "resume_fit",
      "score": 85.0,
      "weight": 1.0,
      "explanation": null
    },
    {
      "id": "uuid", 
      "category": "hard_skills",
      "score": 90.0,
      "weight": 1.0,
      "explanation": null
    }
  ],
  "evaluation_summary": {
    "id": "uuid",
    "overall_score": 87.5,
    "breakdown": {
      "resume_fit": 85,
      "hard_skills": 90,
      "soft_skills": 88
    },
    "reasoning": "Strong alignment with job requirements; Excellent technical competency",
    "ai_confidence": 0.9,
    "generated_at": "2024-01-20T10:15:00Z"
  },
  "chat_messages": [
    {
      "id": "uuid",
      "sender": "bot",
      "stage": "resume_fit",
      "message_type": "question",
      "message": "Hello! I'm conducting your interview...",
      "ai_generated": true,
      "created_at": "2024-01-20T10:00:00Z"
    },
    {
      "id": "uuid",
      "sender": "candidate",
      "stage": "resume_fit", 
      "message_type": "answer",
      "message": "Yes, I am open to relocating.",
      "ai_generated": false,
      "created_at": "2024-01-20T10:01:00Z"
    }
  ]
}
```

### **4. Get Individual Data**
```http
GET /api/interviews/{interview_id}/messages
GET /api/interviews/{interview_id}/evaluation-scores
GET /api/interviews/{interview_id}/evaluation-summary
```

## 🎨 **Frontend Implementation**

### **React Example:**
```jsx
import React, { useState, useEffect, useRef } from 'react';

const InterviewChat = ({ interviewId }) => {
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isConnected, setIsConnected] = useState(false);
  const [evaluation, setEvaluation] = useState(null);
  const wsRef = useRef(null);

  useEffect(() => {
    connectWebSocket();
    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, [interviewId]);

  const connectWebSocket = () => {
    const ws = new WebSocket(`ws://localhost:8000/interviews/ws/${interviewId}`);
    wsRef.current = ws;

    ws.onopen = () => {
      setIsConnected(true);
    };

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      
      if (data.type === 'message') {
        setMessages(prev => [...prev, {
          sender: 'ai',
          message: data.message,
          stage: data.stage
        }]);
      } else if (data.type === 'interview_complete') {
        setEvaluation(data.summary);
        setMessages(prev => [...prev, {
          sender: 'ai',
          message: '🎉 Interview completed!',
          stage: 'finished'
        }]);
      }
    };

    ws.onclose = () => {
      setIsConnected(false);
    };
  };

  const sendMessage = () => {
    if (inputMessage.trim() && wsRef.current) {
      setMessages(prev => [...prev, {
        sender: 'user',
        message: inputMessage
      }]);
      
      wsRef.current.send(JSON.stringify({
        type: 'candidate_message',
        message: inputMessage
      }));
      
      setInputMessage('');
    }
  };

  return (
    <div className="interview-chat">
      <div className="messages">
        {messages.map((msg, index) => (
          <div key={index} className={`message ${msg.sender}`}>
            {msg.message}
          </div>
        ))}
      </div>
      
      {evaluation && (
        <div className="evaluation">
          <h3>Final Evaluation</h3>
          <p>Overall Score: {evaluation.overall_score}%</p>
          <div>
            {Object.entries(evaluation.breakdown).map(([key, value]) => (
              <div key={key}>
                {key.replace('_', ' ').toUpperCase()}: {value}%
              </div>
            ))}
          </div>
        </div>
      )}
      
      <div className="input-area">
        <input
          value={inputMessage}
          onChange={(e) => setInputMessage(e.target.value)}
          onKeyPress={(e) => e.key === 'Enter' && sendMessage()}
          disabled={!isConnected}
          placeholder="Type your response..."
        />
        <button onClick={sendMessage} disabled={!isConnected}>
          Send
        </button>
      </div>
    </div>
  );
};
```

### **Vue.js Example:**
```vue
<template>
  <div class="interview-chat">
    <div class="messages">
      <div 
        v-for="(message, index) in messages" 
        :key="index"
        :class="['message', message.sender]"
      >
        {{ message.message }}
      </div>
    </div>
    
    <div v-if="evaluation" class="evaluation">
      <h3>Final Evaluation</h3>
      <p>Overall Score: {{ evaluation.overall_score }}%</p>
      <div v-for="(score, category) in evaluation.breakdown" :key="category">
        {{ category.replace('_', ' ').toUpperCase() }}: {{ score }}%
      </div>
    </div>
    
    <div class="input-area">
      <input
        v-model="inputMessage"
        @keypress.enter="sendMessage"
        :disabled="!isConnected"
        placeholder="Type your response..."
      />
      <button @click="sendMessage" :disabled="!isConnected">
        Send
      </button>
    </div>
  </div>
</template>

<script>
export default {
  data() {
    return {
      messages: [],
      inputMessage: '',
      isConnected: false,
      evaluation: null,
      ws: null
    };
  },
  mounted() {
    this.connectWebSocket();
  },
  beforeUnmount() {
    if (this.ws) {
      this.ws.close();
    }
  },
  methods: {
    connectWebSocket() {
      this.ws = new WebSocket(`ws://localhost:8000/interviews/ws/${this.interviewId}`);
      
      this.ws.onopen = () => {
        this.isConnected = true;
      };
      
      this.ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        
        if (data.type === 'message') {
          this.messages.push({
            sender: 'ai',
            message: data.message,
            stage: data.stage
          });
        } else if (data.type === 'interview_complete') {
          this.evaluation = data.summary;
          this.messages.push({
            sender: 'ai',
            message: '🎉 Interview completed!',
            stage: 'finished'
          });
        }
      };
      
      this.ws.onclose = () => {
        this.isConnected = false;
      };
    },
    
    sendMessage() {
      if (this.inputMessage.trim() && this.ws) {
        this.messages.push({
          sender: 'user',
          message: this.inputMessage
        });
        
        this.ws.send(JSON.stringify({
          type: 'candidate_message',
          message: this.inputMessage
        }));
        
        this.inputMessage = '';
      }
    }
  }
};
</script>
```

## 🔐 **Authentication**

All API endpoints require authentication. Include the token in headers:

```javascript
const headers = {
  'Content-Type': 'application/json',
  'Authorization': `Bearer ${userToken}`
};
```

## 🎯 **Interview Stages**

The AI conducts interviews in 3 stages:

1. **Resume Fit** - Basic requirements matching
2. **Hard Skills** - Technical competencies
3. **Soft Skills** - Communication and motivation

## 📊 **Evaluation Data**

The system stores:
- **Chat messages** with timestamps and stages
- **Individual scores** for each category
- **Overall evaluation** with reasoning
- **AI confidence** level

## 🚀 **Getting Started**

1. **Start your backend server:**
   ```bash
   python -m uvicorn app.main:app --reload
   ```

2. **Create an interview via API**

3. **Connect to WebSocket for real-time chat**

4. **Retrieve evaluation data after completion**

## 🔧 **Error Handling**

Handle common errors:
- **WebSocket connection failures**
- **Authentication errors (401/403)**
- **Interview not found (404)**
- **Server errors (500)**

## 📱 **Mobile Considerations**

- Use WebSocket libraries that support mobile
- Handle connection drops gracefully
- Implement reconnection logic
- Consider offline message queuing

## 🎨 **UI/UX Recommendations**

- Show typing indicators
- Display interview progress
- Highlight current stage
- Show evaluation results clearly
- Provide clear error messages
- Implement responsive design
