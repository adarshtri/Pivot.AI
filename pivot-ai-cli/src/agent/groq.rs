use async_trait::async_trait;
use reqwest::Client;
use serde::{Deserialize, Serialize};
use crate::agent::{Agent, ChatResponse, Message};

/// Client for interacting with the Groq API (OpenAI-compatible).
pub struct GroqClient {
    client: Client,
    model: String,
    api_token: String,
    url: String,
}

#[derive(Serialize, Deserialize, Debug)]
pub struct OpenAIRequest {
    pub model: String,
    pub messages: Vec<Message>,
}

#[derive(Serialize, Deserialize, Debug)]
pub struct OpenAIResponse {
    pub choices: Vec<Choice>,
}

#[derive(Serialize, Deserialize, Debug)]
pub struct Choice {
    pub message: Message,
}

impl GroqClient {
    pub fn new(model: &str, api_token: &str) -> Self {
        Self {
            client: Client::new(),
            model: model.to_string(),
            api_token: api_token.to_string(),
            url: "https://api.groq.com/openai/v1/chat/completions".to_string(),
        }
    }
}

#[async_trait]
impl Agent for GroqClient {
    /// Send a request to the Groq chat API.
    async fn chat(&self, messages: Vec<Message>) -> Result<ChatResponse, Box<dyn std::error::Error>> {
        let request = OpenAIRequest {
            model: self.model.clone(),
            messages,
        };

        let response = self.client.post(&self.url)
            .header("Authorization", format!("Bearer {}", self.api_token))
            .json(&request)
            .send()
            .await?;

        if !response.status().is_success() {
            let error_text = response.text().await?;
            return Err(format!("Groq API error: {}", error_text).into());
        }

        let openai_response: OpenAIResponse = response.json().await?;
        
        let first_choice = openai_response.choices.get(0).ok_or("No choices returned from Groq")?;
        
        Ok(ChatResponse {
            message: first_choice.message.clone(),
            done: true,
        })
    }
}
