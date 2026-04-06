use crate::mcp::types::{ListToolsResult, ListResourcesResult, ReadResourceResult,
    ListPromptsResult, GetPromptResult};
use serde_json::Value;
use std::process::{Child, Command, Stdio};
use std::io::{BufRead, BufReader, Write, Read};
use std::error::Error;

pub struct McpClient {
    #[allow(dead_code)]
    child: Child,
    stdin: Box<dyn Write + Send>,
    reader: BufReader<Box<dyn Read + Send>>,
    id_counter: u64,
}

impl McpClient {
    pub fn spawn(command: &str, args: Vec<&str>) -> Result<Self, Box<dyn Error>> {
        let mut child = Command::new(command)
            .args(args)
            .stdin(Stdio::piped())
            .stdout(Stdio::piped())
            .stderr(Stdio::inherit())
            .spawn()?;

        let stdin = Box::new(child.stdin.take().ok_or("Failed to capture stdin")?);
        let stdout = child.stdout.take().ok_or("Failed to capture stdout")?;
        
        let reader = BufReader::new(Box::new(stdout) as Box<dyn Read + Send>);

        Ok(Self { child, stdin, reader, id_counter: 1 })
    }

    pub async fn initialize(&mut self) -> Result<(), Box<dyn Error>> {
        let req = serde_json::json!({
            "jsonrpc": "2.0",
            "id": self.id_counter,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {
                    "name": "pivot-ai-cli",
                    "version": "0.1.0"
                }
            }
        });
        self.send_request(req).await?;
        self.id_counter += 1;
        Ok(())
    }

    pub async fn list_tools(&mut self) -> Result<ListToolsResult, Box<dyn Error>> {
        let req = serde_json::json!({
            "jsonrpc": "2.0",
            "id": self.id_counter,
            "method": "tools/list",
            "params": {}
        });
        let res = self.send_request(req).await?;
        self.id_counter += 1;
        
        let result: ListToolsResult = serde_json::from_value(res.get("result").cloned().unwrap_or(serde_json::json!({"tools": []})))?;
        Ok(result)
    }

    pub async fn list_resources(&mut self) -> Result<ListResourcesResult, Box<dyn Error>> {
        let req = serde_json::json!({
            "jsonrpc": "2.0",
            "id": self.id_counter,
            "method": "resources/list",
            "params": {}
        });
        let res = self.send_request(req).await?;
        self.id_counter += 1;
        
        let result: ListResourcesResult = serde_json::from_value(res.get("result").cloned().unwrap_or(serde_json::json!({"resources": []})))?;
        Ok(result)
    }

    pub async fn read_resource(&mut self, uri: &str) -> Result<ReadResourceResult, Box<dyn Error>> {
        let req = serde_json::json!({
            "jsonrpc": "2.0",
            "id": self.id_counter,
            "method": "resources/read",
            "params": { "uri": uri }
        });
        let res = self.send_request(req).await?;
        self.id_counter += 1;
        
        let result: ReadResourceResult = serde_json::from_value(res.get("result").cloned().unwrap_or(serde_json::json!({"contents": []})))?;
        Ok(result)
    }

    pub async fn list_prompts(&mut self) -> Result<ListPromptsResult, Box<dyn Error>> {
        let req = serde_json::json!({
            "jsonrpc": "2.0",
            "id": self.id_counter,
            "method": "prompts/list",
            "params": {}
        });
        let res = self.send_request(req).await?;
        self.id_counter += 1;
        
        let result: ListPromptsResult = serde_json::from_value(res.get("result").cloned().unwrap_or(serde_json::json!({"prompts": []})))?;
        Ok(result)
    }

    pub async fn get_prompt(&mut self, name: &str, arguments: Option<Value>) -> Result<GetPromptResult, Box<dyn Error>> {
        let req = serde_json::json!({
            "jsonrpc": "2.0",
            "id": self.id_counter,
            "method": "prompts/get",
            "params": {
                "name": name,
                "arguments": arguments.unwrap_or(serde_json::json!({}))
            }
        });
        let res = self.send_request(req).await?;
        self.id_counter += 1;
        
        let result: GetPromptResult = serde_json::from_value(res.get("result").cloned().unwrap_or(serde_json::json!({"messages": []})))?;
        Ok(result)
    }

    pub async fn call_tool(&mut self, name: &str, arguments: Option<Value>) -> Result<Option<Value>, Box<dyn Error>> {
        let req = serde_json::json!({
            "jsonrpc": "2.0",
            "id": self.id_counter,
            "method": "tools/call",
            "params": {
                "name": name,
                "arguments": arguments.unwrap_or(serde_json::json!({}))
            }
        });
        let res = self.send_request(req).await?;
        self.id_counter += 1;
        Ok(res.get("result").cloned())
    }

    async fn send_request(&mut self, req: Value) -> Result<Value, Box<dyn Error>> {
        let line = serde_json::to_string(&req)? + "\n";
        self.stdin.write_all(line.as_bytes())?;
        self.stdin.flush()?;

        let mut res_line = String::new();
        self.reader.read_line(&mut res_line)?;
        
        if res_line.is_empty() {
             return Err("Server closed the connection".into());
        }

        let res: Value = serde_json::from_str(&res_line)?;
        
        if let Some(error) = res.get("error") {
            return Err(format!("MCP Error: {}", error).into());
        }

        Ok(res)
    }
}
