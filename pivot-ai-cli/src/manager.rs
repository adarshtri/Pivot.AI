use std::process::Stdio;
use tokio::process::Command;

/// Manages the lifecycle of sub-agents and their processes.
pub struct AgentManager {
    agents: Vec<String>,
}

impl AgentManager {
    /// Create a new AgentManager.
    pub fn new() -> Self {
        Self {
            agents: Vec::new(),
        }
    }

    /// Spawn a new sub-agent as a child process.
    pub async fn spawn_agent(&mut self, name: &str) -> Result<(), std::io::Error> {
        println!("🚀 [Manager] Spawning sub-agent: {}...", name);
        
        self.agents.push(name.to_string());

        // For now, we spawn a dummy process (sleep 1) to demonstrate the concept.
        // In the future, this will be 'pivot-ai-cli --mode sub-agent'
        let mut child = Command::new("sleep")
            .arg("1")
            .stdout(Stdio::null())
            .spawn()?;

        // We must own the name to pass it into the async move block
        let name_owned = name.to_string();

        // We can wait for it asynchronously!
        tokio::spawn(async move {
            let status = child.wait().await.expect("failed to wait on child");
            println!("✅ [Manager] Sub-agent '{}' finished with status: {}", name_owned, status);
        });

        Ok(())
    }
}
