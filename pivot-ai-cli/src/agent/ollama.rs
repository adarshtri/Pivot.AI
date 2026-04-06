use async_trait::async_trait;
use reqwest::Client;
use crate::agent::{Agent, ChatRequest, ChatResponse, Message};

/// Client for interacting with the local Ollama API.
pub struct OllamaClient {
    client: Client,
    model: String,
    url: String,
}

impl OllamaClient {
    pub fn new(model: &str) -> Self {
        Self {
            client: Client::new(),
            model: model.to_string(),
            url: "http://localhost:11434/api/chat".to_string(),
        }
    }
}

#[async_trait]
impl Agent for OllamaClient {
    /// Send a request to the Ollama chat API.
    async fn chat(&self, messages: Vec<Message>) -> Result<ChatResponse, Box<dyn std::error::Error>> {
        let request = ChatRequest {
            model: self.model.clone(),
            messages,
            stream: false,
        };

        let response = self.client.post(&self.url)
            .json(&request)
            .send()
            .await?;

        if !response.status().is_success() {
            let error_text = response.text().await?;
            return Err(format!("Ollama API error: {}", error_text).into());
        }

        let chat_response: ChatResponse = response.json().await?;
        Ok(chat_response)
    }
}
