mod manager;
mod repl;
mod mcp;
mod agent;

use clap::{Parser, Subcommand};
use manager::AgentManager;

#[derive(Parser, Debug)]
#[command(name = "pivot-ai-cli", version, about = "Pivot.AI CLI - Your Personalized Agentic Career Engine", long_about = None)]
struct Cli {
    #[command(subcommand)]
    command: Option<Commands>, // Optional: running without subcommand enters Interactive Mode
}

#[derive(Subcommand, Debug)]
enum Commands {
    /// Start an agentic chat session
    Agent {
        /// The message to send to the agent
        message: String,
    },
    /// Run a specific pipeline task (ingest, score, match)
    Run {
        /// The task to run
        task: String,
    },
    /// Manage configuration and settings
    Config {
        /// The setting to view or modify
        #[command(subcommand)]
        action: ConfigAction,
    },
}

#[derive(Subcommand, Debug)]
enum ConfigAction {
    /// Get a configuration value
    Get { key: String },
    /// Set a configuration value
    Set { key: String, value: String },
    /// List all configuration values
    List,
}

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    let cli = Cli::parse();
    let mut manager = AgentManager::new();

    match &cli.command {
        Some(Commands::Agent { message }) => {
            println!("🤖 Agent: Processing your request: '{}'", message);
            manager.spawn_agent("worker-1").await?;
            tokio::time::sleep(tokio::time::Duration::from_millis(1100)).await;
        }
        Some(Commands::Run { task }) => {
            println!("⚙️ Running pipeline task: {}", task);
        }
        Some(Commands::Config { action }) => {
            match action {
                ConfigAction::Get { key } => println!("🔍 Config [{}]: (value will be here)", key),
                ConfigAction::Set { key, value } => {
                    println!("💾 Config: Setting {} to {}", key, value);
                }
                ConfigAction::List => println!("📋 Listing all configuration items..."),
            }
        }
        None => {
            // No subcommand provided? Start the Interactive Agent REPL!
            repl::run_repl().await?;
        }
    }

    Ok(())
}
