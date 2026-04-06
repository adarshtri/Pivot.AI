use serde::{Deserialize, Serialize};
use std::fs;
use std::path::PathBuf;
use home::home_dir;

#[derive(Serialize, Deserialize, Debug, Clone)]
#[serde(rename_all = "lowercase")]
pub enum IntegrationType {
    Ollama,
    Groq,
    OpenAI,
}

#[derive(Serialize, Deserialize, Debug, Clone)]
pub struct ModelConfig {
    pub integration: IntegrationType,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub api_token: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub model_name: Option<String>,
}

impl Default for ModelConfig {
    fn default() -> Self {
        Self {
            integration: IntegrationType::Ollama,
            api_token: None,
            model_name: Some("qwen2.5:0.5b".to_string()),
        }
    }
}

impl ModelConfig {
    /// Loads the configuration from ~/.pivot-ai/model.json
    pub fn load() -> Self {
        let mut config_path = home_dir().unwrap_or_else(|| PathBuf::from("."));
        config_path.push(".pivot-ai");
        config_path.push("model.json");

        if !config_path.exists() {
            return Self::default();
        }

        let content = fs::read_to_string(config_path).unwrap_or_default();
        serde_json::from_str(&content).unwrap_or_else(|_| Self::default())
    }

    /// Returns the path to a session file, ensuring the directory exists.
    pub fn get_session_path(session_id: &str) -> PathBuf {
        let mut config_path = home_dir().unwrap_or_else(|| PathBuf::from("."));
        config_path.push(".pivot-ai");
        config_path.push("sessions");
        
        let _ = fs::create_dir_all(&config_path);
        
        config_path.push(format!("{}.md", session_id));
        config_path
    }

    /// Saves the configuration to ~/.pivot-ai/model.json
    pub fn save(&self) -> Result<(), Box<dyn std::error::Error>> {
        let mut config_path = home_dir().unwrap_or_else(|| PathBuf::from("."));
        config_path.push(".pivot-ai");
        fs::create_dir_all(&config_path)?;
        config_path.push("model.json");

        let content = serde_json::to_string_pretty(self)?;
        fs::write(config_path, content)?;
        Ok(())
    }
}
