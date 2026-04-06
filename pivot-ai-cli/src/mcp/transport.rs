use crate::agent::Message;
use crate::mcp::types::{ListToolsResult, ListResourcesResult, ReadResourceResult,
    ListPromptsResult, GetPromptResult};
use std::io::{BufRead, BufReader, Write};
use std::process::{ChildStdin, ChildStdout};

/// Handles low-level reading and writing of JSON-RPC messages over subprocess streams.
pub struct Transport {
    reader: BufReader<ChildStdout>,
    writer: ChildStdin,
}

impl Transport {
    pub fn new(stdout: ChildStdout, stdin: ChildStdin) -> Self {
        Self {
            reader: BufReader::new(stdout),
            writer: stdin,
        }
    }

    /// Read the next message from the subprocess's stdout.
    pub fn read_message(&mut self) -> Result<Option<Message>, Box<dyn std::error::Error>> {
        let mut line = String::new();
        let bytes_read = self.reader.read_line(&mut line)?;
        
        if bytes_read == 0 {
            return Ok(None);
        }

        let message: Message = serde_json::from_str(&line)?;
        Ok(Some(message))
    }

    /// Write a message to the subprocess's stdin.
    pub fn write_message(&mut self, message: &Message) -> Result<(), Box<dyn std::error::Error>> {
        let json = serde_json::to_string(message)?;
        self.writer.write_all(json.as_bytes())?;
        self.writer.write_all(b"\n")?;
        self.writer.flush()?;
        Ok(())
    }
}
