use serde::{Deserialize, Serialize};
use std::fs;
use std::path::PathBuf;
use home::home_dir;

#[derive(Serialize, Deserialize, Debug, Clone)]
pub struct McpServerConfig {
    pub name: String,
    pub command: String,
    pub args: Vec<String>,
}

#[derive(Serialize, Deserialize, Debug, Clone)]
pub struct McpConfig {
    pub servers: Vec<McpServerConfig>,
}

pub fn get_config_path() -> PathBuf {
    let mut path = home_dir().expect("Could not find home directory");
    path.push(".pivot-ai");
    path.push("mcp.json");
    path
}

pub fn load_config() -> Result<McpConfig, Box<dyn std::error::Error>> {
    let path = get_config_path();
    
    if !path.exists() {
        // Create default config with our own pivot-mcp server
        let default_config = McpConfig {
            servers: vec![McpServerConfig {
                name: "pivot-core".to_string(),
                command: "pivot-mcp".to_string(),
                args: vec![],
            }],
        };
        save_config(&default_config)?;
        return Ok(default_config);
    }

    let content = fs::read_to_string(path)?;
    let config: McpConfig = serde_json::from_str(&content)?;
    Ok(config)
}

pub fn save_config(config: &McpConfig) -> Result<(), Box<dyn std::error::Error>> {
    let path = get_config_path();
    
    // Ensure parent directory exists
    if let Some(parent) = path.parent() {
        fs::create_dir_all(parent)?;
    }

    let content = serde_json::to_string_pretty(config)?;
    fs::write(path, content)?;
    Ok(())
}
