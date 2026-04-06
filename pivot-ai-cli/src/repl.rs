use rustyline::DefaultEditor;
use crate::mcp::hub::McpHub;
use crate::agent::ollama::OllamaClient;
use crate::agent::groq::GroqClient;
use crate::agent::config::{ModelConfig, IntegrationType};
use crate::agent::{Agent, Message};
use colored::*;
use std::sync::Arc;
use std::fs;
use chrono::Local;

/// Helper to persist the session history as a Markdown file.
fn persist_session(path: &std::path::Path, history: &[Message]) {
    let mut content = format!("# 🧬 Pivot.AI Session: {}\n\n", Local::now().to_rfc3339());
    for msg in history {
        let role = match msg.role.as_str() {
            "user" => "👤 USER",
            "assistant" => "🤖 AGENT",
            "system" => "⚙️ SYSTEM",
            _ => "📝 LOG",
        };
        content.push_str(&format!("## {}\n{}\n\n", role, msg.content));
    }
    let _ = fs::write(path, content);
}

/// Helper to slice the history for "Context Readiness."
fn get_context_window(history: &[Message], window_size: usize) -> Vec<Message> {
    if history.len() <= window_size + 1 {
        return history.to_vec();
    }
    let mut window = Vec::new();
    window.push(history[0].clone());
    let start_idx = history.len() - window_size;
    window.extend_from_slice(&history[start_idx..]);
    window
}

pub async fn run_repl() -> Result<(), Box<dyn std::error::Error>> {
    println!("{}", "🚀 [Pivot.AI] Entering Agentic Hub Mode (Dynamic SOPs Enabled)".bright_cyan().bold());
    println!("Type your message or use /sop-name to invoke a workflow.");
    
    let model_config = ModelConfig::load();
    let session_id = Local::now().format("%Y-%m-%dT%H-%M-%S").to_string();
    let session_path = ModelConfig::get_session_path(&session_id);

    let agent: Arc<dyn Agent + Send + Sync> = match model_config.integration {
        IntegrationType::Ollama => Arc::new(OllamaClient::new(&model_config.model_name.unwrap_or("qwen2.5:0.5b".to_string()))),
        IntegrationType::Groq => {
            let token = model_config.api_token.ok_or("Groq API token missing")?;
            Arc::new(GroqClient::new(&model_config.model_name.unwrap_or("llama-3.3-70b-versatile".to_string()), &token))
        },
        _ => return Err("Integration not supported".into()),
    };

    let mut mcp_hub = McpHub::new().await?;
    let all_tools = mcp_hub.get_all_tools().await;
    let all_resources = mcp_hub.get_all_resources().await;
    let all_sops = mcp_hub.get_all_prompts().await;
    
    println!("✅ Skill Registry: {} tools | {} resources | {} SOPs", 
        all_tools.len().to_string().yellow(), 
        all_resources.len().to_string().cyan(), 
        all_sops.len().to_string().magenta());

    let mut history: Vec<Message> = Vec::new();
    let context_window_size = 10;

    let system_prompt = format!(
        "You are the Pivot.AI Agent. Access to tools: {}\n\nRESOURCES: {}\n\n\
        INSTRUCTIONS: Handle /sop commands if triggered. Perform tool calls using [tool_name].",
        all_tools.iter().map(|t| t.name.clone()).collect::<Vec<_>>().join(", "),
        all_resources.iter().map(|r| r.uri.clone()).collect::<Vec<_>>().join(", ")
    );

    history.push(Message { role: "system".to_string(), content: system_prompt, tool_calls: None });
    persist_session(&session_path, &history);

    let mut rl = DefaultEditor::new()?;
    loop {
        let readline = rl.readline(&"pivot-ai > ".bright_blue().to_string());
        match readline {
            Ok(line) => {
                let input = line.trim();
                if input.is_empty() { continue; }
                if input == "exit" || input == "quit" { break; }
                
                let _ = rl.add_history_entry(input);

                // --- SOP Slash Command Invocaton ---
                if input.starts_with('/') {
                    let sop_name = &input[1..].split(' ').next().unwrap_or("");
                    if let Some(sop) = all_sops.iter().find(|p| p.name == *sop_name) {
                        println!("🧬 {} '{}'...", "Invoking SOP:".bright_magenta(), sop.name.cyan().bold());
                        
                        // Parse arguments from the command or ask
                        let mut args = serde_json::Map::new();
                        let parts: Vec<&str> = input.split(' ').collect();
                        
                        // Check for provided arguments e.g. /my-sop job_id=123
                        for part in &parts[1..] {
                            if part.contains('=') {
                                let kv: Vec<&str> = part.split('=').collect();
                                if kv.len() == 2 {
                                    args.insert(kv[0].to_string(), serde_json::json!(kv[1]));
                                }
                            }
                        }

                        // Get the prompt content
                        match mcp_hub.get_prompt(&sop.name, Some(serde_json::Value::Object(args))).await {
                            Ok(result) => {
                                for msg in result.messages {
                                    println!("📝 Found SOP Procedure: {}", result.description.as_deref().unwrap_or("Guided Task"));
                                    history.push(Message { role: "system".to_string(), content: format!("SOP INSTRUCTIONS: {}", msg.content.text), tool_calls: None });
                                }
                                println!("{}", "🧠 Agent is processing the SOP blueprint...".dimmed());
                            }
                            Err(e) => println!("❌ Resource Error: {}", e),
                        }
                    } else {
                        println!("⚠️ SOP '{}' not found. Available SOPs: {}", sop_name, all_sops.iter().map(|p| p.name.clone()).collect::<Vec<_>>().join(", "));
                        continue;
                    }
                } else {
                    history.push(Message { role: "user".to_string(), content: input.to_string(), tool_calls: None });
                }

                // AI Loop (SOP or regular chat)
                loop {
                    let current_context = get_context_window(&history, context_window_size);
                    let response = agent.chat(current_context).await?;
                    let ai_content = response.message.content.clone();
                    let ai_lower = ai_content.to_lowercase();
                    
                    let mut tool_called = false;
                    for tool in &all_tools {
                        if ai_lower.contains(&format!("[{}", tool.name.to_lowercase())) {
                            println!("⚙️  {} '{}'...", "Executing tool:".bright_yellow(), tool.name.cyan().bold());
                            match mcp_hub.call_tool(&tool.name, None).await {
                                Ok(res) => {
                                    history.push(Message { role: "assistant".to_string(), content: ai_content.clone(), tool_calls: None });
                                    history.push(Message { role: "system".to_string(), content: format!("Result: {:?}", res), tool_calls: None });
                                    tool_called = true;
                                    break;
                                }
                                Err(e) => println!("❌ Tool Error: {}", e),
                            }
                        }
                    }
                    
                    if !tool_called {
                        println!("\n{} {}", "🤖 Agent:".bright_green().bold(), ai_content);
                        history.push(response.message);
                        persist_session(&session_path, &history);
                        break;
                    }
                }
            }
            Err(_) => break,
        }
    }
    println!("{}", "👋 Goodbye!".bright_yellow());
    Ok(())
}
