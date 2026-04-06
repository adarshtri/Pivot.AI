use crate::mcp::client::McpClient;
use crate::mcp::config::load_config;
use crate::mcp::types::{Tool, Resource, ReadResourceResult, Prompt, GetPromptResult};
use std::collections::HashMap;

/// Central hub managing multiple MCP server connections.
pub struct McpHub {
    clients: HashMap<String, McpClient>,
}

impl McpHub {
    pub async fn new() -> Result<Self, Box<dyn std::error::Error>> {
        let config = load_config()?;
        let mut hub = Self { clients: HashMap::new() };

        for server_config in &config.servers {
            let args: Vec<&str> = server_config.args.iter().map(|s| s.as_str()).collect();
            let mut client = McpClient::spawn(&server_config.command, args)?;
            
            println!("🔌 Connecting to MCP Server: {}...", server_config.name);
            if let Err(e) = client.initialize().await {
                eprintln!("⚠️ Failed to initialize {}: {}", server_config.name, e);
                continue;
            }
            
            hub.clients.insert(server_config.name.clone(), client);
        }

        Ok(hub)
    }

    /// Aggregate all tools from all connected servers.
    pub async fn get_all_tools(&mut self) -> Vec<Tool> {
        let mut all_tools = Vec::new();
        for (name, client) in self.clients.iter_mut() {
            match client.list_tools().await {
                Ok(result) => all_tools.extend(result.tools),
                Err(e) => eprintln!("⚠️  Error listing tools from {}: {}", name, e),
            }
        }
        all_tools
    }

    /// Aggregate all resources from all connected servers.
    pub async fn get_all_resources(&mut self) -> Vec<Resource> {
        let mut all_resources = Vec::new();
        for (name, client) in self.clients.iter_mut() {
            match client.list_resources().await {
                Ok(result) => all_resources.extend(result.resources),
                Err(e) => eprintln!("⚠️  Error listing resources from {}: {}", name, e),
            }
        }
        all_resources
    }

    /// Aggregate all prompts (SOPs) from all connected servers.
    pub async fn get_all_prompts(&mut self) -> Vec<Prompt> {
        let mut all_prompts = Vec::new();
        for (name, client) in self.clients.iter_mut() {
            match client.list_prompts().await {
                Ok(result) => all_prompts.extend(result.prompts),
                Err(e) => eprintln!("⚠️  Error listing SOPs from {}: {}", name, e),
            }
        }
        all_prompts
    }

    /// Route a tool call to the correct server.
    pub async fn call_tool(&mut self, name: &str, params: Option<serde_json::Value>) -> Result<serde_json::Value, Box<dyn std::error::Error>> {
        for client in self.clients.values_mut() {
            let tools = client.list_tools().await?;
            if tools.tools.iter().any(|t| t.name == name) {
                let result = client.call_tool(name, params).await?;
                return Ok(result.unwrap_or(serde_json::json!({ "status": "success", "message": "Tool executed with empty result" })));
            }
        }
        Err(format!("Tool not found: {}", name).into())
    }

    /// Route a resource read to the correct server.
    pub async fn read_resource(&mut self, uri: &str) -> Result<ReadResourceResult, Box<dyn std::error::Error>> {
        for client in self.clients.values_mut() {
            let resources = client.list_resources().await?;
            if resources.resources.iter().any(|r| r.uri == uri) {
                return client.read_resource(uri).await;
            }
        }
        Err(format!("Resource not found: {}", uri).into())
    }

    /// Route an SOP (Prompt) request to the correct server.
    pub async fn get_prompt(&mut self, name: &str, arguments: Option<serde_json::Value>) -> Result<GetPromptResult, Box<dyn std::error::Error>> {
        for client in self.clients.values_mut() {
            let prompts = client.list_prompts().await?;
            if prompts.prompts.iter().any(|p| p.name == name) {
                return client.get_prompt(name, arguments).await;
            }
        }
        Err(format!("SOP (Prompt) not found: {}", name).into())
    }
}
