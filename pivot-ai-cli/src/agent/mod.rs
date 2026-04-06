pub mod ollama;
pub mod groq;
pub mod config;

use serde::{Deserialize, Serialize};
use async_trait::async_trait;

#[derive(Serialize, Deserialize, Debug, Clone)]
pub struct Message {
    pub role: String,
    pub content: String,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub tool_calls: Option<Vec<ToolCall>>,
}

#[derive(Serialize, Deserialize, Debug, Clone)]
pub struct ToolCall {
    pub name: String,
    pub arguments: serde_json::Value,
}

#[derive(Serialize, Deserialize, Debug, Clone)]
pub struct ChatRequest {
    pub model: String,
    pub messages: Vec<Message>,
    pub stream: bool,
}

#[derive(Serialize, Deserialize, Debug, Clone)]
pub struct ChatResponse {
    pub message: Message,
    pub done: bool,
}

/// Common trait for all LLM providers (Ollama, Groq, etc.)
#[async_trait]
pub trait Agent {
    /// Send a chat request to the LLM.
    async fn chat(&self, messages: Vec<Message>) -> Result<ChatResponse, Box<dyn std::error::Error>>;
}
