"use client";
import { useState } from "react";

export function Toast({ message, type = "success", onClose }) {
  return (
    <div
      className={`fixed bottom-6 right-6 z-50 px-5 py-3 rounded-xl text-sm font-medium
        border backdrop-blur-xl animate-[toast-in_0.3s_ease]
        ${type === "success" ? "bg-emerald-400/15 text-emerald-400 border-emerald-400/20" : ""}
        ${type === "error" ? "bg-red-400/15 text-red-400 border-red-400/20" : ""}
        ${type === "info" ? "bg-blue-400/15 text-blue-400 border-blue-400/20" : ""}
      `}
    >
      {message}
    </div>
  );
}

export function useToast() {
  const [toast, setToast] = useState(null);

  const showToast = (message, type = "success") => {
    setToast({ message, type });
    setTimeout(() => setToast(null), 3000);
  };

  const ToastComponent = toast ? (
    <Toast message={toast.message} type={toast.type} />
  ) : null;

  return { showToast, ToastComponent };
}

export function TagInput({ tags, onAdd, onRemove, placeholder }) {
  const [value, setValue] = useState("");

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && value.trim()) {
      e.preventDefault();
      onAdd(value.trim());
      setValue("");
    }
  };

  const handleBlur = () => {
    if (value.trim()) {
      onAdd(value.trim());
      setValue("");
    }
  };

  return (
    <div>
      <div className="flex flex-wrap gap-2 mb-2">
        {tags.map((tag) => (
          <span
            key={tag}
            className="tag cursor-pointer hover:bg-red-400/15 hover:text-red-400 hover:border-red-400/30"
            onClick={() => onRemove(tag)}
          >
            {tag}
            <span className="opacity-60 text-xs ml-1">×</span>
          </span>
        ))}
      </div>
      <input
        className="input-dark w-full"
        value={value}
        onChange={(e) => setValue(e.target.value)}
        onKeyDown={handleKeyDown}
        onBlur={handleBlur}
        placeholder={placeholder || "Type and press Enter"}
      />
    </div>
  );
}

export function Spinner() {
  return (
    <div className="w-5 h-5 border-2 border-white/10 border-t-[var(--accent)] rounded-full animate-spin inline-block" />
  );
}

export function EmptyState({ icon, message, action }) {
  return (
    <div className="text-center py-12 text-[#5a5c72]">
      <div className="text-4xl mb-4 opacity-50">{icon}</div>
      <p className="text-sm mb-4">{message}</p>
      {action}
    </div>
  );
}
